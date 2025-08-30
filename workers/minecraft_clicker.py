import time
import random
from pynput.mouse import Button, Controller as MouseController
import pyautogui
from workers.base_worker import BaseWorker

class MinecraftClicker(BaseWorker):
    def __init__(self, interval_ms, humanize, button_str):
        super().__init__()
        self.interval_sec = max(0.001, interval_ms / 1000.0)
        self.humanize = humanize
        self.mouse = MouseController()
        self.button = Button.left if button_str.lower() == 'лкм' else Button.right
        
    def run(self):
        self.status_update.emit("Minecraft кликер запущен...")
        

        pyautogui.PAUSE = 0
        
        next_click_time = time.perf_counter()

        while self._is_running:
            self.input_manager.is_synthetic_click = True
            self.mouse.press(self.button)
            self.mouse.release(self.button)
            self.input_manager.is_synthetic_click = False

            delay_sec = self.interval_sec
            if self.humanize:
                delay_variance = self.interval_sec * 0.25
                delay_sec = random.uniform(
                    self.interval_sec - delay_variance,
                    self.interval_sec + delay_variance
                )
                
                if random.random() < 0.6:
                    pyautogui.move(random.randint(-2, 2), random.randint(-2, 2))

            next_click_time += delay_sec
            
            sleep_duration = next_click_time - time.perf_counter()
            
            if sleep_duration > 0:
                self.sleep_sec_while_running(sleep_duration)