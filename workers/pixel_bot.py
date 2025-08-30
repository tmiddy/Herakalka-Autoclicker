import pyautogui
from workers.base_worker import BaseWorker
from pynput.mouse import Button, Controller as MouseController
import numpy as np

class PixelBot(BaseWorker):
    def __init__(self, search_area, target_color, click_target, interval_ms):
        super().__init__()
        self.search_area = search_area
        self.target_color = np.array(target_color) # (r, g, b)
        self.click_target = click_target
        self.interval_ms = interval_ms
        self.mouse = MouseController()

    def run(self):
        self.status_update.emit("Пиксельный бот запущен...")
        while self._is_running:
            try:
                screenshot = pyautogui.screenshot(region=self.search_area)
                img_np = np.array(screenshot)
                

                matches = np.where(np.all(np.abs(img_np[:, :, :3] - self.target_color) <= 10, axis=2))
                
                if matches[0].size > 0:
                    y, x = matches[0][0], matches[1][0]
                    
                    if self.click_target == 'pixel':
                        click_x = self.search_area[0] + x
                        click_y = self.search_area[1] + y
                        pyautogui.moveTo(click_x, click_y, duration=0.1)
                    
                    self.input_manager.is_synthetic_click = True
                    self.mouse.click(Button.left)
                    self.input_manager.is_synthetic_click = False

                
            except Exception as e:
                self.status_update.emit(f"Ошибка в пиксельном боте: {e}")
                self.stop()
            
            self.msleep_while_running(self.interval_ms)