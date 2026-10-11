from pynput import keyboard
from PySide6.QtCore import QObject, Signal


class KeyboardControls(QObject):
    play_pause_requested = Signal()
    next_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()

    def _on_press(self, key):
        if key == keyboard.Key.media_play_pause:
            self.play_pause_requested.emit()
        elif key == keyboard.Key.media_next:
            self.next_requested.emit()

    def stop(self):
        self._listener.stop()
