from PyQt6.QtCore import QObject, QThread, pyqtSignal
import queue

class Worker(QObject):
    update_signal = pyqtSignal(str, str, str, str, str)

    def __init__(self, update_queue):
        super().__init__()
        self.update_queue = update_queue

    def start_working(self):
        while True:
            try:
                filename, status, size, downloaded, date = self.update_queue.get(timeout=0.1)
                self.update_signal.emit(filename, status, size, downloaded, date)
            except queue.Empty:
                continue
