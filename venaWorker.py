from PyQt6.QtCore import QObject, QThread, pyqtSignal
import queue
import json, aiofiles,os
from pathlib import Path

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
        self.segments = {}
        self.progress_file = Path(f"{Path.home()}/.venaApp/temp/.{os.path.basename(filename)}/progress.json")

    async def load_progress(self):
        if self.progress_file.exists():
            async with aiofiles.open(self.progress_file, 'r') as f:
                self.segments = json.loads(await f.read())

        else:
            # Initialize the file with an empty JSON object if it does not exist
            self.segments = {}
            await self.save_progress()

    async def save_progress(self):
        async with aiofiles.open(self.progress_file, 'w') as f:
            await f.write(json.dumps(self.segments))

    def update_segment(self, segment_id, downloaded, total):
        self.segments[segment_id] = {'downloaded': downloaded, 'total': total}

    def get_segment_progress(self, segment_id):
        return self.segments.get(segment_id, {'downloaded': 0, 'total': 0})
