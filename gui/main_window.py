import sys
import os

from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel,
                             QApplication, QPushButton, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon

from gui.simple_tab import SimpleTab
from gui.minecraft_tab import MinecraftTab
from gui.macro_tab import MacroTab
from gui.pixel_tab import PixelTab
from gui.hotkey_dialog import HotkeyDialog
from workers.simple_clicker import SimpleClicker
from workers.minecraft_clicker import MinecraftClicker
from workers.macro_worker import MacroWorker
from workers.pixel_bot import PixelBot
from utils.config_manager import ConfigManager
from utils.input_manager import InputManager

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:

        base_path = sys._MEIPASS
    except Exception:

        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Herakalka")
        self.setGeometry(100, 100, 590, 620)
        self.setMinimumSize(500, 480)

        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_settings()
        self.worker = None
        self.is_working = False

        
        try:
            # Устанавливаем иконку окна, используя нашу надежную функцию
            self.setWindowIcon(QIcon(resource_path('icon.ico')))

            # Загружаем файл стилей
            style_path = resource_path(os.path.join('gui', 'style.qss'))
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error loading resources (icon/stylesheet): {e}")

        # Основная структура окна
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        # Вкладки
        self.tabs = QTabWidget()
        self.simple_tab = SimpleTab()
        self.minecraft_tab = MinecraftTab()
        self.macro_tab = MacroTab()
        self.pixel_tab = PixelTab(self)
        self.tabs.addTab(self.simple_tab, "Простой")
        self.tabs.addTab(self.minecraft_tab, "Minecraft")
        self.tabs.addTab(self.macro_tab, "Макросы")
        self.tabs.addTab(self.pixel_tab, "Пиксельный бот")
        self.main_layout.addWidget(self.tabs)

        # Нижняя панель (кнопки и статус)
        bottom_layout = QHBoxLayout()
        self.start_stop_button = QPushButton("Старт")
        self.start_stop_button.setCheckable(True)
        self.hotkey_button = QPushButton()
        bottom_layout.addWidget(self.start_stop_button)
        bottom_layout.addWidget(self.hotkey_button)

        status_layout = QHBoxLayout()
        self.status_label = QLabel("Готов к работе.")
        status_layout.addWidget(self.status_label, 1)

        self.main_layout.addLayout(status_layout)
        self.main_layout.addLayout(bottom_layout)

        # Применяем сохраненные настройки
        self.apply_settings()

        # Инициализация менеджера ввода (слушателя горячих клавиш)
        self.input_manager = InputManager()
        self.input_manager.set_primary_hotkey(self.settings.get("main", {}).get("hotkey", "Key.f6"))
        
        # Подключение сигналов и слотов
        self.connect_signals()
        
        # Запускаем слушатель горячих клавиш
        self.input_manager.start()
        # Вызываем смену вкладки, чтобы зарегистрировать нужные вторичные хоткеи
        self.on_tab_changed(self.tabs.currentIndex())

    def connect_signals(self):
        """Централизованное подключение всех сигналов и слотов."""
        self.start_stop_button.clicked.connect(self.toggle_current_worker_button)
        self.hotkey_button.clicked.connect(self.change_hotkey)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Сигналы от InputManager
        self.input_manager.primary_hotkey_pressed.connect(self.toggle_current_worker)
        self.input_manager.secondary_hotkey_pressed.connect(self.handle_secondary_hotkey)
        self.input_manager.fast_click_detected.connect(self.handle_fast_click)
        
        # Сигналы от вкладок
        self.simple_tab.register_hotkey_signal.connect(self.input_manager.register_secondary_hotkey)
        self.simple_tab.unregister_hotkey_signal.connect(self.input_manager.unregister_secondary_hotkey)
        self.pixel_tab.register_hotkey_signal.connect(self.input_manager.register_secondary_hotkey)
        self.pixel_tab.unregister_hotkey_signal.connect(self.input_manager.unregister_secondary_hotkey)
        self.minecraft_tab.settings_changed.connect(self.update_input_manager_settings)
        self.macro_tab.play_macro_signal.connect(self.play_macro_preview)

    def start_worker(self):
        if self.is_working:
            return
        current_tab_index = self.tabs.currentIndex()
        settings = None
        self.worker = None

        if current_tab_index == 0: # Простой кликер
            settings = self.simple_tab.get_settings()
            self.worker = SimpleClicker(**settings)
        elif current_tab_index == 1: # Minecraft кликер
            settings = self.minecraft_tab.get_settings()
            self.worker = MinecraftClicker(interval_ms=settings['interval_ms'], humanize=settings['humanize'], button_str=settings['button'])
        elif current_tab_index == 2: # Макросы
            settings = self.macro_tab.get_settings()
            if not settings['mode']:
                self.update_status("Выберите макрос или введите имя для записи.")
                return
            self.worker = MacroWorker(**settings)
        elif current_tab_index == 3: # Пиксельный бот
            settings = self.pixel_tab.get_settings(for_worker=True)
            if not settings:
                return
            self.worker = PixelBot(**settings)

        if self.worker:
            self.is_working = True
            self.set_ui_enabled(False)
            self.start_stop_button.setChecked(True)
            self.start_stop_button.setText("Стоп (Hotkey)")
            self.worker.status_update.connect(self.update_status)
            if settings and settings.get('mode') == 'record':
                self.worker.finished.connect(self.on_macro_record_finished)
            self.worker.finished.connect(self.on_worker_stopped)
            self.worker.start()

    def stop_worker(self):
        if self.is_working and self.worker:
            self.worker.stop()

    def on_worker_stopped(self):
        self.is_working = False
        self.set_ui_enabled(True)
        self.start_stop_button.setChecked(False)
        self.start_stop_button.setText("Старт (Hotkey)")
        self.update_status("Готов к работе.")
        self.worker = None

    def play_macro_preview(self, events, humanize, speed, repeat):
        if self.is_working:
            self.update_status("Дождитесь завершения текущей операции.")
            return
        settings = {
            'mode': 'play', 'events': events, 'humanize': humanize, 
            'speed_multiplier': speed, 'repeat_count': repeat
        }
        self.worker = MacroWorker(**settings)
        self.is_working = True
        self.set_ui_enabled(False)
        self.start_stop_button.setChecked(True)
        self.start_stop_button.setText("Стоп (Hotkey)")
        self.worker.status_update.connect(self.update_status)
        self.worker.finished.connect(self.on_worker_stopped)
        self.worker.start()

    def update_input_manager_settings(self):
        mc_settings = self.minecraft_tab.get_settings()
        self.input_manager.set_fast_click_settings(
            enabled=mc_settings['fast_click_activation'],
            count=mc_settings['fast_click_count'],
            max_interval_ms=mc_settings['fast_click_interval_ms']
        )
        
    def update_hotkey_button_text(self):
        hotkey = self.settings.get("main", {}).get("hotkey", "Key.f6")
        
        if hotkey.startswith("mouse."):
            mouse_map = {"mouse.left": "ЛКМ", "mouse.right": "ПКМ", "mouse.middle": "СКМ", "mouse.x1": "Mouse 4", "mouse.x2": "Mouse 5"}
            display_text = mouse_map.get(hotkey, "MOUSE")
        else:
            parts = [part.replace("Key.", "").upper() for part in hotkey.split('+')]
            display_text = " + ".join(parts)
            
        self.hotkey_button.setText(f"Hotkey: {display_text}")

    def gather_all_settings(self):
        """Собирает настройки со всех вкладок для сохранения в файл."""
        return {
            "main": {"hotkey": self.settings.get("main", {}).get("hotkey", "Key.f6")},
            "simple": self.simple_tab.get_settings(),
            "minecraft": self.minecraft_tab.get_settings(),
            "macro": self.macro_tab.get_persistent_settings(),
            "pixel": self.pixel_tab.get_settings(for_worker=False) if self.pixel_tab.get_settings(for_worker=False) else {}
        }

    def apply_settings(self):
        """Применяет загруженные настройки к элементам интерфейса."""
        self.update_hotkey_button_text()
        self.simple_tab.set_settings(self.settings.get('simple', {}))
        self.minecraft_tab.set_settings(self.settings.get('minecraft', {}))
        self.macro_tab.set_settings(self.settings.get('macro', {}))
        self.pixel_tab.set_settings(self.settings.get('pixel', {}))

    def closeEvent(self, event):
        """Событие при закрытии окна."""
        all_settings = self.gather_all_settings()
        self.config_manager.save_settings(all_settings)
        if self.is_working:
            self.stop_worker()
            if self.worker and not self.worker.wait(1000):
                 QMessageBox.warning(self, "Внимание", "Рабочий поток не смог завершиться корректно.")
        self.input_manager.stop_listening()
        if self.input_manager.isRunning():
            self.input_manager.quit()
            self.input_manager.wait(500)
        event.accept()

    def toggle_current_worker_button(self, checked):
        if checked != self.is_working:
            self.toggle_current_worker()

    def toggle_current_worker(self):
        if self.is_working:
            self.stop_worker()
        else:
            self.start_worker()

    def set_ui_enabled(self, enabled):
        """Включает/выключает элементы интерфейса на время работы кликера."""
        self.tabs.setEnabled(enabled)
        self.hotkey_button.setEnabled(enabled)
    
    def on_tab_changed(self, index):
        """Событие при смене вкладки."""
        self.input_manager.clear_secondary_hotkeys()
        current_widget = self.tabs.widget(index)
        if hasattr(current_widget, 'on_tab_selected'):
            current_widget.on_tab_selected()
        self.update_input_manager_settings()

    def handle_secondary_hotkey(self, key):
        """Обрабатывает нажатия вторичных хоткеев (F7, F8 и т.д.)."""
        current_widget = self.tabs.currentWidget()
        if hasattr(current_widget, 'handle_secondary_hotkey'):
            current_widget.handle_secondary_hotkey(key)

    def change_hotkey(self):
        """Открывает диалог смены основной горячей клавиши."""
        dialog = HotkeyDialog(self)
        dialog.hotkey_set.connect(self.set_new_hotkey)
        dialog.exec()

    def set_new_hotkey(self, hotkey_str):
        """Устанавливает новую основную горячую клавишу."""
        if "main" not in self.settings:
            self.settings["main"] = {}
        self.settings["main"]["hotkey"] = hotkey_str
        self.input_manager.set_primary_hotkey(hotkey_str)
        self.update_hotkey_button_text()

    def on_macro_record_finished(self):
        """Событие, когда рабочий поток записи макроса завершился."""
        if hasattr(self.sender(), 'events'):
            self.macro_tab.on_record_finished(self.sender().events)

    def handle_fast_click(self):
        """Обрабатывает сигнал о быстрых кликах (для Minecraft-режима)."""
        if self.tabs.currentIndex() == 1:
            self.toggle_current_worker()

    def update_status(self, message):
        """Обновляет текст в строке статуса."""
        self.status_label.setText(message)