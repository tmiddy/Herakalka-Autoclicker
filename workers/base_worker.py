from PyQt6.QtCore import QThread, pyqtSignal
import time
from utils.input_manager import InputManager

class BaseWorker(QThread):
    status_update = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._is_running = True
        self.input_manager = InputManager()

    def run(self):
        pass

    def stop(self):
        self.status_update.emit("Остановка...")
        self._is_running = False

    def msleep_while_running(self, ms):
        end_time = time.perf_counter() + ms / 1000.0
        while self._is_running and time.perf_counter() < end_time:
            time.sleep(0.001)

    def sleep_sec_while_running(self, sec):
        if sec <= 0:
            return
        end_time = time.perf_counter() + sec
        

        while self._is_running and time.perf_counter() < end_time:
            
            time.sleep(0.001)