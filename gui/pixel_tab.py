from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
                             QPushButton, QSpinBox, QRadioButton, QColorDialog, QMessageBox)
from PyQt6.QtGui import QPalette, QColor, QKeyEvent, QMouseEvent
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import pyautogui

class PixelTab(QWidget):
    register_hotkey_signal = pyqtSignal(str)
    unregister_hotkey_signal = pyqtSignal(str)
    
    def __init__(self, main_window_ref):
        super().__init__()
        self.main_window = main_window_ref
        self.top_left_coord = None
        self.bottom_right_coord = None
        self.target_color = None
        self.capture_corner = None
        self.capture_timer = QTimer(self)
        self.capture_timer.setInterval(1000)
        self.capture_timer.timeout.connect(self.update_capture_countdown)
        self.countdown = 3
        self.init_ui()


    def init_ui(self):
        layout = QVBoxLayout(self)
        area_group = QGroupBox("Область поиска")
        area_layout = QVBoxLayout()
        area_mode_layout = QHBoxLayout()
        self.full_screen_radio = QRadioButton("Весь экран")
        self.custom_area_radio = QRadioButton("Выбранная область")
        self.full_screen_radio.setChecked(True)
        area_mode_layout.addWidget(self.full_screen_radio)
        area_mode_layout.addWidget(self.custom_area_radio)
        area_layout.addLayout(area_mode_layout)
        self.custom_area_widget = QWidget()
        custom_area_layout = QVBoxLayout(self.custom_area_widget)
        custom_area_layout.setContentsMargins(0, 5, 0, 0)
        buttons_layout = QHBoxLayout()
        self.select_top_left_btn = QPushButton("Захват ЛВ угла (F8)")
        self.select_bottom_right_btn = QPushButton("Захват ПН угла (F9)")
        buttons_layout.addWidget(self.select_top_left_btn)
        buttons_layout.addWidget(self.select_bottom_right_btn)
        custom_area_layout.addLayout(buttons_layout)
        coords_layout = QHBoxLayout()
        self.top_left_label = QLabel("Верхний левый: (не задан)")
        self.bottom_right_label = QLabel("Правый нижний: (не задан)")
        coords_layout.addWidget(self.top_left_label)
        coords_layout.addWidget(self.bottom_right_label)
        custom_area_layout.addLayout(coords_layout)
        self.countdown_label = QLabel("")
        self.countdown_label.setStyleSheet("font-weight: bold; color: #d08770;")
        custom_area_layout.addWidget(self.countdown_label, 0, Qt.AlignmentFlag.AlignCenter)
        area_layout.addWidget(self.custom_area_widget)
        area_group.setLayout(area_layout)
        layout.addWidget(area_group)
        color_group = QGroupBox("Целевой цвет")
        color_layout = QVBoxLayout()
        self.select_color_btn = QPushButton("Выбрать цвет пипеткой")
        color_preview_layout = QHBoxLayout()
        self.color_preview = QLabel(" ")
        self.color_preview.setAutoFillBackground(False)
        self.color_preview.setFixedSize(50, 20)
        self.color_label = QLabel("Цвет не выбран")
        color_preview_layout.addWidget(self.color_preview)
        color_preview_layout.addWidget(self.color_label)
        color_layout.addWidget(self.select_color_btn)
        color_layout.addLayout(color_preview_layout)
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        click_group = QGroupBox("Действие при нахождении")
        click_layout = QVBoxLayout()
        self.click_pixel_radio = QRadioButton("Кликнуть по найденному пикселю")
        self.click_cursor_radio = QRadioButton("Кликнуть в текущей позиции курсора")
        self.click_pixel_radio.setChecked(True)
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Интервал проверки (ms):"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(10, 60000)
        self.interval_spinbox.setValue(100)
        interval_layout.addWidget(self.interval_spinbox)
        click_layout.addWidget(self.click_pixel_radio)
        click_layout.addWidget(self.click_cursor_radio)
        click_layout.addLayout(interval_layout)
        click_group.setLayout(click_layout)
        layout.addWidget(click_group)
        layout.addStretch(1)
        self.full_screen_radio.toggled.connect(self.update_area_mode)
        self.select_top_left_btn.clicked.connect(lambda: self.start_coord_capture('top_left'))
        self.select_bottom_right_btn.clicked.connect(lambda: self.start_coord_capture('bottom_right'))
        self.select_color_btn.clicked.connect(self.select_target_color)
        self.update_area_mode()

    def _update_color_widgets(self):
        if self.target_color:
            color = QColor(*self.target_color)
            self.color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #4c566a; border-radius: 3px;")
            self.color_label.setText(f"RGB: {self.target_color}")

    def get_settings(self, for_worker=True):
        # for_worker=True: возвращает данные, нужные для запуска PixelBot
        # for_worker=False: возвращает данные для сохранения в config.json

        persistent_settings = {
            'search_mode': 'fullscreen' if self.full_screen_radio.isChecked() else 'custom',
            'top_left': [self.top_left_coord.x, self.top_left_coord.y] if self.top_left_coord else None,
            'bottom_right': [self.bottom_right_coord.x, self.bottom_right_coord.y] if self.bottom_right_coord else None,
            'target_color': self.target_color,
            'click_target': 'pixel' if self.click_pixel_radio.isChecked() else 'cursor',
            'interval_ms': self.interval_spinbox.value()
        }
        
        if not for_worker:
            return persistent_settings


        if not self.target_color:
            self.main_window.update_status("Ошибка: Целевой цвет не выбран.")
            return None
        final_area = None
        if self.full_screen_radio.isChecked():
            screen_size = pyautogui.size()
            final_area = (0, 0, screen_size.width, screen_size.height)
        elif self.custom_area_radio.isChecked():
            if self.top_left_coord and self.bottom_right_coord:
                x = min(self.top_left_coord.x, self.bottom_right_coord.x)
                y = min(self.top_left_coord.y, self.bottom_right_coord.y)
                width = abs(self.bottom_right_coord.x - self.top_left_coord.x)
                height = abs(self.bottom_right_coord.y - self.top_left_coord.y)
                if width <= 0 or height <= 0:
                    self.main_window.update_status("Ошибка: Неверные координаты (ширина или высота <= 0).")
                    return None
                final_area = (x, y, width, height)
            else:
                self.main_window.update_status("Ошибка: Не все углы области поиска заданы.")
                return None
        
        return {'search_area': final_area, 'target_color': self.target_color, 
                'click_target': 'pixel' if self.click_pixel_radio.isChecked() else 'cursor', 
                'interval_ms': self.interval_spinbox.value()}


    def set_settings(self, settings):
        if settings.get('search_mode') == 'custom':
            self.custom_area_radio.setChecked(True)
        else:
            self.full_screen_radio.setChecked(True)

        tl = settings.get('top_left')
        if tl:

            self.top_left_coord = pyautogui.Point(tl[0], tl[1])
            self.top_left_label.setText(f"Верхний левый: {self.top_left_coord}")
            
        br = settings.get('bottom_right')
        if br:

            self.bottom_right_coord = pyautogui.Point(br[0], br[1])
            self.bottom_right_label.setText(f"Правый нижний: {self.bottom_right_coord}")

        color = settings.get('target_color')
        if color:
            self.target_color = tuple(color)
            self._update_color_widgets()

        if settings.get('click_target') == 'cursor':
            self.click_cursor_radio.setChecked(True)
        else:
            self.click_pixel_radio.setChecked(True)
        
        self.interval_spinbox.setValue(settings.get('interval_ms', 100))


    def on_tab_selected(self):
        self.register_hotkey_signal.emit('f8')
        self.register_hotkey_signal.emit('f9')
    def on_tab_deselected(self):
        self.unregister_hotkey_signal.emit('f8')
        self.unregister_hotkey_signal.emit('f9')
    def handle_secondary_hotkey(self, key):
        if key == 'f8': self.start_coord_capture('top_left')
        elif key == 'f9': self.start_coord_capture('bottom_right')
    def update_area_mode(self): self.custom_area_widget.setVisible(self.custom_area_radio.isChecked())
    def start_coord_capture(self, corner):
        if self.capture_timer.isActive(): return
        self.capture_corner = corner; self.countdown = 3
        self.countdown_label.setText(f"Наведите курсор... {self.countdown}")
        self.main_window.set_ui_enabled(False); self.capture_timer.start()
    def update_capture_countdown(self):
        self.countdown -= 1
        self.countdown_label.setText(f"Наведите курсор... {self.countdown}")
        if self.countdown <= 0:
            self.capture_timer.stop()
            self.capture_coord(self.capture_corner)
            self.countdown_label.setText("")
            self.main_window.set_ui_enabled(True)
    def capture_coord(self, corner):
        pos = pyautogui.position()
        if corner == 'top_left': self.top_left_coord = pos; self.top_left_label.setText(f"Верхний левый: {pos}")
        else: self.bottom_right_coord = pos; self.bottom_right_label.setText(f"Правый нижний: {pos}")
    def select_target_color(self):
        dialog = QColorDialog(self)
        dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        color = dialog.getColor()
        if color.isValid():
            self.target_color = color.getRgb()[:3]
            self._update_color_widgets()