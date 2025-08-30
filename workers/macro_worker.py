import time, json, random
from pynput import mouse, keyboard
from workers.base_worker import BaseWorker
import pyautogui

class MacroWorker(BaseWorker):
    def __init__(self, mode, events=None, macro_file=None, humanize=False, speed_multiplier=1.0, repeat_count=1):
        super().__init__()
        self.mode = mode
        self.events = events if events is not None else []
        self.macro_file = macro_file
        self.humanize = humanize
        self.speed_multiplier = max(0.1, speed_multiplier)
        self.repeat_count = repeat_count if repeat_count > 0 else float('inf')
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()

    def run(self):
        
        if self.mode == 'record':
            self.status_update.emit("Запись макроса началась... (нажмите hotkey для остановки)")
            self.record_macro()
            self.status_update.emit("Запись макроса завершена.")
        elif self.mode == 'play':
            if self.macro_file:
                try:
                    with open(self.macro_file, 'r') as f:
                        self.events = json.load(f)
                except Exception as e:
                    self.status_update.emit(f"Ошибка загрузки макроса: {e}")
                    return

            if not self.events:
                self.status_update.emit("Нет событий для воспроизведения.")
                return

            self.status_update.emit("Воспроизведение макроса...")
            self.play_macro()
            self.status_update.emit("Воспроизведение завершено.")
        else:
            self.status_update.emit("Режим не выбран (ошибка).")

    def record_macro(self):
        self.events = []
        start_time = time.perf_counter()

        def add_event(event_type, **kwargs):
            self.events.append({'time': time.perf_counter() - start_time, 'type': event_type, **kwargs})

        def on_move(x, y):
            add_event('mouse_move', x=x, y=y)
        def on_click(x, y, button, pressed):
            add_event('mouse_click', button=str(button), pressed=pressed, x=x, y=y)
        def on_scroll(x, y, dx, dy):
            add_event('mouse_scroll', dx=dx, dy=dy)
        def on_press(key):
            add_event('key', key=self.get_key_str(key), pressed=True)
        def on_release(key):
            add_event('key', key=self.get_key_str(key), pressed=False)

        mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)

        mouse_listener.start()
        keyboard_listener.start()

        while self._is_running:
            self.msleep(100)

        mouse_listener.stop()
        keyboard_listener.stop()

    def play_macro(self):
        if not self.events: return
        
        current_repeat = 0
        while self._is_running and current_repeat < self.repeat_count:
            start_time = time.perf_counter()
            last_event_time = 0
            
            for event in self.events:
                if not self._is_running: break

                playback_time = time.perf_counter() - start_time
                event_time = event['time'] / self.speed_multiplier
                
                sleep_duration = event_time - playback_time
                if sleep_duration > 0:
                    self.msleep_while_running(sleep_duration * 1000)

                if not self._is_running: break
                
                self.execute_event(event)
                last_event_time = event_time

            current_repeat += 1
            if self.repeat_count != float('inf') and current_repeat >= self.repeat_count:
                break
    
    def execute_event(self, event):
        etype = event['type']
        if etype == 'mouse_move':
            x, y = event['x'], event['y']
            if self.humanize: x, y = x + random.randint(-2, 2), y + random.randint(-2, 2)
            self.mouse_controller.position = (x, y)
        
        elif etype == 'mouse_click':
            button_str = event['button']
            button = getattr(mouse.Button, button_str.replace('Button.', ''), None)
            if button:
                self.input_manager.is_synthetic_click = True
                if event['pressed']:
                    self.mouse_controller.press(button)
                else:
                    self.mouse_controller.release(button)
                self.input_manager.is_synthetic_click = False
        
        elif etype == 'mouse_scroll':
            self.mouse_controller.scroll(event['dx'], event['dy'])
            
        elif etype == 'key':
            key = self.parse_key_str(event['key'])
            if event['pressed']:
                self.keyboard_controller.press(key)
            else:
                self.keyboard_controller.release(key)

    def get_key_str(self, key):
        if isinstance(key, keyboard.Key): return f'Key.{key.name}'
        if hasattr(key, 'char') and key.char is not None: return key.char
        if hasattr(key, 'vk'): return f'<vk_{key.vk}>'
        return 'unknown_key'

    def parse_key_str(self, key_str):
        if key_str.startswith('Key.'): return keyboard.Key[key_str.replace('Key.', '')]
        if key_str.startswith('<vk_'): return keyboard.KeyCode(int(key_str.strip('<>').split('_')[1]))
        return keyboard.KeyCode.from_char(key_str)