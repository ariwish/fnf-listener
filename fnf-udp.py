import socket
import threading
import tkinter as tk
from tkinter import PhotoImage, messagebox
from PIL import Image, ImageTk
import platform

# --- Backend Logic (Unchanged) ---
backend = "pynput" if platform.system() != "Linux" else "evdev"
keyboard = None
ui = None
EVDEV_MAP = {}
PYNPUT_MAP = {}

def init_pynput():
    global keyboard, PYNPUT_MAP
    try:
        from pynput.keyboard import Controller, Key
        keyboard = Controller()
        PYNPUT_MAP.update({
            "return": Key.enter, "tab": Key.tab, "space": Key.space,
            "backspace": Key.backspace, "escape": Key.esc, "up": Key.up,
            "down": Key.down, "left": Key.left, "right": Key.right,
            "shift": Key.shift, "control": Key.ctrl, "alt": Key.alt, "super": Key.cmd
        })
        return True
    except ImportError: return False

def init_evdev():
    global ui, EVDEV_MAP
    try:
        import evdev
        from evdev import UInput, ecodes as e
        ui = UInput()
        EVDEV_MAP = {
            "return": e.KEY_ENTER, "tab": e.KEY_TAB, "space": e.KEY_SPACE,
            "backspace": e.KEY_BACKSPACE, "escape": e.KEY_ESC,
            "up": e.KEY_UP, "down": e.KEY_DOWN, "left": e.KEY_LEFT, "right": e.KEY_RIGHT,
            "shift": e.KEY_LEFTSHIFT, "control": e.KEY_LEFTCTRL, "alt": e.KEY_LEFTALT,
            "super": e.KEY_LEFTMETA, "comma": e.KEY_COMMA, "period": e.KEY_DOT,
            "slash": e.KEY_SLASH, "backslash": e.KEY_BACKSLASH, "bracketleft": e.KEY_LEFTBRACE,
            "bracketright": e.KEY_RIGHTBRACE, "minus": e.KEY_MINUS, "equal": e.KEY_EQUAL, "grave": e.KEY_GRAVE
        }
        return True
    except: return False

if backend == "evdev": 
    if not init_evdev(): init_pynput(); backend = "pynput"
else:
    if not init_pynput(): init_evdev(); backend = "evdev"

class FNFUDPListener:
    def __init__(self, root):
        self.root = root
        self.root.title("FNF UDP Listener")
        self.root.geometry("900x500")
        self.root.resizable(False, False)

        self.running = False
        self.keybinds = ["q", "w", "o", "p"]
        self.listening_idx = None
        self.directions = ["left", "down", "up", "right"]
        self.n_font = ("Arial", 16, "bold")
        self.l_font = ("Arial", 28, "bold")
        
        self.load_assets()
        self.setup_ui()

    def load_assets(self):
        try:
            bg_raw = Image.open("assets/menu.png").resize((900, 500), Image.Resampling.LANCZOS)
            self.bg_img = ImageTk.PhotoImage(bg_raw)
            self.arrow_off, self.arrow_on = {}, {}
            for d in self.directions:
                img_off = Image.open(f"assets/{d}_.png")
                img_on = Image.open(f"assets/{d}.png")
                new_size = (int(img_off.width * 0.8), int(img_off.height * 0.8))
                self.arrow_off[d] = ImageTk.PhotoImage(img_off.resize(new_size, Image.Resampling.LANCZOS))
                self.arrow_on[d] = ImageTk.PhotoImage(img_on.resize(new_size, Image.Resampling.LANCZOS))
            self.icon_img = PhotoImage(file="assets/up_.png")
            self.root.iconphoto(False, self.icon_img)
        except Exception as err:
            print(f"Asset Error: {err}"); self.root.destroy()

    def setup_ui(self):
        self.canvas = tk.Canvas(self.root, width=900, height=500, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_img, anchor="nw")

        try: ip = socket.gethostbyname(socket.gethostname())
        except: ip = "127.0.0.1"
        self.canvas.create_text(450, 60, text=f"IP: {ip}", fill="white", font=self.l_font)

        self.arrow_widgets = {}
        self.key_buttons = []
        for i, direction in enumerate(self.directions):
            x = 150 + (i * 200)
            self.arrow_widgets[direction] = self.canvas.create_image(x, 200, image=self.arrow_off[direction])
            btn = tk.Button(self.root, text=self.keybinds[i].upper(), font=self.n_font, width=10,
                            command=lambda idx=i: self.start_key_listen(idx))
            self.canvas.create_window(x, 300, window=btn)
            self.key_buttons.append(btn)

        self.canvas.create_text(280, 420, text="PORT:", fill="white", font=self.n_font)
        vcmd = (self.root.register(self.validate_port), '%P')
        self.port_entry = tk.Entry(self.root, width=8, font=self.n_font, justify="center", validate="key", validatecommand=vcmd)
        self.port_entry.insert(0, "8000")
        self.canvas.create_window(380, 420, window=self.port_entry)

        # Updated START/STOP color to white text
        self.start_btn = tk.Button(self.root, text="START", font=self.n_font, command=self.toggle_service, width=8, bg="#2ecc71", fg="white")
        self.canvas.create_window(550, 420, window=self.start_btn)

        self.settings_btn = tk.Button(self.root, text="⚙", font=("Arial", 18), command=self.toggle_settings, bg="#7f8c8d", fg="white")
        self.canvas.create_window(860, 40, window=self.settings_btn)
        
        # Modal Overlay (Darkens background and blocks clicks)
        self.modal_overlay = tk.Frame(self.root, bg="#000000")
        self.modal_overlay.place_forget() # Hidden by default
        
        # Settings Container
        self.settings_frame = tk.Frame(self.modal_overlay, bg="#2c3e50", highlightbackground="white", highlightthickness=2)
        tk.Label(self.settings_frame, text="Backend Settings", font=self.n_font, bg="#2c3e50", fg="white").pack(pady=10, padx=40)
        self.backend_var = tk.StringVar(value=backend)
        tk.Radiobutton(self.settings_frame, text="evdev (Linux Native)", variable=self.backend_var, value="evdev", bg="#2c3e50", fg="white", selectcolor="#34495e").pack(anchor="w", padx=20)
        tk.Radiobutton(self.settings_frame, text="pynput (Cross-platform)", variable=self.backend_var, value="pynput", bg="#2c3e50", fg="white", selectcolor="#34495e").pack(anchor="w", padx=20)
        tk.Button(self.settings_frame, text="Apply", command=self.apply_settings, width=10).pack(pady=20)
        
        self.root.bind("<Button-1>", self.check_focus)

    def validate_port(self, P):
        if P == "": return True
        return P.isdigit() and 0 <= int(P) <= 65535

    def toggle_settings(self):
        # If already visible, hide it. Otherwise, show it.
        if self.modal_overlay.winfo_viewable():
            self.modal_overlay.place_forget()
        else:
            # Place overlay across entire window and center the frame inside it
            self.modal_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.settings_frame.place(relx=0.5, rely=0.5, anchor="center")
            self.modal_overlay.lift()
            self.settings_btn.lift() # Keep settings button clickable to toggle back

    def apply_settings(self):
        global backend
        new_backend = self.backend_var.get()
        
        # Check if the backend is actually different
        if new_backend == backend:
            self.modal_overlay.place_forget()
            return

        # Only reconfigure if a change was made
        success = init_evdev() if new_backend == "evdev" else init_pynput()
        if success:
            backend = new_backend
            self.modal_overlay.place_forget()
        else:
            # Revert the radio button selection to the actual working backend on failure
            self.backend_var.set(backend)
            messagebox.showerror("Error", f"Failed to switch to {new_backend}. Reverting to {backend}.")

    def start_key_listen(self, idx):
        self.cancel_key_listen()
        self.listening_idx = idx
        self.key_buttons[idx].config(text="...")
        self.root.bind("<Key>", self.assign_key)

    def assign_key(self, event):
        if self.listening_idx is not None:
            key_name = event.keysym.lower()
            for mod in ["shift", "alt", "control", "super"]:
                if key_name.startswith(mod):
                    key_name = mod
                    break
            self.keybinds[self.listening_idx] = key_name
            self.cancel_key_listen()

    def cancel_key_listen(self):
        if self.listening_idx is not None:
            display = self.keybinds[self.listening_idx].replace('return', 'enter').upper()
            self.key_buttons[self.listening_idx].config(text=display)
            self.listening_idx = None
            self.root.unbind("<Key>")

    def check_focus(self, event):
        if not isinstance(event.widget, tk.Button): self.cancel_key_listen()

    def toggle_service(self):
        if not self.running:
            self.running = True
            self.port_entry.config(state="disabled")
            self.settings_btn.config(state="disabled")
            self.start_btn.config(text="STOP", bg="#e74c3c", fg="white")
            threading.Thread(target=self.udp_worker, daemon=True).start()
        else:
            self.running = False
            self.port_entry.config(state="normal")
            self.settings_btn.config(state="normal")
            self.start_btn.config(text="START", bg="#2ecc71", fg="white")

    def udp_worker(self):
        port_str = self.port_entry.get()
        port = int(port_str) if port_str else 8000
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(('0.0.0.0', port))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Socket Error", str(e)))
                self.root.after(0, self.toggle_service)
                return

            s.settimeout(1.0)
            prev_state = 0
            while self.running:
                try:
                    data, _ = s.recvfrom(16)
                    curr_state = data[0]
                    if curr_state != prev_state:
                        for i in range(4):
                            if ((prev_state >> i) & 1) != ((curr_state >> i) & 1):
                                self.handle_input(i, (curr_state >> i) & 1)
                        prev_state = curr_state
                except socket.timeout:
                    if prev_state != 0:
                        for i in range(4): self.handle_input(i, 0)
                        prev_state = 0

    def handle_input(self, index, is_pressed):
        keysym = self.keybinds[index]
        direction = self.directions[index]
        img = self.arrow_on[direction] if is_pressed else self.arrow_off[direction]
        self.root.after(0, lambda: self.canvas.itemconfig(self.arrow_widgets[direction], image=img))
        
        if backend == "pynput" and keyboard:
            k = PYNPUT_MAP.get(keysym, keysym)
            try:
                if is_pressed: keyboard.press(k)
                else: keyboard.release(k)
            except: pass
        
        elif backend == "evdev" and ui:
            import evdev
            code = EVDEV_MAP.get(keysym)
            if code:
                ui.write(evdev.ecodes.EV_KEY, code, 1 if is_pressed else 0)
                ui.syn()

if __name__ == "__main__":
    root = tk.Tk()
    app = FNFUDPListener(root)
    root.mainloop()