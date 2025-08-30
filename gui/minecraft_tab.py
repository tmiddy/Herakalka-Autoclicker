from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
                             QSpinBox, QRadioButton, QCheckBox, QComboBox)
from PyQt6.QtCore import pyqtSignal

class MinecraftTab(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        settings_group = QGroupBox("Настройки Minecraft кликера")
        settings_layout = QVBoxLayout()
        interval_mode_layout = QHBoxLayout()
        interval_mode_layout.addWidget(QLabel("Режим интервала:"))
        self.cps_radio = QRadioButton("CPS")
        self.ms_radio = QRadioButton("ms")
        self.cps_radio.setChecked(True)
        interval_mode_layout.addWidget(self.cps_radio)
        interval_mode_layout.addWidget(self.ms_radio)
        settings_layout.addLayout(interval_mode_layout)
        interval_layout = QHBoxLayout()
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 1000)
        self.interval_spinbox.setValue(10)
        self.update_interval_mode()
        interval_layout.addWidget(QLabel("Значение:"))
        interval_layout.addWidget(self.interval_spinbox)
        settings_layout.addLayout(interval_layout)
        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel("Кнопка мыши:"))
        self.button_combo = QComboBox()
        self.button_combo.addItems(["ЛКМ", "ПКМ"])
        button_layout.addWidget(self.button_combo)
        settings_layout.addLayout(button_layout)
        self.humanize_checkbox = QCheckBox("Имитировать действия человека")
        self.humanize_checkbox.setChecked(True)
        self.humanize_checkbox.setToolTip("Добавляет случайные задержки и небольшие смещения курсора.")
        settings_layout.addWidget(self.humanize_checkbox)
        self.fast_click_group = QGroupBox("Активация быстрыми кликами ЛКМ")
        self.fast_click_group.setCheckable(True)
        self.fast_click_group.setChecked(False)
        fast_click_layout = QVBoxLayout()
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Кол-во кликов:"))
        self.fast_click_count = QSpinBox()
        self.fast_click_count.setRange(2, 5)
        self.fast_click_count.setValue(3)
        count_layout.addWidget(self.fast_click_count)
        fast_click_layout.addLayout(count_layout)
        interval_layout_fc = QHBoxLayout()
        interval_layout_fc.addWidget(QLabel("Макс. интервал (ms):"))
        self.fast_click_interval = QSpinBox()
        self.fast_click_interval.setRange(50, 500)
        self.fast_click_interval.setValue(150)
        interval_layout_fc.addWidget(self.fast_click_interval)
        fast_click_layout.addLayout(interval_layout_fc)
        self.fast_click_group.setLayout(fast_click_layout)
        settings_layout.addWidget(self.fast_click_group)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        layout.addStretch(1)

        self.cps_radio.toggled.connect(self.update_interval_mode)


        self.fast_click_group.toggled.connect(self.settings_changed.emit)
        self.fast_click_count.valueChanged.connect(self.settings_changed.emit)
        self.fast_click_interval.valueChanged.connect(self.settings_changed.emit)

    def update_interval_mode(self):
        is_cps = self.cps_radio.isChecked()
        self.interval_spinbox.setSuffix(" CPS" if is_cps else " ms")
        self.interval_spinbox.setToolTip("Кликов в секунду" if is_cps else "Миллисекунд между кликами")
        self.interval_spinbox.setRange(1, 100) if is_cps else self.interval_spinbox.setRange(10, 10000)

    def get_settings(self):
        is_cps = self.cps_radio.isChecked()
        interval_value = self.interval_spinbox.value()
        interval_ms = (1000 / interval_value) if is_cps else interval_value
        return {
            'interval_ms': interval_ms,
            'interval_mode': 'cps' if is_cps else 'ms',
            'interval_value': interval_value,
            'humanize': self.humanize_checkbox.isChecked(),
            'button': self.button_combo.currentText(),
            'fast_click_activation': self.fast_click_group.isChecked(),
            'fast_click_count': self.fast_click_count.value(),
            'fast_click_interval_ms': self.fast_click_interval.value()
        }

    def set_settings(self, settings):
        if settings.get('interval_mode') == 'ms':
            self.ms_radio.setChecked(True)
        else:
            self.cps_radio.setChecked(True)

        self.interval_spinbox.setValue(settings.get('interval_value', 10))
        self.humanize_checkbox.setChecked(settings.get('humanize', True))
        
        button_text = settings.get('button', 'ЛКМ')
        index = self.button_combo.findText(button_text)
        if index != -1: self.button_combo.setCurrentIndex(index)

        self.fast_click_group.setChecked(settings.get('fast_click_activation', False))
        self.fast_click_count.setValue(settings.get('fast_click_count', 3))
        self.fast_click_interval.setValue(settings.get('fast_click_interval_ms', 150))