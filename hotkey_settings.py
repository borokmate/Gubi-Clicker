import keyboard
import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QPushButton, QDialogButtonBox, QVBoxLayout, QLabel, QHBoxLayout

class HotkeyDialogBox(QDialog):
    shortcut_selected = Signal(str)

    def __init__(self, parent = None, hotkey = None):
        super().__init__(parent)

        with open('settings.json', 'r', encoding="utf-8") as f:
            data = json.load(f)
            self.shortcut = data["shortcut"]
        
        self.setWindowTitle("Hotkey Setting")
        flags = Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint
        flags |= Qt.WindowType.WindowTitleHint

        self.setWindowFlags(flags)

        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        for btn in [ok_button, cancel_button]:
            btn.setFixedSize(75, 35)

        ok_button.clicked.connect(self.accepted_it)
        cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        layout = QVBoxLayout()

        horizontal_layout = QHBoxLayout()
        self.hotkey_record_btn = QPushButton("Start/Stop")
        self.hotkey_record_btn.setFixedHeight(45)
        self.recording = False
        self.hotkey_record_btn.pressed.connect(self.start_or_stop_recording)
        self.hotkey_label = QLabel(hotkey, alignment=Qt.AlignmentFlag.AlignCenter)
        self.hotkey_label.setFixedHeight(45)
        self.hotkey_label.setStyleSheet("""
            QLabel {
                border: 1px solid black;
                font-weight: bold;
                font-size: 14pt;
            }
        """)

        horizontal_layout.addWidget(self.hotkey_record_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        horizontal_layout.addWidget(self.hotkey_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(horizontal_layout)
        layout.addStretch()
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.setFixedSize(250, 110)

    def accepted_it(self): # Weird name ik, but just accepted doesn't work
        self.shortcut_selected.emit(self.shortcut)
        self.accept()

    def start_or_stop_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        if self.recording:
            return

        self.recording = True
        self.pressed_keys = []

        def on_key_event(event):
            if event.event_type == "down" and event.name != 'enter':
                if event.name not in self.pressed_keys:
                    self.pressed_keys.append(event.name)
                shortcut_display = ' + '.join(self.pressed_keys)
                self.hotkey_label.setText(shortcut_display)

        self.key_hook = keyboard.hook(on_key_event)

    def stop_recording(self):
        
        if not self.recording:
            return
        
        keyboard.unhook(self.key_hook)

        self.shortcut = '+'.join(self.pressed_keys)
        self.recording = False