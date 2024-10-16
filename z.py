import asyncio
from collections import defaultdict

class TaskManager:
    def __init__(self, parent):
        # ... (other initializations)
        self.active_tasks = defaultdict(set)
        self.download_state = {}

    async def start_task(self, file):
        link, filename, path, cookies = file
        # ... (existing code)

        try:
            if size > self.config.SEGMENT_SIZE * 3 and range_supported:
                num_segments = (size + self.config.SEGMENT_SIZE - 1) // self.config.SEGMENT_SIZE
                tasks = []

                for seg_no in range(num_segments):
                    start = seg_no * self.config.SEGMENT_SIZE
                    end = start + self.config.SEGMENT_SIZE - 1 if seg_no < num_segments - 1 else size - 1
                    segment_size = end - start + 1

                    async with self.segment_semaphore:
                        task = asyncio.create_task(self.download_segment(session, filename, link, self.headers, start, end, seg_no, segment_size, size, uuid))
                        self.active_tasks[filename].add(task)
                        tasks.append(task)

                try:
                    await asyncio.gather(*tasks)
                    await self.file_manager.combine_segments(filename, link, size, num_segments, uuid)
                except DownloadPausedError:
                    # Store the current state for resuming later
                    self.download_state[filename] = {
                        'size': size,
                        'num_segments': num_segments,
                        'completed_segments': [task.result() for task in tasks if task.done() and not task.exception()],
                        'uuid': uuid
                    }
                    raise
                finally:
                    # Clean up tasks
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    self.active_tasks[filename].clear()

            else:
                # Handle small downloads
                await self.file_manager._handle_download(resp, filename, link, downloaded_chunk)

        except DownloadPausedError:
            # Handle pausing
            await self.handle_pause(filename, link, size, downloaded_chunk)
        
        # ... (error handling)

    async def pause_downloads_fn(self, filename, size, link, downloaded):
        pause_event = self._get_or_create_pause_event(filename)
        pause_event.clear()  # Set the pause flag for this file

        # Cancel all active tasks for this file
        for task in self.active_tasks[filename]:
            if not task.done():
                task.cancel()
        
        await asyncio.gather(*self.active_tasks[filename], return_exceptions=True)
        self.active_tasks[filename].clear()

        self.paused_downloads[filename] = {
            'downloaded': downloaded,
            'size': size,
            'link': link,
            'resume': False
        }
        
        await self.update_all_active_downloads('Paused.', filename)

    async def resume_downloads_fn(self, name, address, downloaded, cookies=None):
        pause_event = self._get_or_create_pause_event(name)
        pause_event.set()  # Clear the pause flag for this file

        state = self.download_state.get(name, {})
        size = state.get('size', downloaded)  # Use the stored size if available

        self.paused_downloads[name] = {
            'downloaded': downloaded,
            'size': size,
            'link': address,
            'resume': True
        }

        # Restore the download state and resume from where we left off
        if state:
            await self.resume_segmented_download(name, state, cookies)
        else:
            await self.addQueue((address, name, None, cookies))

        async with self.file_locks[name]:
            self.size_downloaded_dict[name] = [downloaded, time.time()]

        await self.update_all_active_downloads('Resuming..', name)

        async with self.condition:
            self.condition.notify_all()

    async def resume_segmented_download(self, filename, state, cookies):
        link = self.paused_downloads[filename]['link']
        size = state['size']
        num_segments = state['num_segments']
        completed_segments = state['completed_segments']
        uuid = state['uuid']

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=None, limit_per_host=10)
        async with await self.network_manager.create_session(connector, self.headers) as session:
            tasks = []
            for seg_no in range(num_segments):
                if seg_no not in completed_segments:
                    start = seg_no * self.config.SEGMENT_SIZE
                    end = start + self.config.SEGMENT_SIZE - 1 if seg_no < num_segments - 1 else size - 1
                    segment_size = end - start + 1

                    async with self.segment_semaphore:
                        task = asyncio.create_task(self.download_segment(session, filename, link, self.headers, start, end, seg_no, segment_size, size, uuid))
                        self.active_tasks[filename].add(task)
                        tasks.append(task)

            try:
                await asyncio.gather(*tasks)
                await self.file_manager.combine_segments(filename, link, size, num_segments, uuid)
            except Exception as e:
                print(f"Error resuming download for {filename}: {str(e)}")
            finally:
                # Clean up tasks
                for task in tasks:
                    if not task.done():
                        task.cancel()
                self.active_tasks[filename].clear()

        # Clear the download state after successful resume
        del self.download_state[filename]

    async def handle_pause(self, filename, link, size, downloaded):
        # Update the paused downloads information
        self.paused_downloads[filename] = {
            'downloaded': downloaded,
            'size': size,
            'link': link,
            'resume': False
        }
        
        # Update the UI and storage
        await self.update_all_active_downloads('Paused.', filename)

        # Clean up any remaining tasks
        for task in self.active_tasks[filename]:
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.active_tasks[filename], return_exceptions=True)
        self.active_tasks[filename].clear()