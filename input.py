import platform
import importlib

# Valid single-character keysyms and named keys the app supports
VALID_KEYS = set("abcdefghijklmnopqrstuvwxyz0123456789") | {
    "return", "tab", "space", "backspace", "escape",
    "up", "down", "left", "right", "shift", "control", "alt", "super",
    "caps", "grave", "comma", "dot", "slash", "semicolon", "apostrophe",
    "bracketleft", "bracketright", "backslash", "minus", "equal"
}


class InputEmulator:
    def __init__(self):
        self.backend = "pynput" if platform.system() != "Linux" else "evdev"
        self.keyboard = None  # For pynput
        self.ui = None        # For evdev
        self.evdev = None     # Cached evdev module
        self.evdev_map = {}
        self.pynput_map = {}

    def init_backend(self, preferred_backend=None):
        """Initialize the input backend with a priority list."""
        if preferred_backend:
            self.backend = preferred_backend

        # Enforce pynput on non-Linux
        if platform.system() != "Linux":
            self.backend = "pynput"

        # Initialization sequence
        success = False
        if self.backend == "evdev":
            success = self._init_evdev()
            if not success:
                print("Falling back to pynput...")
                self.backend = "pynput"
                success = self._init_pynput()
        else:
            success = self._init_pynput()
            if not success and platform.system() == "Linux":
                print("Falling back to evdev...")
                self.backend = "evdev"
                success = self._init_evdev()

        if not success:
            print(f"Critical Error: Failed to initialize any backend.")
        return success

    def _init_pynput(self):
        try:
            from pynput.keyboard import Controller, Key
            self.keyboard = Controller()
            self.pynput_map = {
                "return": Key.enter, "tab": Key.tab, "space": Key.space,
                "backspace": Key.backspace, "escape": Key.esc,
                "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
                "shift": Key.shift, "control": Key.ctrl, "alt": Key.alt, "super": Key.cmd,
                "caps": Key.caps_lock
            }
            symbols = {
                "grave": "`", "comma": ",", "dot": ".", "slash": "/", "semicolon": ";", "apostrophe": "'",
                "bracketleft": "[", "bracketright": "]", "backslash": "\\", "minus": "-", "equal": "="
            }
            for k, v in symbols.items():
                self.pynput_map[k] = v
            return True
        except ImportError:
            return False

    def _init_evdev(self):
        if platform.system() != "Linux":
            return False
        try:
            if not self.evdev:
                self.evdev = importlib.import_module("evdev")
            
            UInput = self.evdev.UInput
            e = self.evdev.ecodes
            
            # Alphanumeric
            self.evdev_map = {c: getattr(e, f"KEY_{c.upper()}") for c in "abcdefghijklmnopqrstuvwxyz0123456789"}
            
            # UI controls and basic keys
            self.evdev_map.update({
                "return": e.KEY_ENTER, "tab": e.KEY_TAB, "space": e.KEY_SPACE,
                "backspace": e.KEY_BACKSPACE, "escape": e.KEY_ESC,
                "up": e.KEY_UP, "down": e.KEY_DOWN, "left": e.KEY_LEFT, "right": e.KEY_RIGHT,
                "shift": e.KEY_LEFTSHIFT, "control": e.KEY_LEFTCTRL,
                "alt": e.KEY_LEFTALT, "super": e.KEY_LEFTMETA, "caps": e.KEY_CAPSLOCK
            })
            
            # Symbols
            self.evdev_map.update({
                "grave": e.KEY_GRAVE, "comma": e.KEY_COMMA, "dot": e.KEY_DOT,
                "slash": e.KEY_SLASH, "semicolon": e.KEY_SEMICOLON, "apostrophe": e.KEY_APOSTROPHE,
                "bracketleft": e.KEY_LEFTBRACE, "bracketright": e.KEY_RIGHTBRACE,
                "backslash": e.KEY_BACKSLASH, "minus": e.KEY_MINUS, "equal": e.KEY_EQUAL
            })

            valid_codes = [v for v in self.evdev_map.values() if v is not None]
            if self.ui:
                self.ui.close()
            self.ui = UInput({e.EV_KEY: valid_codes}, name="fnf-udp-vkeyboard")
            return True
        except Exception as err:
            print(f"Evdev init failed: {err}")
            return False

    def press(self, keysym):
        if self.backend == "evdev" and self.ui:
            code = self.evdev_map.get(keysym)
            if code:
                self.ui.write(self.evdev.ecodes.EV_KEY, code, 1)
                self.ui.syn()
        elif self.backend == "pynput" and self.keyboard:
            k = self.pynput_map.get(keysym, keysym)
            try:
                self.keyboard.press(k)
            except Exception:
                pass

    def release(self, keysym):
        if self.backend == "evdev" and self.ui:
            code = self.evdev_map.get(keysym)
            if code:
                self.ui.write(self.evdev.ecodes.EV_KEY, code, 0)
                self.ui.syn()
        elif self.backend == "pynput" and self.keyboard:
            k = self.pynput_map.get(keysym, keysym)
            try:
                self.keyboard.release(k)
            except Exception:
                pass

    def close(self):
        if self.ui:
            self.ui.close()
            self.ui = None
