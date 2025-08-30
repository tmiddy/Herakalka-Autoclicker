from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
                             QSpinBox, QCheckBox, QPushButton, QListWidget, QRadioButton)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QKeyEvent
import pyautogui


class KeyCaptureButton(QPushButton):
    key_captured = pyqtSignal(str)
    def __init__(self, text="Нажмите, чтобы назначить", parent=None):
        super().__init__(text, parent)
        self.key_str = ""
        self.is_capturing = False
        self.clicked.connect(self.start_capture)
    def start_capture(self):
        self.is_capturing = True
        self.setText("Нажмите клавишу...")
        self.setFocus()
    def keyPressEvent(self, event: QKeyEvent):
        if self.is_capturing:
            event.accept()
            key_name = self.get_key_name(event)
            if key_name:
                self.key_str = key_name
                self.setText(f"Клавиша: {key_name}")
                self.key_captured.emit(self.key_str)
                self.is_capturing = False
                self.clearFocus()
        else: super().keyPressEvent(event)
    def focusOutEvent(self, event):
        if self.is_capturing:
            self.is_capturing = False
            self.setText("Нажмите, чтобы назначить" if not self.key_str else f"Клавиша: {self.key_str}")
        super().focusOutEvent(event)
    def get_key_name(self, event):
        key = event.key()
        text = event.text()
        pynput_map = {
            Qt.Key.Key_Control: "ctrl", Qt.Key.Key_Shift: "shift", Qt.Key.Key_Alt: "alt", 
            Qt.Key.Key_Meta: "cmd", Qt.Key.Key_F1: "f1", Qt.Key.Key_F2: "f2", 
            Qt.Key.Key_F3: "f3", Qt.Key.Key_F4: "f4", Qt.Key.Key_F5: "f5", 
            Qt.Key.Key_F6: "f6", Qt.Key.Key_F7: "f7", Qt.Key.Key_F8: "f8", 
            Qt.Key.Key_F9: "f9", Qt.Key.Key_F10: "f10", Qt.Key.Key_F11: "f11", Qt.Key.Key_F12: "f12",
        }
        if key in pynput_map: return pynput_map[key]
        if text.strip(): return text.lower()
        return None

class SimpleTab(QWidget):
    register_hotkey_signal = pyqtSignal(str)
    unregister_hotkey_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.points_list = []
        self.click_button = "ЛКМ" # Значение по умолчанию
        self.init_ui()
        self._get_pos_timer = QTimer(self)
        self._get_pos_timer.setInterval(100)
        self._get_pos_timer.timeout.connect(self.update_pos_label)


    def init_ui(self):
        layout = QVBoxLayout(self)
        settings_group = QGroupBox("Настройки простого кликера")
        settings_layout = QVBoxLayout()
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Интервал (ms):"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 600000)
        self.interval_spinbox.setValue(100)
        interval_layout.addWidget(self.interval_spinbox)
        settings_layout.addLayout(interval_layout)
        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel("Кнопка для клика:"))
        self.mouse_lmb_radio = QRadioButton("ЛКМ")
        self.mouse_rmb_radio = QRadioButton("ПКМ")
        self.mouse_mmb_radio = QRadioButton("СКМ")
        self.key_radio = QRadioButton("Клавиша:")
        self.key_capture_btn = KeyCaptureButton()
        self.key_capture_btn.setEnabled(False)
        self.mouse_lmb_radio.setChecked(True)
        button_layout.addWidget(self.mouse_lmb_radio)
        button_layout.addWidget(self.mouse_rmb_radio)
        button_layout.addWidget(self.mouse_mmb_radio)
        button_layout.addWidget(self.key_radio)
        button_layout.addWidget(self.key_capture_btn, 1)
        settings_layout.addLayout(button_layout)
        self.mouse_lmb_radio.toggled.connect(self.update_button_choice)
        self.mouse_rmb_radio.toggled.connect(self.update_button_choice)
        self.mouse_mmb_radio.toggled.connect(self.update_button_choice)
        self.key_radio.toggled.connect(self.update_button_choice)
        self.key_capture_btn.key_captured.connect(self.set_captured_key)
        self.hold_checkbox = QCheckBox("Зажать кнопку (игнорирует интервал и точки)")
        settings_layout.addWidget(self.hold_checkbox)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        points_group = QGroupBox("Клик по координатам (если пусто - клик по курсору)")
        points_layout = QVBoxLayout()
        self.points_list_widget = QListWidget()
        points_layout.addWidget(self.points_list_widget)
        pos_layout = QHBoxLayout()
        self.add_point_btn = QPushButton("Добавить точку (F7)")
        self.add_point_btn.setToolTip("Также можно добавить точку нажатием клавиши F7")
        self.get_pos_btn = QPushButton("Отследить позицию")
        self.pos_label = QLabel("X: - Y: -")
        pos_layout.addWidget(self.add_point_btn)
        pos_layout.addWidget(self.get_pos_btn)
        pos_layout.addWidget(self.pos_label)
        points_layout.addLayout(pos_layout)
        btn_layout = QHBoxLayout()
        self.remove_point_btn = QPushButton("Удалить выбранную")
        self.clear_points_btn = QPushButton("Очистить список")
        btn_layout.addWidget(self.remove_point_btn)
        btn_layout.addWidget(self.clear_points_btn)
        points_layout.addLayout(btn_layout)
        points_group.setLayout(points_layout)
        layout.addWidget(points_group)
        layout.addStretch(1)
        self.add_point_btn.clicked.connect(self.add_current_pos)
        self.get_pos_btn.clicked.connect(self.toggle_pos_tracking)
        self.remove_point_btn.clicked.connect(self.remove_selected_point)
        self.clear_points_btn.clicked.connect(self.clear_all_points)

    def get_settings(self):
        self.update_button_choice()
        return {
            'interval_ms': self.interval_spinbox.value(),
            'button': self.click_button,
            'is_hold': self.hold_checkbox.isChecked(),
            'click_points': list(self.points_list)
        }


    def set_settings(self, settings):
        self.interval_spinbox.setValue(settings.get('interval_ms', 100))
        self.hold_checkbox.setChecked(settings.get('is_hold', False))
        
        button = settings.get('button', 'ЛКМ')
        if button == "ЛКМ": self.mouse_lmb_radio.setChecked(True)
        elif button == "ПКМ": self.mouse_rmb_radio.setChecked(True)
        elif button == "СКМ": self.mouse_mmb_radio.setChecked(True)
        else:
            self.key_radio.setChecked(True)
            self.key_capture_btn.key_str = button
            self.key_capture_btn.setText(f"Клавиша: {button}")
        
        self.clear_all_points()
        points = settings.get('click_points', [])
        for p in points:
            if isinstance(p, list) and len(p) == 2:
                self.points_list.append(tuple(p))
                self.points_list_widget.addItem(f"Точка {len(self.points_list)}: (X={p[0]}, Y={p[1]})")


    def on_tab_selected(self): self.register_hotkey_signal.emit('f7')
    def on_tab_deselected(self): self.unregister_hotkey_signal.emit('f7')
    def handle_secondary_hotkey(self, key):
        if key == 'f7': self.add_current_pos()
    def update_button_choice(self):
        self.key_capture_btn.setEnabled(self.key_radio.isChecked())
        if self.mouse_lmb_radio.isChecked(): self.click_button = "ЛКМ"
        elif self.mouse_rmb_radio.isChecked(): self.click_button = "ПКМ"
        elif self.mouse_mmb_radio.isChecked(): self.click_button = "СКМ"
        elif self.key_radio.isChecked(): self.click_button = self.key_capture_btn.key_str
    def set_captured_key(self, key): self.click_button = key
    def toggle_pos_tracking(self):
        if self._get_pos_timer.isActive():
            self._get_pos_timer.stop()
            self.get_pos_btn.setText("Отследить позицию")
        else:
            self._get_pos_timer.start()
            self.get_pos_btn.setText("Остановить отслеживание")
    def update_pos_label(self):
        x, y = pyautogui.position()
        self.pos_label.setText(f"X: {x} Y: {y}")
    def add_current_pos(self):
        x, y = pyautogui.position()
        self.points_list.append((x, y))
        self.points_list_widget.addItem(f"Точка {len(self.points_list)}: (X={x}, Y={y})")
    def remove_selected_point(self):
        current_row = self.points_list_widget.currentRow()
        if current_row > -1:
            self.points_list_widget.takeItem(current_row)
            del self.points_list[current_row]
    def clear_all_points(self):
        self.points_list.clear()
        self.points_list_widget.clear()