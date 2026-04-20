# FNF Listener

**FNF Listener** is a desktop application designed to receive input signals from the [FNF Controller Mobile App](https://github.com/ariwish/fnf-controller) and translate them into keyboard presses. This allows you to play Friday Night Funkin' on your PC using your mobile device as a wireless controller.

## Features

-   **Wireless Low-Latency Input**: Uses UDP for fast communication between your mobile device and PC.
-   **Customizable Keybinds**: Map the mobile buttons to any key on your keyboard.
-   **Dual Backends**:
    -   **evdev**: Linux-native input emulation (excellent for Wayland or games requiring low-level input).
    -   **pynput**: Cross-platform compatibility.
-   **Visual Feedback**: On-screen arrows light up in real-time when inputs are received.
-   **Auto-Discovery**: Displays your local IP address for easy connection setup on the mobile app.
-   **Persistent Settings**: Saves your port and key mapping automatically.

## 🛠️ Installation

### Prerequisites

-   **Python 3.8 or higher**
-   **Linux Users**: If using the `evdev` backend, you may need to add your user to the `input` group or run with appropriate permissions to access `/dev/uinput`.

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

1.  **Run the listener**:
    ```bash
    python fnf_listener.py
    ```
2.  **Configure Binds**: Click the buttons below the arrows to rebind keys. Press the key you wish to assign.
3.  **Start the Service**:
    -   Note the **IP Address** displayed at the top of the window.
    -   Ensure the **Port** matches the one set in your mobile app (default is `8000`).
    -   Click **START**.
4.  **Connect the Mobile App**: Open the [FNF Controller](https://github.com/ariwish/fnf-controller) on your phone, enter the PC's IP and Port, and start playing!

## FNF Controller

This project requires the mobile sender app built with Godot:
**[FNF Controller Repository](https://github.com/ariwish/fnf-controller)**
