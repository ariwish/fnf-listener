# ![logo](https://github.com/user-attachments/assets/d51f9dd0-ac25-449e-9be4-9d82f5ed959c) FNF Listener

A Python-based desktop app that receives real-time UDP packets from the [FNF Controller](https://github.com/ariwish/fnf-controller) and translates them into keypresses on your PC.

---

## Requirements

- [Python 3.8+](https://www.python.org/downloads/)
- **Linux Users:** If using the `evdev` backend (Settings ⚙️), ensure your user has access to `/dev/uinput`.

---

## Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/ariwish/fnf-listener.git
   cd fnf-listener
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the fnf listener:**
   ```bash
   python main.py
   ```

---

## Usage

1. Open the fnf listener app
2. Put the same port at [FNF Controller](https://github.com/ariwish/fnf-controller)
3. Note the **IP Address** is shown at the top of the window.
4. Open the [FNF Controller](https://github.com/ariwish/fnf-controller) on your phone and enter that IP.
5. Tap the arrows on your phone — they will register as keypresses on your PC.
6. Click **START** in the listener app.
---

## Firewall

If packets aren't arriving, allow UDP port 8000 through your firewall.

**Linux**
```bash
sudo ufw allow 8000/udp
```

**macOS**
System Settings → Network → Firewall → Options → allow Python incoming connections.

**Windows** (run PowerShell as Administrator)
```powershell
netsh advfirewall firewall add rule name="FNF Listener" protocol=UDP dir=in localport=8000 action=allow
```
