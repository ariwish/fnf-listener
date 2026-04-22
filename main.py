import socket
import threading
import tkinter as tk
from tkinter import PhotoImage, messagebox
import platform
import sys
import os
import time
import json
from input import InputEmulator, VALID_KEYS

# Resource path helper for PyInstaller bundles
def resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)

SAVE_FILE = os.path.join(os.path.abspath("."), "bind.json")

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

class AssetLoadError(Exception):
    pass

class FNFListener:
    def __init__(self, root):
        self.root = root
        self.root.title("FNF Listener")
        self.root.geometry("900x500")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.emulator = InputEmulator()
        self.stop_event = threading.Event()
        self.keybinds = ["q", "w", "o", "p"]
        self.port = 8000
        self.directions = ["left", "down", "up", "right"]
        self.n_font = ("Arial", 16, "bold")
        self.l_font = ("Arial", 24, "bold")
        self.listening_idx = None
        self.current_ip = "........"

        self.load_save()
        self.emulator.init_backend()
        self.load_assets()
        self.setup_ui()

        # Start network monitoring thread
        self.net_thread_running = True
        threading.Thread(target=self._network_monitor, daemon=True).start()

    def validate_port(self, port_str):
        """Authoritative port validation."""
        port_str = port_str.strip()
        if port_str.isdigit() and (1 <= int(port_str) <= 65535):
            return int(port_str)
        return None

    def _network_monitor(self):
        """Background thread to poll for IP changes."""
        while self.net_thread_running:
            new_ip = get_local_ip()
            if new_ip != self.current_ip:
                self.current_ip = new_ip
                # Safely update UI from thread
                self.root.after(0, lambda: self.canvas.itemconfig(self.net_label, text=self.current_ip))
            time.sleep(5) # Check every 5 seconds

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
            port_val = self.validate_port(str(data.get("port", "")))
            if port_val is None:
                raise ValueError("Invalid port")
            self.port = port_val

            # Validate backend
            new_backend = data.get("backend", "")
            if platform.system() != "Linux":
                self.emulator.backend = "pynput"
            elif new_backend in ["pynput", "evdev"]:
                self.emulator.backend = new_backend
            else:
                raise ValueError("Invalid backend")

        except Exception:
            # If corrupted or invalid, reset the file with current (default) memory state
            self.save_state()

    def save_state(self):
        try:
            # If UI is ready, use its value; otherwise use memory value
            current_port = self.port
            if hasattr(self, "port_entry") and self.port_entry.winfo_exists():
                val = self.validate_port(self.port_entry.get())
                if val is not None:
                    current_port = val
            
            data = {
                "keybinds": self.keybinds,
                "port": current_port,
                "backend": self.emulator.backend
            }
            with open(SAVE_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def load_assets(self):
        try:
            self.bg_img = PhotoImage(file=resource_path("assets/menu.png"))
            self.arrow_off, self.arrow_on = {}, {}
            for d in self.directions:
                self.arrow_off[d] = PhotoImage(file=resource_path(f"assets/{d}_.png"))
                self.arrow_on[d]  = PhotoImage(file=resource_path(f"assets/{d}.png"))
            self.icon_img = PhotoImage(file=resource_path("assets/up_.png"))
            self.root.iconphoto(False, self.icon_img)
        except Exception as e:
            raise AssetLoadError(str(e))

    def setup_ui(self):
        self.canvas = tk.Canvas(self.root, width=900, height=500, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_img, anchor="nw")

        self.net_label = self.canvas.create_text(450, 60, text=self.current_ip, fill="white", font=self.l_font)

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
        self.port_entry.insert(0, str(self.port))
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
        settings_color = "#139E6E"
        self.settings_frame = tk.Frame(self.modal_overlay, bg=settings_color,
                                       highlightbackground="white", highlightthickness=2)
        tk.Label(self.settings_frame, text="Input Emulator", font=self.n_font,
                 bg=settings_color, fg="white").pack(pady=10, padx=40)
        self.backend_var = tk.StringVar(value=self.emulator.backend)
        backends = [("pynput", "pynput (Cross-platform)")]
        if platform.system() == "Linux":
            backends.append(("evdev", "evdev (Linux Native)"))

        for val, label in backends:
            tk.Radiobutton(self.settings_frame, text=label, variable=self.backend_var, value=val,
                           bg=settings_color, fg="white", selectcolor=settings_color,
                           activebackground=settings_color, activeforeground="white",
                           highlightthickness=0, bd=0).pack(anchor="w", padx=20)
        tk.Button(self.settings_frame, text="Apply", command=self.apply_settings, width=10).pack(pady=20)

    def toggle_settings(self):
        if self.modal_overlay.winfo_viewable():
            self.modal_overlay.place_forget()
        else:
            self.modal_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.settings_frame.place(relx=0.5, rely=0.5, anchor="center")
            self.settings_btn.lift()

    def apply_settings(self):
        new_backend = self.backend_var.get()
        if new_backend != self.emulator.backend:
            if self.emulator.init_backend(new_backend):
                self.save_state()
            else:
                messagebox.showerror("Backend Error", f"Failed to init '{new_backend}'.")
                self.backend_var.set(self.emulator.backend)
                return
        self.modal_overlay.place_forget()

    def start_key_listen(self, idx):
        if self.listening_idx == idx:
            self.cancel_key_listen()
            return
        if self.listening_idx is not None:
            self.cancel_key_listen()
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
        self.cancel_key_listen()
        if not self.stop_event.is_set() and hasattr(self, "running_thread") and self.running_thread.is_alive():
            # Stop the service
            self.stop_event.set()
            self.start_btn.config(text="START", bg="#2ecc71", activebackground="#2ecc71")
            self.port_entry.config(state="normal")
            for btn in self.key_buttons:
                btn.config(state="normal")
            self.settings_btn.config(state="normal")
            self.root.title("FNF Listener")
        else:
            # Start the service
            port = self.validate_port(self.port_entry.get())
            if port is None:
                messagebox.showerror("Invalid Port", "Please enter a valid port number (1-65535)")
                return
            
            self.save_state()
            self.stop_event.clear()
            self.start_btn.config(text="STOP", bg="#e74c3c", activebackground="#e74c3c")
            for btn in self.key_buttons:
                btn.config(state="disabled")
            self.settings_btn.config(state="disabled")
            self.port_entry.config(state="disabled")
            self.root.title(f"Listening on port {port}")
            self.running_thread = threading.Thread(target=self.udp_worker, args=(port,), daemon=True)
            self.running_thread.start()

    def udp_worker(self, port):
        """Runs in a background thread to receive UDP packets."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", port))
                s.setblocking(False)
                prev_state = 0
                while not self.stop_event.is_set():
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
                    self.stop_event.wait(0.001)
        except OSError as e:
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: (
                self.start_btn.config(text="START", bg="#2ecc71", activebackground="#2ecc71"),
                self.port_entry.config(state="normal"),
                messagebox.showerror("Socket Error", f"Could not bind to port {port}:\n{msg}")
            ))

    def handle_input(self, index, is_pressed):
        """
        Processes key events. This runs on the UDP background thread. 
        UI updates must use self.root.after. Key simulation is thread-safe for pynput/evdev.
        """
        keysym = self.keybinds[index]
        direction = self.directions[index]
        img = self.arrow_on[direction] if is_pressed else self.arrow_off[direction]
        
        # Safely update UI
        self.root.after(0, lambda: self.canvas.itemconfig(self.arrow_widgets[direction], image=img))
        
        # Log to window title for simple debugging/feedback
        log_msg = f"{'Pressed' if is_pressed else 'Released'} {keysym.upper()}"
        self.root.after(0, lambda msg=log_msg: self.root.title(f"FNF Listener - {msg}"))

        if is_pressed:
            self.emulator.press(keysym)
        else:
            self.emulator.release(keysym)

    def on_close(self):
        self.stop_event.set()
        self.net_thread_running = False
        self.emulator.close()
        self.root.destroy()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = FNFListener(root)
        root.mainloop()
    except AssetLoadError as e:
        messagebox.showerror("Asset Error", f"Failed to load assets:\n{e}")
    except KeyboardInterrupt:
        pass