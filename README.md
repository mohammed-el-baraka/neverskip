# NeverSkip

NeverSkip is a minimalist, unskippable task reminder for Linux. It helps you stay productive by popping up a full-screen, Obsidian-inspired task list every time you wake your computer from sleep or unlock your screen.

It also acts as a standard application you can pin to your GNOME dock. Clicking the dock icon will immediately pop up your task list, allowing you to use it as a rapid productivity scratchpad.

## Features
- **Dock Integration**: Pin it to your dock. Click it anytime to instantly pop up the task list.
- **Zero-Friction Trigger**: Automatically triggers on system wake and screen unlock using native `DBus` signals.
- **Obsidian Aesthetic**: A beautiful, dark-mode, full-screen text editor.
- **Unskippable Timer**: A customizable visual countdown timer prevents you from closing the app impulsively.
- **Task Persistence**: Just type in your tasks as bullet points. Everything is auto-saved locally.

## Requirements
- Linux OS (Wayland or X11)
- Python 3
- PyQt6 (`python3-pyqt6` on Ubuntu/Debian)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/neverskip.git
   cd neverskip
   ```

2. **Run the installation script:**
   The `install.sh` script installs dependencies, sets up the `.desktop` file so it appears in your app drawer, and sets up a background systemd user service.
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Pin to Dock!**
   Search for "NeverSkip" in your app menu and pin it to your dock. Click it anytime to view your tasks.

## Usage
- **Lock Screen Behavior**: Whenever the system unlocks, NeverSkip will cover your screen. You cannot close it until the countdown reaches 0.
- **Dock Clicking**: If the daemon is running, clicking the NeverSkip icon in your dock will immediately summon the lock screen.
- **Settings**: Right-click the NeverSkip tray icon and select **Settings** to modify the block duration.

## License
[MIT License](LICENSE)
