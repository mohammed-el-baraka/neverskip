import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, 
                             QSystemTrayIcon, QMenu, QDialog, QSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QObject
from PyQt6.QtGui import QFont, QIcon, QAction
from PyQt6.QtDBus import QDBusConnection, QDBusMessage
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

CONFIG_DIR = Path.home() / ".config" / "neverskip"
CONFIG_FILE = CONFIG_DIR / "config.json"
SOCKET_NAME = "neverskip_single_instance_socket"

DEFAULT_CONFIG = {
    "duration": 10,
    "opacity": 0.95,
    "main_task": "Review pending pull requests",
    "tasks": "## Other Focus\n\n- Hydrate\n- Focus work block"
}

def load_config():
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return DEFAULT_CONFIG.copy()

def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("NeverSkip Settings")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Block Duration (seconds):"))
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1, 300)
        self.duration_spinbox.setValue(self.config.get("duration", 10))
        h_layout.addWidget(self.duration_spinbox)
        
        h_layout.addWidget(QLabel("Opacity (%):"))
        self.opacity_spinbox = QSpinBox()
        self.opacity_spinbox.setRange(10, 100)
        self.opacity_spinbox.setValue(int(self.config.get("opacity", 0.95) * 100))
        h_layout.addWidget(self.opacity_spinbox)
        layout.addLayout(h_layout)

        layout.addWidget(QLabel("Most Important Task:"))
        self.main_task_edit = QLineEdit()
        self.main_task_edit.setText(self.config.get("main_task", ""))
        self.main_task_edit.setFont(QFont("Inter", 12))
        layout.addWidget(self.main_task_edit)
        
        layout.addWidget(QLabel("Other Tasks:"))
        self.tasks_edit = QTextEdit()
        self.tasks_edit.setAcceptRichText(False)
        self.tasks_edit.setPlainText(self.config.get("tasks", ""))
        self.tasks_edit.setFont(QFont("Inter", 11))
        layout.addWidget(self.tasks_edit)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
    def save_settings(self):
        self.config["duration"] = self.duration_spinbox.value()
        self.config["opacity"] = self.opacity_spinbox.value() / 100.0
        self.config["main_task"] = self.main_task_edit.text()
        self.config["tasks"] = self.tasks_edit.toPlainText()
        save_config(self.config)
        self.accept()

class LockScreen(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.update_stylesheet()
        
        central_widget = QWidget()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(100, 80, 100, 80)
        
        header_label = QLabel("NeverSkip")
        header_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #777777;")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)
        
        main_layout.addStretch()

        self.main_task_label = QLabel()
        self.main_task_label.setObjectName("mainTask")
        self.main_task_label.setFont(QFont("Inter", 36))
        self.main_task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_task_label.setWordWrap(True)
        main_layout.addWidget(self.main_task_label)
        
        main_layout.addSpacing(40)
        
        self.tasks_label = QLabel()
        self.tasks_label.setObjectName("otherTasks")
        self.tasks_label.setFont(QFont("Inter", 20))
        self.tasks_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tasks_label.setWordWrap(True)
        main_layout.addWidget(self.tasks_label)

        main_layout.addStretch()
        
        bottom_layout = QHBoxLayout()
        self.timer_label = QLabel("Waiting...")
        self.timer_label.setFont(QFont("Inter", 18))
        bottom_layout.addWidget(self.timer_label)
        bottom_layout.addStretch()
        
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setDisabled(True)
        self.continue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.continue_btn.clicked.connect(self.close_screen)
        bottom_layout.addWidget(self.continue_btn)
        
        main_layout.addLayout(bottom_layout)
        
        self.remaining_time = self.config.get("duration", 10)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
    def update_stylesheet(self):
        opacity = self.config.get("opacity", 0.95)
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: rgba(30, 30, 30, {opacity}); }}
            QLabel {{ color: #e0e0e0; }}
            QLabel#mainTask {{
                color: #a371f7; font-weight: bold; font-family: 'Segoe UI', 'Inter', sans-serif;
            }}
            QLabel#otherTasks {{
                color: #d4d4d4; font-family: 'Segoe UI', 'Inter', monospace;
            }}
            QPushButton {{
                background-color: #0e639c; color: white;
                border: none; padding: 15px 40px;
                font-size: 20px; font-weight: bold; border-radius: 8px;
            }}
            QPushButton:disabled {{ background-color: #333333; color: #888888; }}
            QPushButton:hover:!disabled {{ background-color: #1177bb; }}
        """)
        
    def start_lock(self):
        self.config = load_config()
        self.update_stylesheet()
        self.remaining_time = self.config.get("duration", 10)
        
        self.main_task_label.setText(self.config.get("main_task", ""))
        self.tasks_label.setText(self.config.get("tasks", ""))
            
        self.continue_btn.setDisabled(True)
        self.update_timer_label()
        
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        
        self.timer.start(1000)

    def update_timer(self):
        self.remaining_time -= 1
        self.update_timer_label()
        if self.remaining_time <= 0:
            self.timer.stop()
            self.timer_label.setText("You may now proceed.")
            self.continue_btn.setDisabled(False)
            self.continue_btn.setFocus()

    def update_timer_label(self):
        if self.remaining_time > 0:
            self.timer_label.setText(f"Screen unlock in {self.remaining_time}s...")

    def close_screen(self):
        self.hide()


class NeverSkipLogic(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.app.setQuitOnLastWindowClosed(False)
        self.config = load_config()
        self.lock_screen = LockScreen(self.config)
        
        self.setup_tray()
        self.setup_dbus()
        self.setup_local_server()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self.app)
        # We rely on the neverskip icon theme installed in user data
        icon = QIcon.fromTheme("neverskip", QIcon.fromTheme("emblem-synchronizing"))
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("NeverSkip")
        
        tray_menu = QMenu()
        show_action = QAction("Lock Screen", self.app)
        show_action.triggered.connect(self.lock_screen.start_lock)
        tray_menu.addAction(show_action)
        
        settings_action = QAction("Settings", self.app)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        
        tray_menu.addSeparator()
        quit_action = QAction("Quit NeverSkip", self.app)
        quit_action.triggered.connect(self.app.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def show_settings(self):
        dialog = SettingsDialog(self.config)
        if dialog.exec():
            self.config = load_config()

    def setup_dbus(self):
        bus = QDBusConnection.sessionBus()
        sys_bus = QDBusConnection.systemBus()
        
        bus.connect("org.freedesktop.ScreenSaver", "/org/freedesktop/ScreenSaver", 
                    "org.freedesktop.ScreenSaver", "ActiveChanged", self.on_screensaver_changed)
        bus.connect("org.gnome.ScreenSaver", "/org/gnome/ScreenSaver", 
                    "org.gnome.ScreenSaver", "ActiveChanged", self.on_screensaver_changed)
        sys_bus.connect("org.freedesktop.login1", "/org/freedesktop/login1", 
                        "org.freedesktop.login1.Manager", "PrepareForSleep", self.on_prepare_for_sleep)

    @pyqtSlot(QDBusMessage)
    def on_screensaver_changed(self, message: QDBusMessage):
        args = message.arguments()
        if args and isinstance(args[0], bool) and not args[0]:
            self.lock_screen.start_lock()

    @pyqtSlot(QDBusMessage)
    def on_prepare_for_sleep(self, message: QDBusMessage):
        args = message.arguments()
        if args and isinstance(args[0], bool) and not args[0]:
            QTimer.singleShot(2000, self.lock_screen.start_lock)

    def setup_local_server(self):
        QLocalServer.removeServer(SOCKET_NAME)
        self.server = QLocalServer()
        self.server.listen(SOCKET_NAME)
        self.server.newConnection.connect(self.handle_new_connection)
        
    def handle_new_connection(self):
        socket = self.server.nextPendingConnection()
        socket.readyRead.connect(lambda: self.read_socket(socket))
        
    def read_socket(self, socket):
        data = socket.readAll().data().decode('utf-8')
        if data == "TRIGGER":
            self.lock_screen.start_lock()
        socket.disconnectFromServer()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NeverSkip")
    
    # Check if another instance is already running
    socket = QLocalSocket()
    socket.connectToServer(SOCKET_NAME)
    if socket.waitForConnected(500):
        # Already running. Send trigger message and exit immediately.
        # This makes the app "pop up" if clicked from the dock.
        socket.write(b"TRIGGER")
        socket.flush()
        socket.waitForBytesWritten(500)
        socket.disconnectFromServer()
        sys.exit(0)
        
    # Not running, start daemon logic
    logic = NeverSkipLogic(app)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
