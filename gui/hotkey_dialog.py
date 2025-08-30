from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QKeySequence

class HotkeyDialog(QDialog):
    hotkey_set = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Назначить горячую клавишу")
        self.setFixedSize(300, 150)
        self.layout = QVBoxLayout(self)

        self.info_label = QLabel("Нажмите комбинацию клавиш или кнопку мыши...")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.info_label)

        self.current_hotkey_label = QLabel("")
        self.current_hotkey_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_hotkey_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #88c0d0;")
        self.layout.addWidget(self.current_hotkey_label)

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.accept)
        self.layout.addWidget(self.save_button)

        self.pressed_keys_str = set()
        self.hotkey_str = ""
        self.is_mouse_hotkey = False

    def keyPressEvent(self, event: QKeyEvent):
        if event.isAutoRepeat():
            return
        
        if self.is_mouse_hotkey:
            self.pressed_keys_str.clear()
            self.is_mouse_hotkey = False

        key_name = self.get_key_name(event)
        if key_name:
            self.pressed_keys_str.add(key_name)
        
        self.update_keyboard_label()

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.isAutoRepeat():
            return
        pass

    def mousePressEvent(self, event: QMouseEvent):
        self.pressed_keys_str.clear()
        self.is_mouse_hotkey = True
        
        button_map = {
            Qt.MouseButton.LeftButton: ("mouse.left", "ЛКМ"),
            Qt.MouseButton.RightButton: ("mouse.right", "ПКМ"),
            Qt.MouseButton.MiddleButton: ("mouse.middle", "СКМ"),
            Qt.MouseButton.XButton1: ("mouse.x1", "Mouse 4"),
            Qt.MouseButton.XButton2: ("mouse.x2", "Mouse 5"),
        }
        button = event.button()
        if button in button_map:
            self.hotkey_str, display_name = button_map[button]
            self.current_hotkey_label.setText(display_name)

    def get_key_name(self, event: QKeyEvent):
        key = event.key()
        
        key_map = {
            Qt.Key.Key_Control: "Key.ctrl", Qt.Key.Key_Shift: "Key.shift",
            Qt.Key.Key_Alt: "Key.alt", Qt.Key.Key_Meta: "Key.cmd",
            Qt.Key.Key_F1: "Key.f1", Qt.Key.Key_F2: "Key.f2", Qt.Key.Key_F3: "Key.f3",
            Qt.Key.Key_F4: "Key.f4", Qt.Key.Key_F5: "Key.f5", Qt.Key.Key_F6: "Key.f6",
            Qt.Key.Key_F7: "Key.f7", Qt.Key.Key_F8: "Key.f8", Qt.Key.Key_F9: "Key.f9",
            Qt.Key.Key_F10: "Key.f10", Qt.Key.Key_F11: "Key.f11", Qt.Key.Key_F12: "Key.f12",
        }
        if key in key_map:
            return key_map[key]

        # Для всех остальных клавиш (буквы, цифры, символы)
        # используем QKeySequence.toString(), чтобы получить символ ('C', 'Ф', '5')

        text = QKeySequence(key).toString().lower()
        if text:
            return text
            
        return None

    def update_keyboard_label(self):
        if not self.pressed_keys_str:
            return
        

        sorted_keys = sorted(list(self.pressed_keys_str), key=lambda x: "Key." in x, reverse=True)
        

        self.hotkey_str = "+".join(sorted_keys)
        

        display_parts = [k.replace("Key.", "").upper() for k in sorted_keys]
        self.current_hotkey_label.setText(" + ".join(display_parts))

    def accept(self):
        if self.hotkey_str:
            self.hotkey_set.emit(self.hotkey_str)
        super().accept()