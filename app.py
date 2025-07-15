import sys
import time
import threading
import keyboard
import json
import os
import shutil

from pynput.mouse import Controller, Button, Listener
from hotkey_settings import HotkeyDialogBox
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, 
    QLabel, 
    QMainWindow, 
    QPushButton, 
    QVBoxLayout, 
    QHBoxLayout, 
    QWidget, 
    QGridLayout, 
    QComboBox, 
    QSpinBox,
    QSizePolicy, 
    QGroupBox, 
    QButtonGroup, 
    QRadioButton) # Yeah I love Python cuz I can import 50GBs of things lol

# This is for the installer, so that the settings.json is in C:\Users\{your_user}\AppData\Local\GubiClicker
def get_user_settings_path():
    appdata_dir = os.path.join(os.environ['LOCALAPPDATA'], 'GubiClicker')
    os.makedirs(appdata_dir, exist_ok=True)
    return os.path.join(appdata_dir, 'settings.json')

# Yeah I could have used the Shortcut thingy that Pyside adds but this works better in my opinion cuz it's global innit
class ShortcutHandler(QObject):
    triggered = Signal()

    def __init__(self):
        super().__init__()
        self.current_hotkey = None
        self.hotkey_ref = None
        self.set_hotkey('ctrl+a')

    def set_hotkey(self, hotkey_sequence):

        if self.hotkey_ref is not None: # We can't rebind hotkeys so you have to remove the original
            keyboard.remove_hotkey(self.hotkey_ref)

        self.hotkey_ref = keyboard.add_hotkey(hotkey_sequence, self.on_shortcut)
        self.current_hotkey = hotkey_sequence
    
    def on_shortcut(self):
        self.triggered.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gubi Clicker")
        self.setWindowIcon(QIcon("gubi_mans_icon.ico"))

        self.settings_path = get_user_settings_path()

        if not os.path.exists(self.settings_path):
            shutil.copyfile('settings.json', self.settings_path)

        with open(self.settings_path, 'r', encoding="utf-8") as f:
            data = json.load(f)
            self.shortcut = data["shortcut"]
            self.hour = data["hour"]
            self.minute = data["min"]
            self.second = data["sec"]
            self.milsecond = data["milsec"]
            self.current_click : int = data["mouse_btn"]
            self.click_type : int = data["click_type"]
            self.repeat : bool = data["repeat"]
            self.amount : int = data["amount"]
            self.is_current_location : bool = data["set_pos"]
            self.x : int = data['x']
            self.y : int = data['y']
            
        self.interval : float = 0
        self.running = False

        self.index_to_mouse_button = {
            0 : Button.left,
            1 : Button.right,
            2 : Button.middle
        }
        self.mouse = Controller()
        
        layout = QVBoxLayout()

        buttom_buttons_layout = QGridLayout()

        self.start_button = QPushButton(f"Start ({self.shortcut})")
        self.start_button.pressed.connect(self.start_button_pressed)

        self.stop_button = QPushButton(f"Stop ({self.shortcut})")
        self.stop_button.pressed.connect(self.start_button_pressed)

        self.hotkey_settings_button = QPushButton("Hotkey settings")
        self.hotkey_settings_button.pressed.connect(self.hotkey_setting_clicked)

        self.help_button = QPushButton("Help?") # Yeah I need to work on this ig?

        for btn in [self.start_button, self.stop_button, self.hotkey_settings_button, self.help_button]:
            btn.setStyleSheet("padding: 20px 40px 20px 40px; font-size: 8pt;")

        buttom_buttons_layout.addWidget(self.start_button, 0, 0)
        buttom_buttons_layout.addWidget(self.stop_button, 0, 1)
        buttom_buttons_layout.addWidget(self.hotkey_settings_button, 1, 0)
        buttom_buttons_layout.addWidget(self.help_button, 1, 1)
        round_margin = 10
        buttom_buttons_layout.setContentsMargins(round_margin, round_margin, round_margin, round_margin)
        buttom_buttons_layout.setSpacing(10)

        interval_group = QGroupBox("Click interval")

        time_layout = QGridLayout()

        hlabel = QLabel("Hour")
        self.hour_input = QSpinBox()
        self.hour_input.setValue(self.hour)
        self.hour_input.valueChanged.connect(self.change_delay)

        mlabel = QLabel("Minute")
        self.minute_input = QSpinBox()
        self.minute_input.setValue(self.minute)
        self.minute_input.valueChanged.connect(self.change_delay)

        slabel = QLabel("Second")
        self.second_input = QSpinBox()
        self.second_input.setValue(self.second)
        self.second_input.valueChanged.connect(self.change_delay)

        mslabel = QLabel("Millisecond")
        self.milsecond_input = QSpinBox()
        self.milsecond_input.setValue(self.milsecond)
        self.milsecond_input.valueChanged.connect(self.change_delay)

        self.change_delay()

        for label in [hlabel, mlabel, slabel, mslabel]:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            label.setContentsMargins(0, 0, 0, 0)

        for input_box in [self.hour_input, self.minute_input, self.second_input, self.milsecond_input]:
            input_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            input_box.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            input_box.setAlignment(Qt.AlignmentFlag.AlignRight)
            input_box.setSingleStep(1)
            input_box.setMinimum(0)

        self.shortcut_handler = ShortcutHandler()
        self.shortcut_handler.set_hotkey(self.shortcut)
        self.shortcut_handler.triggered.connect(self.start_button_pressed)

        time_layout.addWidget(hlabel, 0, 0)
        time_layout.addWidget(mlabel, 0, 1)
        time_layout.addWidget(slabel, 0, 2)
        time_layout.addWidget(mslabel, 0, 3)

        time_layout.addWidget(self.hour_input, 1, 0)
        time_layout.addWidget(self.minute_input, 1, 1)
        time_layout.addWidget(self.second_input, 1, 2)
        time_layout.addWidget(self.milsecond_input, 1, 3)

        interval_group.setLayout(time_layout)
        interval_group.setFixedHeight(100)

        click_settings_layout = QHBoxLayout()

        click_options_group = QGroupBox("Click options")

        click_options = QGridLayout()

        self.mouse_btn_label = QLabel("Mouse button")
        self.click_type_label = QLabel("Click type")

        self.mouse_btn_cbox = QComboBox()
        self.mouse_btn_cbox.addItems(["Left click", "Right click", "Middle click"])
        self.mouse_btn_cbox.setCurrentIndex(self.current_click)
        self.mouse_btn_cbox.currentIndexChanged.connect(self.set_click_index)

        self.click_type_cbox = QComboBox()
        self.click_type_cbox.addItems(["Single", "Double"])
        self.click_type_cbox.setCurrentIndex(self.click_type)
        self.click_type_cbox.currentIndexChanged.connect(self.set_click_type)

        click_options.addWidget(self.mouse_btn_label, 0, 0)
        click_options.addWidget(self.mouse_btn_cbox, 0, 1)
        click_options.addWidget(self.click_type_label, 1, 0)
        click_options.addWidget(self.click_type_cbox, 1, 1)

        click_options_group.setLayout(click_options)

        click_repeat_group = QGroupBox("Click repeat")

        click_repeat_top_row = QHBoxLayout()
        click_repeat_bot_row = QHBoxLayout()
        click_repeat_holder = QVBoxLayout()

        self.repeat_radio_button = QRadioButton("Repeat")
        self.repeat_until_stop_radio_button = QRadioButton("Repeat until stopped")
        self.amount_sbox = QSpinBox()
        self.amount_sbox.setMinimum(1)
        self.amount_sbox.setValue(self.amount)
        self.amount_sbox.valueChanged.connect(self.amount_changed)
        self.amount_sbox_label = QLabel("times")


        self.click_repeat_button_group = QButtonGroup()
        self.click_repeat_button_group.addButton(self.repeat_until_stop_radio_button)
        self.click_repeat_button_group.addButton(self.repeat_radio_button)

        if self.repeat:
            self.repeat_radio_button.setChecked(True)
        else:
            self.repeat_until_stop_radio_button.setChecked(True)

        self.click_repeat_button_group.buttonToggled.connect(self.radio_button_handler)

        click_repeat_top_row.addWidget(self.repeat_radio_button)
        click_repeat_top_row.addWidget(self.amount_sbox)
        click_repeat_top_row.addWidget(self.amount_sbox_label)

        click_repeat_bot_row.addWidget(self.repeat_until_stop_radio_button)

        click_repeat_holder.addStretch()
        click_repeat_holder.addLayout(click_repeat_top_row)
        click_repeat_holder.addStretch()
        click_repeat_holder.addLayout(click_repeat_bot_row)
        click_repeat_holder.addStretch()

        click_repeat_group.setLayout(click_repeat_holder)

        click_settings_layout.addWidget(click_options_group)
        click_settings_layout.addWidget(click_repeat_group)

        cursor_pos_group = QGroupBox("Cursor position")
        cursor_pos_layout = QHBoxLayout()

        self.location_btn_group = QButtonGroup()
        self.cur_location_radio_btn = QRadioButton("Current location")
        self.dif_location_radio_btn = QRadioButton()
        self.location_btn_group.addButton(self.cur_location_radio_btn)
        self.location_btn_group.addButton(self.dif_location_radio_btn)

        if self.is_current_location:
            self.dif_location_radio_btn.setChecked(True)
        else:
            self.cur_location_radio_btn.setChecked(True)

        self.location_btn_group.buttonToggled.connect(self.change_location)

        self.pick_location_btn = QPushButton("Pick location")
        self.pick_location_btn.setStyleSheet("padding: 10px 15px 10px 15px;")
        self.pick_location_btn.pressed.connect(self.start_location_pick)

        self.x_label = QLabel('X')
        self.x_location = QSpinBox(maximum=999999999, value=self.x)
        self.x_location.valueChanged.connect(self.change_location_enter)

        self.y_label = QLabel('Y')
        self.y_location = QSpinBox(maximum=999999999, value=self.y)
        self.y_location.valueChanged.connect(self.change_location_enter)

        for sbox in [self.x_location, self.y_location]:
            sbox.setMinimumWidth(80)
            sbox.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            sbox.setAlignment(Qt.AlignmentFlag.AlignRight)

        cursor_pos_layout.addWidget(self.cur_location_radio_btn)
        cursor_pos_layout.addStretch()
        cursor_pos_layout.addWidget(self.dif_location_radio_btn)
        cursor_pos_layout.addWidget(self.pick_location_btn)
        cursor_pos_layout.addWidget(self.x_label)
        cursor_pos_layout.addWidget(self.x_location)
        cursor_pos_layout.addWidget(self.y_label)
        cursor_pos_layout.addWidget(self.y_location)

        cursor_pos_group.setLayout(cursor_pos_layout)

        layout.addWidget(interval_group)
        layout.addLayout(click_settings_layout)
        layout.addWidget(cursor_pos_group)
        layout.addLayout(buttom_buttons_layout)

        w = QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)

        self.setFixedSize(500, 450)

        self.show()

    def hotkey_setting_clicked(self):
        dlg = HotkeyDialogBox(self, self.shortcut)
        dlg.shortcut_selected.connect(self.hotkey_accepted)
        dlg.exec()

    def hotkey_accepted(self, hotkey):
        self.shortcut_handler.set_hotkey(hotkey)
        self.shortcut = hotkey
        self.start_button.setText(f"Start ({self.shortcut})")
        self.stop_button.setText(f"Stop ({self.shortcut})")
        self.save_to_json()

    def change_location_enter(self):
        self.x = self.x_location.value()
        self.y = self.y_location.value()
        self.save_to_json()

    def change_location(self, btn, checked):
        if btn == self.cur_location_radio_btn:
            self.is_current_location = False
        else:
            self.is_current_location = True
        self.save_to_json()

    def start_location_pick(self):
        threading.Thread(target=self.pick_location, daemon=True).start()

    def pick_location(self):
        self.pick_location_btn.setText("Listening...")

        def on_click(x, y, button, pressed):
            if pressed:
                self.pick_location_btn.setText("Pick location")
                self.x_location.setValue(x)
                self.y_location.setValue(y)
                listener.stop()

        listener = Listener(on_click=on_click)
        listener.start()
        listener.join()

    def amount_changed(self, value):
        self.amount = value
        self.save_to_json()

    def radio_button_handler(self, btn, checked):
        if btn == self.repeat_radio_button:
            self.repeat = True
        else:
            self.repeat = False
        self.save_to_json()

    def set_click_index(self, index : int):
        self.current_click = index
        self.save_to_json()

    def set_click_type(self, type : int):
        self.click_type = type
        self.save_to_json()

    def change_delay(self):
        self.interval = self.hour_input.value() * 3600 + self.minute_input.value() * 60 + self.second_input.value() + self.milsecond_input.value() / 1000
        self.save_to_json()

    def start_button_pressed(self):
        if not self.running and self.interval != 0:
            self.start_button.setDisabled(not self.running)
            self.stop_button.setDisabled(self.running)
            threading.Thread(target=self.click, daemon=True).start()
        else:
            self.clicking = False
            self.start_button.setDisabled(not self.running)
            self.stop_button.setDisabled(self.running)
        
        self.running = not self.running

    def click(self):
        time.sleep(0.001) # Python thread needs this from some strange reason
        if not self.repeat:
            while self.running:
                time.sleep(self.interval)
                if not self.running:
                    return
                if self.is_current_location:
                    self.mouse.position(self.x, self.y)
                self.mouse.click(self.index_to_mouse_button[self.current_click])
                if self.click_type == 1: self.mouse.click(self.index_to_mouse_button[self.current_click])
        else:
            for i in range(self.amount):
                time.sleep(self.interval)
                if not self.running:
                    return
                if self.is_current_location:
                    self.mouse.position = (self.x, self.y)
                self.mouse.click(self.index_to_mouse_button[self.current_click])
                if self.click_type == 1: self.mouse.click(self.index_to_mouse_button[self.current_click])
            self.start_button_pressed()

    def save_to_json(self):
        with open(self.settings_path, 'r', encoding="utf-8") as f:
            data = json.load(f)
            data["shortcut"] = self.shortcut
            data["hour"] = self.hour_input.value()
            data["min"] = self.minute_input.value()
            data["sec"] = self.second_input.value()
            data["milsec"] = self.milsecond_input.value()
            data["mouse_btn"] = self.current_click
            data["click_type"] = self.click_type
            data["repeat"] = self.repeat
            data["amount"] = self.amount
            data["set_pos"] = self.is_current_location
            data["x"] = self.x
            data["y"] = self.y
            f.close()
        with open(self.settings_path, 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            f.close()

app = QApplication(sys.argv)
window = MainWindow()
window.setWindowIcon(QIcon("gubi_mans_icon.ico"))
window.resize(400, 300)
app.exec()