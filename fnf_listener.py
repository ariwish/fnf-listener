import socket
import threading
import tkinter as tk
from tkinter import PhotoImage, messagebox
from PIL import Image, ImageTk
import platform
import sys
import os
import time
import json

# Resource path helper for PyInstaller bundles
def resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)

SAVE_FILE = os.path.join(os.path.abspath("."), "bind.json")

# Valid single-character keysyms and named keys the app supports
VALID_KEYS = set("abcdefghijklmnopqrstuvwxyz0123456789") | {
    "return", "tab", "space", "backspace", "escape",
    "up", "down", "left", "right", "shift", "control", "alt", "super",
    "delete", "home", "end", "prior", "next", "caps_lock", "insert",
    "grave", "comma", "period", "dot", "slash", "semicolon", "apostrophe",
    "bracketleft", "bracketright", "backslash", "minus", "equal",
    "`", ",", ".", "/", ";", "'", "[", "]", "\\", "-", "="
} | {f"f{i}" for i in range(1, 13)}

# Backend state
backend = "pynput" if platform.system() != "Linux" else "evdev"
keyboard = None
ui = None
EVDEV_MAP = {}
PYNPUT_MAP = {}


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"



def init_pynput():
    global keyboard, PYNPUT_MAP
    try:
        from pynput.keyboard import Controller, Key
        keyboard = Controller()
        PYNPUT_MAP = {
            "return": Key.enter, "tab": Key.tab, "space": Key.space,
            "backspace": Key.backspace, "escape": Key.esc,
            "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
            "shift": Key.shift, "control": Key.ctrl, "alt": Key.alt, "super": Key.cmd,
            "delete": Key.delete, "home": Key.home, "end": Key.end,
            "prior": Key.page_up, "next": Key.page_down, "caps_lock": Key.caps_lock, "insert": Key.insert
        }
        symbols = {
            "grave": "`", "comma": ",", "period": ".", "dot": ".", "slash": "/", "semicolon": ";", "apostrophe": "'",
            "bracketleft": "[", "bracketright": "]", "backslash": "\\", "minus": "-", "equal": "="
        }
        for k, v in symbols.items():
            PYNPUT_MAP[k] = v
            PYNPUT_MAP[v] = v
        for i in range(1, 13):
            PYNPUT_MAP[f"f{i}"] = getattr(Key, f"f{i}", None)
        return True
    except ImportError:
        return False


def init_evdev():
    global ui, EVDEV_MAP
    if platform.system() != "Linux":
        return False
    try:
        import evdev
        from evdev import UInput, ecodes as e
        EVDEV_MAP = {c: getattr(e, f"KEY_{c.upper()}") for c in "abcdefghijklmnopqrstuvwxyz0123456789"
                     if hasattr(e, f"KEY_{c.upper()}")}
        EVDEV_MAP.update({
            "return": e.KEY_ENTER, "tab": e.KEY_TAB, "space": e.KEY_SPACE,
            "backspace": e.KEY_BACKSPACE, "escape": e.KEY_ESC,
            "up": e.KEY_UP, "down": e.KEY_DOWN, "left": e.KEY_LEFT, "right": e.KEY_RIGHT,
            "shift": e.KEY_LEFTSHIFT, "control": e.KEY_LEFTCTRL,
            "alt": e.KEY_LEFTALT, "super": e.KEY_LEFTMETA,
            "delete": e.KEY_DELETE, "home": e.KEY_HOME, "end": e.KEY_END,
            "prior": e.KEY_PAGEUP, "next": e.KEY_PAGEDOWN, "caps_lock": e.KEY_CAPSLOCK, "insert": e.KEY_INSERT
        })
        evdev_symbols = {
            "grave": e.KEY_GRAVE, "`": e.KEY_GRAVE,
            "comma": e.KEY_COMMA, ",": e.KEY_COMMA,
            "period": e.KEY_DOT, ".": e.KEY_DOT, "dot": e.KEY_DOT,
            "slash": e.KEY_SLASH, "/": e.KEY_SLASH,
            "semicolon": e.KEY_SEMICOLON, ";": e.KEY_SEMICOLON,
            "apostrophe": e.KEY_APOSTROPHE, "'": e.KEY_APOSTROPHE,
            "bracketleft": e.KEY_LEFTBRACE, "[": e.KEY_LEFTBRACE,
            "bracketright": e.KEY_RIGHTBRACE, "]": e.KEY_RIGHTBRACE,
            "backslash": e.KEY_BACKSLASH, "\\": e.KEY_BACKSLASH,
            "minus": e.KEY_MINUS, "-": e.KEY_MINUS,
            "equal": e.KEY_EQUAL, "=": e.KEY_EQUAL
        }
        for k, code in evdev_symbols.items():
            if code is not None:
                EVDEV_MAP[k] = code
        for i in range(1, 13):
            val = getattr(e, f"KEY_F{i}", None)
            if val is not None:
                EVDEV_MAP[f"f{i}"] = val

        # Filter out any None values and ensure all codes are valid
        valid_codes = [v for v in EVDEV_MAP.values() if v is not None]
        ui = UInput({e.EV_KEY: valid_codes}, name="fnf-udp-vkeyboard")
        return True
    except Exception as err:
        print(f"Evdev init failed: {err}")
        return False


class FNFListener:
    def __init__(self, root):
        self.root = root
        self.root.title("FNF Listener")
        self.root.geometry("900x500")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.running = False
        self.keybinds = ["q", "w", "o", "p"]
        self.port = "8000"
        self.directions = ["left", "down", "up", "right"]
        self.n_font = ("Arial", 16, "bold")
        self.l_font = ("Arial", 24, "bold")
        self.listening_idx = None

        self.load_save()
        self._init_backend()
        self.load_assets()
        self.setup_ui()

        # Fetch SSID in background so it doesn't delay startup
        threading.Thread(target=self._load_network_info, daemon=True).start()

    def _init_backend(self):
        global backend
        if backend == "evdev":
            if not init_evdev():
                init_pynput()
                backend = "pynput"
        else:
            if not init_pynput():
                init_evdev()
                backend = "evdev"

    def _load_network_info(self):
        ip = get_local_ip()
        self.root.after(0, lambda: self.canvas.itemconfig(self.net_label, text=ip))

    def load_save(self):
        if not os.path.exists(SAVE_FILE):
            # Attempt to create default save if it doesn't exist
            self.save_state()
            return

        try:
            with open(SAVE_FILE) as f:
                data = json.load(f)
            
            # Validate keybinds
            keys = data.get("keybinds", [])
            if len(keys) != 4 or not all(k in VALID_KEYS for k in keys):
                raise ValueError("Invalid keybinds")
            self.keybinds = keys

            # Validate port
            port_val = str(data.get("port", ""))
            if not port_val.isdigit() or not (1 <= int(port_val) <= 65535):
                raise ValueError("Invalid port")
            self.port = port_val

            # Validate backend
            new_backend = data.get("backend", "")
            if new_backend not in ["pynput", "evdev"]:
                raise ValueError("Invalid backend")
            global backend
            backend = new_backend

        except Exception:
            # If corrupted or invalid, reset the file with current (default) memory state
            self.save_state()

    def save_state(self):
        try:
            # Handle case where UI might not be fully initialized yet
            port_val = self.port
            if hasattr(self, "port_entry") and self.port_entry.winfo_exists():
                port_val = self.port_entry.get()
            
            data = {
                "keybinds": self.keybinds,
                "port": port_val,
                "backend": backend
            }
            with open(SAVE_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def load_assets(self):
        try:
            bg = Image.open(resource_path("assets/menu.png")).resize((900, 500), Image.Resampling.LANCZOS)
            self.bg_img = ImageTk.PhotoImage(bg)
            self.arrow_off, self.arrow_on = {}, {}
            for d in self.directions:
                off = Image.open(resource_path(f"assets/{d}_.png"))
                on  = Image.open(resource_path(f"assets/{d}.png"))
                size = (int(off.width * 0.8), int(off.height * 0.8))
                self.arrow_off[d] = ImageTk.PhotoImage(off.resize(size, Image.Resampling.LANCZOS))
                self.arrow_on[d]  = ImageTk.PhotoImage(on.resize(size, Image.Resampling.LANCZOS))
            self.icon_img = PhotoImage(file=resource_path("assets/up_.png"))
            self.root.iconphoto(False, self.icon_img)
        except Exception as e:
            messagebox.showerror("Asset Error", f"Failed to load assets:\n{e}")
            self.root.destroy()

    def setup_ui(self):
        self.canvas = tk.Canvas(self.root, width=900, height=500, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_img, anchor="nw")

        self.net_label = self.canvas.create_text(450, 60, text="........", fill="white", font=self.l_font)

        self.arrow_widgets, self.key_buttons = {}, []
        for i, d in enumerate(self.directions):
            x = 185 + i * 180
            self.arrow_widgets[d] = self.canvas.create_image(x, 200, image=self.arrow_off[d])
            btn = tk.Button(self.root, text=self.keybinds[i].upper(), font=self.n_font,
                            width=10, command=lambda idx=i: self.start_key_listen(idx))
            self.canvas.create_window(x, 300, window=btn)
            self.key_buttons.append(btn)

        self.canvas.create_text(280, 420, text="PORT:", fill="white", font=self.n_font)

        vcmd = (self.root.register(lambda s: s.isdigit() or s == ""), "%P")
        self.port_entry = tk.Entry(self.root, width=8, font=self.n_font, justify="center",
                                   validate="key", validatecommand=vcmd)
        self.port_entry.insert(0, self.port)
        self.canvas.create_window(380, 420, window=self.port_entry)

        self.start_btn = tk.Button(self.root, text="START", font=self.n_font,
                                   command=self.toggle_service, width=8, bg="#2ecc71", fg="white",
                                   activebackground="#2ecc71", activeforeground="white")
        self.canvas.create_window(550, 420, window=self.start_btn)

        self.settings_btn = tk.Button(self.root, text="⚙", font=("Arial", 18),
                                      command=self.toggle_settings, bg="#7f8c8d", fg="white",
                                      activebackground="#7f8c8d", activeforeground="white")
        self.canvas.create_window(860, 40, window=self.settings_btn)

        # Focus handling for port entry
        self.port_entry.bind("<Escape>", lambda e: self.root.focus_set())
        self.canvas.bind("<Button-1>", lambda e: self.root.focus_set())

        # Settings modal
        self.modal_overlay = tk.Frame(self.root, bg="#000000")
        self.settings_frame = tk.Frame(self.modal_overlay, bg="#2c3e50",
                                       highlightbackground="white", highlightthickness=2)
        tk.Label(self.settings_frame, text="Input Emulator", font=self.n_font,
                 bg="#2c3e50", fg="white").pack(pady=10, padx=40)
        self.backend_var = tk.StringVar(value=backend)
        for val, label in [("pynput", "pynput (Cross-platform)"), ("evdev", "evdev (Linux Native)")]:
            tk.Radiobutton(self.settings_frame, text=label, variable=self.backend_var, value=val,
                           bg="#2c3e50", fg="white", selectcolor="#34495e").pack(anchor="w", padx=20)
        tk.Button(self.settings_frame, text="Apply", command=self.apply_settings, width=10).pack(pady=20)

    def toggle_settings(self):
        if self.modal_overlay.winfo_viewable():
            self.modal_overlay.place_forget()
        else:
            self.modal_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.settings_frame.place(relx=0.5, rely=0.5, anchor="center")
            self.settings_btn.lift()

    def apply_settings(self):
        global backend
        new_backend = self.backend_var.get()
        if new_backend != backend:
            ok = init_evdev() if new_backend == "evdev" else init_pynput()
            if ok:
                backend = new_backend
            else:
                messagebox.showerror("Backend Error", f"Failed to init '{new_backend}'.")
                self.backend_var.set(backend)
                return
        self.save_state()
        self.modal_overlay.place_forget()

    def start_key_listen(self, idx):
        self.listening_idx = idx
        self.key_buttons[idx].config(text="...")
        self.root.bind("<Key>", self.assign_key)

    def assign_key(self, event):
        if self.listening_idx is None:
            return
        key = event.keysym.lower()
        # Map Tkinter keysyms to our internal VALID_KEYS names
        if key.startswith("shift_"): key = "shift"
        elif key.startswith("control_"): key = "control"
        elif key.startswith("alt_"): key = "alt"
        elif key.startswith("super_") or key == "win_l": key = "super"

        if key in VALID_KEYS:
            self.keybinds[self.listening_idx] = key
            self.save_state()
        # Invalid key silently restores previous bind
        self.cancel_key_listen()

    def cancel_key_listen(self):
        if self.listening_idx is not None:
            self.key_buttons[self.listening_idx].config(text=self.keybinds[self.listening_idx].upper())
            self.listening_idx = None
            self.root.unbind("<Key>")

    def toggle_service(self):
        if not self.running:
            port_str = self.port_entry.get().strip()
            if not port_str or not port_str.isdigit() or not (1 <= int(port_str) <= 65535):
                messagebox.showerror("Invalid Port", "Please enter a valid port number")
                return
            self.save_state()
            self.running = True
            self.start_btn.config(text="STOP", bg="#e74c3c", activebackground="#e74c3c")
            self.settings_btn.config(state="disabled")
            self.port_entry.config(state="disabled")
            self.root.title(f"Listening on port {self.port_entry.get()}")
            threading.Thread(target=self.udp_worker, daemon=True).start()
        else:
            self.running = False
            self.start_btn.config(text="START", bg="#2ecc71", activebackground="#2ecc71")
            self.port_entry.config(state="normal")
            self.settings_btn.config(state="normal")
            self.root.title("FNF Listener")

    def udp_worker(self):
        port = int(self.port_entry.get())
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", port))
                s.setblocking(False)
                prev_state = 0
                while self.running:
                    processed = 0
                    while processed < 50:
                        try:
                            data, _ = s.recvfrom(16)
                            curr = data[0]
                            if curr != prev_state:
                                diff = curr ^ prev_state
                                for i in range(4):
                                    if (diff >> i) & 1:
                                        self.handle_input(i, (curr >> i) & 1)
                                prev_state = curr
                            processed += 1
                        except (BlockingIOError, socket.error):
                            break
                    time.sleep(0.001)
        except OSError as e:
            self.running = False
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: (
                self.start_btn.config(text="START", bg="#2ecc71", activebackground="#2ecc71"),
                messagebox.showerror("Socket Error", f"Could not bind to port {port}:\n{msg}")
            ))

    def handle_input(self, index, is_pressed):
        keysym = self.keybinds[index]
        direction = self.directions[index]
        img = self.arrow_on[direction] if is_pressed else self.arrow_off[direction]
        self.root.after(0, lambda: self.canvas.itemconfig(self.arrow_widgets[direction], image=img))

        if backend == "evdev" and ui:
            import evdev
            code = EVDEV_MAP.get(keysym)
            if code:
                ui.write(evdev.ecodes.EV_KEY, code, 1 if is_pressed else 0)
                ui.syn()
        elif backend == "pynput" and keyboard:
            k = PYNPUT_MAP.get(keysym, keysym)
            try:
                keyboard.press(k) if is_pressed else keyboard.release(k)
            except Exception:
                pass

    def on_close(self):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = FNFListener(root)
        root.mainloop()
    except KeyboardInterrupt:
        pass