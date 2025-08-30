import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QSpinBox,
                             QListWidget, QLineEdit, QCheckBox, QLabel, QSlider, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal


app_data_path = os.getenv('APPDATA')
MACRO_DIR = os.path.join(app_data_path, "Herakalka", "macros")

class MacroTab(QWidget):
    play_macro_signal = pyqtSignal(list, bool, float, int)

    def __init__(self):
        super().__init__()
        if not os.path.exists(MACRO_DIR):
            os.makedirs(MACRO_DIR)
        self.recorded_events = []
        self.init_ui()
        self.load_macros()

    def init_ui(self):
        layout = QVBoxLayout(self)
        list_group = QGroupBox("Управление макросами")
        list_layout = QVBoxLayout()
        self.macro_list_widget = QListWidget()
        list_layout.addWidget(self.macro_list_widget)
        list_buttons_layout = QHBoxLayout()
        self.delete_macro_btn = QPushButton("Удалить выбранный")
        list_buttons_layout.addWidget(self.delete_macro_btn)
        list_layout.addLayout(list_buttons_layout)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        playback_group = QGroupBox("Настройки воспроизведения")
        playback_layout = QVBoxLayout()
        self.humanize_checkbox = QCheckBox("Воспроизводить с 'человеческими' неточностями")
        self.humanize_checkbox.setChecked(True)
        playback_layout.addWidget(self.humanize_checkbox)
        repeat_layout = QHBoxLayout()
        repeat_layout.addWidget(QLabel("Повторить:"))
        self.repeat_count_spinbox = QSpinBox()
        self.repeat_count_spinbox.setRange(0, 999)
        self.repeat_count_spinbox.setToolTip("0 = бесконечно")
        self.repeat_count_spinbox.setValue(1)
        repeat_layout.addWidget(self.repeat_count_spinbox)
        repeat_layout.addWidget(QLabel("раз (0 - бесконечно)"))
        playback_layout.addLayout(repeat_layout)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Скорость:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(0, 8)
        self.speed_slider.setValue(3)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_label = QLabel("1.0x")
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        playback_layout.addLayout(speed_layout)
        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)
        record_group = QGroupBox("Запись нового макроса")
        record_layout = QVBoxLayout()
        self.record_status_label = QLabel("Статус: Ожидание")
        record_layout.addWidget(self.record_status_label)
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Имя файла:"))
        self.macro_name_input = QLineEdit()
        self.macro_name_input.setPlaceholderText("например, my_macro")
        name_layout.addWidget(self.macro_name_input)
        name_layout.addWidget(QLabel(".json"))
        record_layout.addLayout(name_layout)
        record_buttons_layout = QHBoxLayout()
        self.preview_btn = QPushButton("Воспроизвести записанное")
        self.preview_btn.setEnabled(False)
        self.save_btn = QPushButton("Сохранить записанное")
        self.save_btn.setEnabled(False)
        record_buttons_layout.addWidget(self.preview_btn)
        record_buttons_layout.addWidget(self.save_btn)
        record_layout.addLayout(record_buttons_layout)
        record_layout.addWidget(QLabel("Запись/Воспроизведение файла контролируется горячей клавишей."))
        record_group.setLayout(record_layout)
        layout.addWidget(record_group)
        layout.addStretch(1)
        self.delete_macro_btn.clicked.connect(self.delete_selected_macro)
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        self.preview_btn.clicked.connect(self.preview_recorded_macro)
        self.save_btn.clicked.connect(self.save_recorded_macro)
        

        self.macro_list_widget.itemClicked.connect(self.on_macro_selected)
        self.macro_name_input.textChanged.connect(self.on_record_name_typed)
        
        self.update_speed_label(self.speed_slider.value())

    def on_macro_selected(self, item):

        self.macro_name_input.blockSignals(True)
        self.macro_name_input.clear()
        self.macro_name_input.blockSignals(False)
        

        self.record_status_label.setText(f"Статус: Выбран '{item.text()}' для воспр.")

    def on_record_name_typed(self, text):

        if text:
            self.macro_list_widget.blockSignals(True)
            self.macro_list_widget.clearSelection()
            self.macro_list_widget.blockSignals(False)
        

        self.record_status_label.setText("Статус: Ожидание")

    def get_settings(self):
        record_name = self.macro_name_input.text().strip()
        selected_items = self.macro_list_widget.selectedItems()
        
        if record_name:
            mode = 'record'
            macro_path = os.path.join(MACRO_DIR, record_name + ".json")
        elif selected_items:
            mode = 'play'
            macro_path = os.path.join(MACRO_DIR, selected_items[0].text())
        else:
            mode, macro_path = None, None
            
        return {
            'mode': mode, 'macro_file': macro_path,
            'humanize': self.humanize_checkbox.isChecked(),
            'speed_multiplier': self.get_speed_multiplier(),
            'repeat_count': self.repeat_count_spinbox.value()
        }
    
    def get_persistent_settings(self):
        return {
            'humanize': self.humanize_checkbox.isChecked(),
            'speed_slider_value': self.speed_slider.value(),
            'repeat_count': self.repeat_count_spinbox.value()
        }

    def set_settings(self, settings):
        self.humanize_checkbox.setChecked(settings.get('humanize', True))
        self.speed_slider.setValue(settings.get('speed_slider_value', 3))
        self.repeat_count_spinbox.setValue(settings.get('repeat_count', 1))

    def load_macros(self):
        self.macro_list_widget.clear()
        try:
            files = [f for f in os.listdir(MACRO_DIR) if f.endswith('.json')]
            self.macro_list_widget.addItems(files)
        except FileNotFoundError: pass
        
    def update_speed_label(self, value): self.speed_label.setText(f"{self.get_speed_multiplier()}x")
    
    def get_speed_multiplier(self): return [0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0][self.speed_slider.value()]
    
    def delete_selected_macro(self):
        selected_items = self.macro_list_widget.selectedItems()
        if not selected_items: return
        item = selected_items[0]; filename = item.text()
        reply = QMessageBox.question(self, "Удаление макроса", f"Вы уверены, что хотите удалить файл '{filename}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(os.path.join(MACRO_DIR, filename))
                self.macro_list_widget.takeItem(self.macro_list_widget.row(item))
            except OSError as e: QMessageBox.warning(self, "Ошибка", f"Не удалось удалить файл: {e}")
            
    def on_record_finished(self, events):
        self.recorded_events = events
        self.record_status_label.setText(f"Записано {len(events)} событий. Готово к сохранению/просмотру.")
        self.preview_btn.setEnabled(True); self.save_btn.setEnabled(True)
        
    def preview_recorded_macro(self):
        if self.recorded_events: self.play_macro_signal.emit(self.recorded_events, self.humanize_checkbox.isChecked(), self.get_speed_multiplier(), 1)
        
    def save_recorded_macro(self):
        record_name = self.macro_name_input.text().strip()
        if not record_name: QMessageBox.warning(self, "Ошибка", "Введите имя файла для сохранения макроса."); return
        if not self.recorded_events: QMessageBox.warning(self, "Ошибка", "Нет записанных событий для сохранения."); return
        macro_path = os.path.join(MACRO_DIR, record_name + ".json")
        try:
            with open(macro_path, 'w') as f: json.dump(self.recorded_events, f, indent=4)
            QMessageBox.information(self, "Успех", f"Макрос сохранен в {macro_path}")
            self.load_macros(); self.recorded_events = []; self.record_status_label.setText("Статус: Ожидание")
            self.preview_btn.setEnabled(False); self.save_btn.setEnabled(False)
        except Exception as e: QMessageBox.critical(self, "Ошибка сохранения", str(e))