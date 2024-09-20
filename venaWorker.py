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
        self.segment_lock = asyncio.Lock()
        self.segments = {}
        self.progress_file = Path(f"{Path.home()}/.venaApp/temp/.{os.path.basename(filename)}/progress.json")

    async def load_progress(self):
        async with self.segment_lock:
            if self.progress_file.exists():
                try:
                    async with aiofiles.open(self.progress_file, 'r') as f:
                        content = await f.read()
                        self.segments = json.loads(content)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading progress file: {e}")
                    self.segments = {}
            else:
                self.segments = {}
                await self.save_progress()

    async def save_progress(self):
            try:
                self.progress_file.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(self.progress_file, 'w') as f:
                    await f.write(json.dumps(self.segments, indent=2))
            except IOError as e:
                print(f"Error saving progress file: {e}")

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
        