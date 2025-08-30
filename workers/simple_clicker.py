import time
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController
import pyautogui
from workers.base_worker import BaseWorker

class SimpleClicker(BaseWorker):
    def __init__(self, interval_ms, button, is_hold, click_points):
        super().__init__()
        self.interval_ms = interval_ms
        self.button_str = button
        self.button_to_press = self._get_button_object(button)
        self.is_hold = is_hold
        self.click_points = click_points
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.is_mouse_button = self.button_str in ['ЛКМ', 'ПКМ', 'СКМ']

    def _get_button_object(self, button_str):
        if button_str == 'ЛКМ': return Button.left
        elif button_str == 'ПКМ': return Button.right
        elif button_str == 'СКМ': return Button.middle
        else:
            if not button_str:
                return None
            try: return Key[button_str]
            except KeyError: return button_str

    def run(self):
        self.status_update.emit("Простой кликер запущен...")
        
        if self.is_hold:
            if self.button_to_press is None:
                self.status_update.emit("Ошибка: не выбрана клавиша для зажатия.")
                return

            if self.is_mouse_button: self.mouse.press(self.button_to_press)
            else: self.keyboard.press(self.button_to_press)
            self.status_update.emit(f"Клавиша '{self.button_str}' зажата...")
            while self._is_running: self.msleep(100)
            if self.is_mouse_button: self.mouse.release(self.button_to_press)
            else: self.keyboard.release(self.button_to_press)
            return

        if self.is_mouse_button:
            while self._is_running:
                if self.click_points:
                    original_pos = pyautogui.position()
                    for point in self.click_points:
                        if not self._is_running: break
                        pyautogui.moveTo(point[0], point[1], duration=0.1)
                        self.input_manager.is_synthetic_click = True
                        self.mouse.click(self.button_to_press)
                        self.input_manager.is_synthetic_click = False
                    pyautogui.moveTo(original_pos[0], original_pos[1], duration=0.1)
                else:
                    self.input_manager.is_synthetic_click = True
                    self.mouse.click(self.button_to_press)
                    self.input_manager.is_synthetic_click = False
                
                self.msleep_while_running(self.interval_ms)
        else:
            if self.button_to_press is None:
                self.status_update.emit("Ошибка: не выбрана клавиша для нажатия.")
                return

            while self._is_running:
                self.keyboard.tap(self.button_to_press)
                self.msleep_while_running(self.interval_ms)