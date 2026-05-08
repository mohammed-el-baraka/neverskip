#!/bin/bash
set -e

echo "Starting NeverSkip installation..."

# 1. Install dependencies
if command -v apt &> /dev/null; then
    sudo apt update && sudo apt install -y python3-pyqt6
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3-qt6
elif command -v pacman &> /dev/null; then
    sudo pacman -Sy --noconfirm python-pyqt6
fi

# 2. Setup directories & files
APP_DIR="$HOME/.local/share/neverskip"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
APP_DESKTOP="$HOME/.local/share/applications/neverskip.desktop"
SYSTEMD_DIR="$HOME/.config/systemd/user"

mkdir -p "$APP_DIR" "$ICON_DIR" "$SYSTEMD_DIR"

cp main.py "$APP_DIR/"
cp logo.svg "$ICON_DIR/neverskip.svg"
cp neverskip.service "$SYSTEMD_DIR/"

# 3. Create Desktop Entry (The App Button)
cat <<EOF > "$APP_DESKTOP"
[Desktop Entry]
Name=NeverSkip
Comment=Unskippable task reminder
Exec=/usr/bin/python3 $APP_DIR/main.py
Icon=neverskip
Terminal=false
Type=Application
Categories=Utility;Productivity;
StartupNotify=true
EOF

# Update desktop database so the icon appears immediately
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

# 4. Systemd setup
systemctl --user daemon-reload
systemctl --user enable --now neverskip.service

echo "Installation complete!"
echo "NeverSkip is now running in the background and is available in your app drawer/dock."
echo "You can pin it to your dock, and clicking the app icon will immediately show the lock screen!"
