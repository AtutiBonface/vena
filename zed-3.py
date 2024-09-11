import os
import json
import asyncio
import aiofiles
from pathlib import Path

class SegmentTracker:
    def __init__(self, filename):
        self.filename = filename
        self.segments = {}
        self.progress_file = Path(f"{Path.home()}/.venaApp/temp/.{os.path.basename(filename)}_progress.json")

    async def load_progress(self):
        if self.progress_file.exists():
            async with aiofiles.open(self.progress_file, 'r') as f:
                self.segments = json.loads(await f.read())

    async def save_progress(self):
        async with aiofiles.open(self.progress_file, 'w') as f:
            await f.write(json.dumps(self.segments))

    def update_segment(self, segment_id, downloaded, total):
        self.segments[segment_id] = {'downloaded': downloaded, 'total': total}

    def get_segment_progress(self, segment_id):
        return self.segments.get(segment_id, {'downloaded': 0, 'total': 0})

class NetworkManager:
    def __init__(self, config, task_manager):
        # ... (existing initialization code) ...
        self.segment_trackers = {}

    async def fetch_segment(self, session, url, start, end, total_segments, filename, segment_id, original_filesize):
        if filename not in self.segment_trackers:
            self.segment_trackers[filename] = SegmentTracker(filename)
            await self.segment_trackers[filename].load_progress()

        segment_tracker = self.segment_trackers[filename]
        segment_progress = segment_tracker.get_segment_progress(segment_id)
        segment_downloaded = segment_progress['downloaded']
        segment_total = end - start + 1 if end else original_filesize - start

        segment_path = Path(f"{Path.home()}/.venaApp/temp/.{os.path.basename(filename)}")
        segment_path.mkdir(parents=True, exist_ok=True)
        segment_filename = segment_path / f'part{segment_id}'

        headers = self.headers.copy()
        headers['Range'] = f'bytes={start + segment_downloaded}-{end}' if end else f'bytes={start + segment_downloaded}-'

        retry_attempts = 0
        max_retries = 5
        
        while retry_attempts < max_retries:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 206:
                        async with aiofiles.open(segment_filename, 'ab') as file:
                            async for chunk in response.content.iter_chunked(self.config.CHUNK_SIZE):
                                if self.task_manager.is_paused:
                                    await segment_tracker.save_progress()
                                    return False  # Indicate that the download was paused

                                await file.write(chunk)
                                chunk_size = len(chunk)
                                segment_downloaded += chunk_size
                                segment_tracker.update_segment(segment_id, segment_downloaded, segment_total)

                                # Update UI progress
                                await self.task_manager.progress_manager._handle_segments_downloads_ui(filename, url, original_filesize)

                        await segment_tracker.save_progress()
                        return True  # Indicate successful download
                    else:
                        retry_attempts += 1
                        await asyncio.sleep(retry_attempts * 2)
            except Exception as e:
                print(f"Error downloading segment {segment_id}: {str(e)}")
                retry_attempts += 1
                await asyncio.sleep(retry_attempts * 2)

        print(f"Failed to download segment {segment_id} after {max_retries} attempts.")
        return False

class TaskManager:
    def __init__(self, parent):
        # ... (existing initialization code) ...
        self.is_paused = False
        self.paused_downloads = {}

    async def pause_downloads_fn(self, filename, size, link, downloaded):
        self.is_paused = True
        self.paused_downloads[filename] = {
            'downloaded': downloaded,
            'size': size,
            'link': link,
            'resume': False
        }
        await self.update_all_active_downloads('Paused')

    async def resume_downloads_fn(self, name, address, downloaded):
        self.is_paused = False
        self.paused_downloads[name] = {
            'downloaded': downloaded,
            'size': '---',
            'link': address,
            'resume': True
        }
        
        for filename, info in self.paused_downloads.items():
            if name == filename:
                await self.addQueue((info['link'], filename, None))
        
        await self.update_all_active_downloads('Resuming..')
        async with self.condition:
            self.condition.notify_all()

    async def start_task(self, file):
        link, filename, path = file
        # ... (existing code) ...

        try:
            # ... (existing code) ...

            if m3u8_extension_in_link:
                # ... (existing m3u8 handling code) ...
                for url, seg_no in zip(segments_urls, range(len(segments_urls))):
                    async with self.segment_semaphore:
                        if not await self.network_manager.fetch_segment(session, url, filename, seg_no, self.headers, size):
                            # If fetch_segment returns False, it means the download was paused
                            return

                await self.file_manager.combine_segments(filename, link, size, len(segments_urls))
                
            else:
                # ... (existing non-m3u8 handling code) ...
                pass

        except Exception as e:
            # ... (existing error handling code) ...
            pass