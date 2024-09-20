from PyQt6.QtCore import QObject, pyqtSignal
import queue
import json, aiofiles,os
from pathlib import Path
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon
from PyQt6.QtGui import QIcon,QAction
from collections import defaultdict
import asyncio
class Worker(QObject):
    update_signal = pyqtSignal(str, str, str, str,str, str, str)

    def __init__(self, update_queue):
        super().__init__()
        self.update_queue = update_queue

    def start_working(self):
        while True:
            try:
                filename, status, size, downloaded, speed, percentage, date = self.update_queue.get(timeout=0.1)
                speed = str(speed)
                self.update_signal.emit(filename, status, size, downloaded,speed, percentage, date)
            except queue.Empty:
                continue


class SegmentTracker:
    def __init__(self, filename):
        self.filename = filename
        self.segment_lock = defaultdict(asyncio.Lock)
        self.segments = {}
        self.progress_file = Path(f"{Path.home()}/.venaApp/temp/.{os.path.basename(filename)}/progress.json")

    async def load_progress(self):
        async with self.segment_lock[self.progress_file]:  # Lock while loading
            if self.progress_file.exists():
                async with aiofiles.open(self.progress_file, 'r') as f:
                    try:
                        self.segments = json.loads(await f.read())
                        self.segments = {str(k): v for k, v in self.segments.items()}
                    except json.JSONDecodeError:
                        print('There is an error with json in segment worker')
                        self.segments = {}  # Reset if there's a loading error
            else:
                self.segments = {}
                await self.save_progress()

    async def save_progress(self):
        async with self.segment_lock[self.progress_file]:
            segments_with_str_keys = {str(k): v for k, v in self.segments.items()}
            async with aiofiles.open(self.progress_file, 'w') as f:
                await f.write(json.dumps(segments_with_str_keys))


    def update_segment(self, segment_id, downloaded, total):  
        segment_id = str(segment_id)
        
        self.segments[segment_id] = {'downloaded': downloaded, 'total': total}
          
        

    def get_segment_progress(self, segment_id):
        segment_id = str(segment_id)
        return self.segments.get(segment_id, {'downloaded': 0, 'total': 0})


class SetAppTray():
    def __init__(self, app) -> None:
        
        self.tray_icon = QSystemTrayIcon(QIcon("images/main.ico"), app)
        self.tray_icon_menu = QMenu()        
        # Create actions for the tray icon menu
        self.restore_action = QAction("Restore")
        self.restore_action.triggered.connect(app.restore_window)
        self.quit_action = QAction("Quit")
        self.quit_action.triggered.connect(app.quit_application)

        self.tray_icon.activated.connect(app.on_tray_icon_activated)
        
        self.tray_icon_menu.addAction(self.restore_action)
        self.tray_icon_menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(self.tray_icon_menu)
        