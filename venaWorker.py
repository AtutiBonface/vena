from PyQt6.QtCore import QObject, pyqtSignal
import queue
import json, aiofiles,os
from pathlib import Path
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon
from PyQt6.QtGui import QIcon,QAction
from collections import defaultdict
import asyncio
import aiosqlite

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

class SQLiteProgressTracker:
    def __init__(self, ):
        self.parent_path = Path().home() / '.venaApp' / 'dbs'
        self.db_path = Path(os.path.join(self.parent_path, 'progress.db'))
        

    async def init_db(self):
        try:
            if not  self.db_path.parent.exists():
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            pass
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS segment_progress
                (filename TEXT, segment_id INTEGER, downloaded INTEGER, total INTEGER,
                PRIMARY KEY (filename, segment_id))
            ''')
            await db.commit()

    async def update_segment(self, filename, segment_id, downloaded, total):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO segment_progress
                (filename, segment_id, downloaded, total)
                VALUES (?, ?, ?, ?)
            ''', (filename, segment_id, downloaded, total))
            await db.commit()

    async def get_segment_progress(self, filename, segment_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT downloaded, total FROM segment_progress
                WHERE filename = ? AND segment_id = ?
            ''', (filename, segment_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {'downloaded': row[0], 'total': row[1]}
                return {'downloaded': 0, 'total': 0}

    async def save_all_progress(self):
        # This method is now a no-op as all changes are immediately saved to the database
        pass

    async def init_uuid_table(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS UUID
                (id INTEGER PRIMARY KEY, filename TEXT, uuid TEXT)
            ''')
            await db.commit()
    async def add_filename_plus_uuid(self, filename, uuid):
        await self.init_uuid_table()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO UUID
                (filename, uuid)
                VALUES (?, ?)
            ''', (filename, uuid))
            await db.commit()

    async def get_uuid_for_filename(self, filename):
        await self.init_uuid_table()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT uuid FROM UUID
                WHERE filename = ?
            ''', (filename,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                return None


