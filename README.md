# FNF Listener

**FNF Listener** is a robust desktop application designed to receive input signals from the [FNF Controller Mobile App](https://github.com/ariwish/fnf-controller) and translate them into keyboard presses. This allows you to play Friday Night Funkin' (or any 4-key rhythm game) on your PC using your mobile device as a wireless, low-latency controller.

## ✨ Features

-   **Low-Latency Performance**: Optimized UDP communication with non-blocking socket handling and a high-frequency polling loop (~1ms).
-   **Thread-Safe Architecture**: Clean separation between the networking layer and the Tkinter UI, ensuring stability and responsiveness.
-   **Modular Design**: Input emulation logic is decoupled into a dedicated `input.py` module.
-   **Dual Backends**:
    -   **evdev**: Linux-native input emulation for ultra-low latency (excellent for Wayland or competitive rhythm gaming).
    -   **pynput**: Reliable cross-platform compatibility for Windows, macOS, and Linux.
-   **Visual Feedback**: On-screen arrows light up in real-time as you tap on your mobile device.
-   **Automatic State Persistence**: Your port settings and keybinds are saved automatically to `bind.json`.
-   **Dynamic IP Monitoring**: Displays your local IP address in real-time for easy connection setup.

## 🛠️ Installation

### Prerequisites

-   **Python 3.8 or higher**
-   **Linux Users**: To use the `evdev` backend, your user must have permissions to access `/dev/uinput` (usually by joining the `input` group).

### Steps

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/ariwish/fnf-listener.git
    cd fnf-listener
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 🎮 Usage

1.  **Launch the listener**:
    ```bash
    python main.py
    ```

2.  **Configure Keybinds**:
    - Click any key button (e.g., `Q`, `W`) to enter "listening" mode.
    - Press the physical key on your keyboard you wish to map to that direction.

3.  **Start the Service**:
    -   Ensure the **Port** matches your mobile app configuration (default is `8000`).
    -   Click **START**. The window title will update to show the active listening port.

4.  **Connect Mobile App**:
    - Open the [FNF Controller](https://github.com/ariwish/fnf-controller) on your phone.
    - Enter the **IP Address** displayed at the top of the listener window.
    - Start playing!

## 🔧 Troubleshooting

-   **Socket Error**: Ensure the port is not being used by another application.
-   **Input Not Registering**: On Linux, ensure you have the correct backend selected in settings (⚙️) and that you have permissions for `/dev/uinput`.
-   **Firewall**: Ensure your PC's firewall allows incoming UDP traffic on your chosen port.

## 🤝 Related Projects

-   **[FNF Controller (Mobile App)](https://github.com/ariwish/fnf-controller)**: The Godot-based mobile application that sends the signals.
