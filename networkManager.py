import os
import asyncio
import aiohttp
import ssl
import certifi
import time
import random
import logging
import aiofiles
import m3u8
from pathlib import Path
from urllib.parse import urljoin, urlparse
from venaUtils import OtherMethods
from venaWorker import SQLiteProgressTracker
from fileManager import FileManager
class NetworkManager:
    def __init__(self, config, task_manager):
        self.config = config
        self.other_methods = OtherMethods()
        self.task_manager = task_manager
        self.segment_trackers = {}

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd, identity;q=1, *;q=0',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'sec-ch-ua-mobile':'?1',
            'sec-ch-ua-platform':"Android",
            'sec-fetch-dest':'empty',
            'sec-fetch-mode':'cors',
            'sec-fetch-site': 'same-origin',
            'DNT': '1', 
            'Cache-Control': 'max-age=0',
        }


        self.logger = logging.getLogger(__name__)
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

    async def create_session(self, connector, headers):       
        return aiohttp.ClientSession(connector=connector, headers=headers, timeout=aiohttp.ClientTimeout(total=60))  # Create an aiohttp session with a custom connector and headers
    
   

   

    async def get_filename_from_m3u8_content(self, session, f_path, url, filename):       
        name, _ = os.path.splitext(filename) # Determine the final filename based on the m3u8 content's MIME type
        async with session.get(url) as response:
            if response.status == 200 and 'Content-Type' in response.headers:
                return self.task_manager.return_filename_with_extension(f_path, name, response.headers.get('Content-Type', ''))
            else:
                return self.task_manager.return_filename_with_extension(f_path, name,  '')
            


    async def download_normal_media(self, session, resp, downloaded_chunk, filename, url, file_path, filesize):
        content_type = resp.headers.get('Content-Type', '')                          
        f_n, ex = os.path.splitext(os.path.basename(filename))
        if not (f_n and ex): 
            new_filename = self.task_manager.return_filename_with_extension(file_path, filename, content_type)
            await self.task_manager.update_changed_filename(filename, new_filename)
            filename = new_filename

        uuid = self.other_methods.generate_uuid() if await self.task_manager.database_progress_tracker.get_uuid_for_filename(filename) is None else await self.task_manager.database_progress_tracker.get_uuid_for_filename(filename)
        await self.task_manager.database_progress_tracker.add_filename_plus_uuid(filename, uuid)
        range_supported = 'Accept-Ranges' in resp.headers      
        if filesize > self.config.SEGMENT_SIZE * 3 and range_supported:
            num_segments = (filesize + self.config.SEGMENT_SIZE - 1) // self.config.SEGMENT_SIZE

            other_file_type_tasks = []
            for seg_no in range(num_segments):
                start = seg_no * self.config.SEGMENT_SIZE
                end = start + self.config.SEGMENT_SIZE - 1 if seg_no < num_segments - 1 else filesize - 1
                segment_size = end - start + 1
                async with self.task_manager.segment_semaphore:   
                    task = asyncio.create_task(self.download_and_throw_pause_resume_events_for_normal_media(
                        session, self.headers, filename, url, file_path, start, end, seg_no, 
                        segment_size, filesize, uuid))
                    other_file_type_tasks.append(task)

            try:
                await asyncio.gather(*other_file_type_tasks)                                       
                await self.task_manager.file_manager.combine_segments(filename, url, filesize, num_segments, uuid)

                async with self.task_manager.file_locks[filename]:
                    if filename in self.task_manager.size_downloaded_dict:
                        del self.task_manager.size_downloaded_dict[filename] 
            except Exception as e:
                print(f'Normal media error is {e}')
        else:
            await self.task_manager.file_manager._handle_download(resp, filename, url, downloaded_chunk)
                        

    async def download_m3u8_media(self, session, resp, filename, m3u8_url, file_path, total_size):
        segments_urls = []
        m3u8_tasks = []
        url_parsed = urlparse(m3u8_url)
        base_url = f"{url_parsed.scheme}://{url_parsed.netloc}{url_parsed.path.rsplit('/', 1)[0]}/"
        content = await resp.text()
       
        playlist = m3u8.loads(content)
        if not playlist.is_variant:                               
            for segment in playlist.segments:
                segment_url = urljoin(base_url, segment.uri)                                   
                segments_urls.append(segment_url)

            segments_urls = list(dict.fromkeys(segments_urls))
    
            new_filename = await self.get_filename_from_m3u8_content(session, file_path, segments_urls[0], filename)
            await self.task_manager.update_changed_filename(filename, new_filename)
            filename = new_filename
            uuid = self.other_methods.generate_uuid() if await self.task_manager.database_progress_tracker.get_uuid_for_filename(filename) is None else await self.task_manager.database_progress_tracker.get_uuid_for_filename(filename)
            await self.task_manager.database_progress_tracker.add_filename_plus_uuid(filename, uuid)

            num_segments = len(segments_urls)
            segment_size = total_size // num_segments

            for seg_no, seg_url in enumerate(segments_urls):
                async with self.task_manager.segment_semaphore:                                        
                    task = asyncio.create_task(self.download_and_throw_pause_resume_events_for_m3u8(session,self.headers, filename, seg_url, file_path,segment_size, total_size, seg_no,  uuid))
                    m3u8_tasks.append(task)                    
            try:
               
                await asyncio.gather(*m3u8_tasks)
                await self.task_manager.file_manager.combine_segments(filename, m3u8_url, total_size, len(segments_urls), uuid)
                async with self.task_manager.file_locks[filename]:
                    if filename in self.task_manager.size_downloaded_dict:
                        del self.task_manager.size_downloaded_dict[filename]
            except Exception as e:
                print(e)


        elif playlist.is_variant:
          
            highest_resolution_stream = max(playlist.playlists, key=lambda p: p.stream_info.resolution[0] if p.stream_info.resolution else 0)        
            highest_res_m3u8_url = urljoin(base_url, highest_resolution_stream.uri)

            ## this is for recursin azin it calls the function again
            async with session.get(highest_res_m3u8_url) as high_res_resp:
                await self.download_m3u8_media(session, high_res_resp, filename, highest_res_m3u8_url, file_path, total_size)


    async def _download_m3u8_media_segment(self, session,headers, filename, segment_url, segment_path, segment_size, total_size, segment_id, uuid):
        
        retry_attempts = 0
        max_retries = 5
        success = False
        segment_downloaded = 0
        self.paused = False       
        self.segment_track_instance = SQLiteProgressTracker() 
        await self.segment_track_instance.init_db()
        segment_path = Path(f"{Path().home()}/.venaApp/temp/{uuid}")
        segment_path.mkdir(parents=True, exist_ok=True)
        segment_filename = segment_path / f'part{segment_id}' 
        segment_progress = await self.segment_track_instance.get_segment_progress(filename, segment_id)

        if segment_filename.exists():
            segment_downloaded = segment_progress['downloaded']    
        
        while retry_attempts < max_retries and not success:
            try:                                 
                headers['Referer'] = self.other_methods.get_base_url(segment_url)                
                
                if segment_downloaded > 0:
                    headers['Range'] = f'bytes={segment_downloaded}-'
                
                else:
                    headers.pop('Range', None)
                async with session.get(segment_url, headers=headers) as response:
                    if response.status in (206, 200):
                        async with aiofiles.open(segment_filename, 'ab') as file:
                            async for chunk in response.content.iter_chunked(self.config.CHUNK_SIZE):    
                                pause_event = self.task_manager._get_or_create_pause_event(filename)
                                if not pause_event.is_set():                                    
                                    self.paused = True
                                    raise                                   
                                await file.write(chunk)
                                chunk_size = len(chunk)
                                segment_downloaded += chunk_size                            
                                await self.segment_track_instance.update_segment(filename, segment_id, segment_downloaded, segment_size)

                                async with self.task_manager.file_locks[segment_filename]:
                                    if filename in self.task_manager.size_downloaded_dict:
                                        self.task_manager.size_downloaded_dict[filename][0] += len(chunk)
                                    else:
                                        self.task_manager.size_downloaded_dict[filename] = [len(chunk), time.time()]
                                await self.task_manager.progress_manager._handle_segments_downloads_ui(filename, segment_url, total_size)
                       
                        success = True
                        return True
                    else:
                        retry_attempts += 1
                        await asyncio.sleep(retry_attempts * 2 + random.uniform(0.5, 1.5))

            except Exception as e:
                print(e)

    async def _download_normal_media_segment(self, session, headers,filename, address, segment_path,  segment_start, segment_end, seg_no, segment_size, file_size, uuid):
        retry_attempts = 0
        max_retries = 5
        success = False
        segment_downloaded = 0
        self.paused = False       
        self.segment_track_instance = SQLiteProgressTracker() 
        await self.segment_track_instance.init_db()
        segment_path = Path(f"{Path().home()}/.venaApp/temp/{uuid}")
        segment_path.mkdir(parents=True, exist_ok=True)
        segment_filename = segment_path / f'part{seg_no}' 
        segment_progress = await self.segment_track_instance.get_segment_progress(filename, seg_no)
        if segment_filename.exists():
            segment_downloaded = segment_progress['downloaded']    

        while retry_attempts < max_retries and not success:
            try:                                 
                headers['Referer'] = self.other_methods.get_base_url(address)                
                if segment_start is not None and segment_end is not None:
                    if segment_downloaded > 0:
                        segment_start = segment_start + segment_downloaded
                    if segment_start < segment_end:
                        headers['Range'] = f'bytes={segment_start}-{segment_end}'
                    else:
                        return True
                elif segment_start is None and segment_end is None:
                    if segment_downloaded > 0:
                        headers['Range'] = f'bytes={segment_downloaded}-'
                    else:
                        headers.pop('Range', None)
               
                async with session.get(address, headers=headers) as response:
                    if response.status in (206, 200):
                        async with aiofiles.open(segment_filename, 'ab') as file:
                            async for chunk in response.content.iter_chunked(self.config.CHUNK_SIZE):  
                                pause_event = self.task_manager._get_or_create_pause_event(filename)
                                if not pause_event.is_set():                                    
                                    self.paused = True
                                    raise                    
                                await file.write(chunk)
                                chunk_size = len(chunk)
                                segment_downloaded += chunk_size                            
                                await self.segment_track_instance.update_segment(filename, seg_no, segment_downloaded, segment_size)

                                async with self.task_manager.file_locks[segment_filename]:
                                    if filename in self.task_manager.size_downloaded_dict:
                                        self.task_manager.size_downloaded_dict[filename][0] += len(chunk)
                                    else:
                                        self.task_manager.size_downloaded_dict[filename] = [len(chunk), time.time()]
                                await self.task_manager.progress_manager._handle_segments_downloads_ui(filename, address, file_size)
                       
                        success = True
                        return True
                    else:
                        retry_attempts += 1
                        await asyncio.sleep(retry_attempts * 2 + random.uniform(0.5, 1.5))

            except Exception as e:
                print(f'M3U8 files error is ', e)


    async def download_and_throw_pause_resume_events_for_m3u8(self, session,headers, filename, segment_url, segment_path, segment_size, total_size, segment_id, uuid):
        pause_event = self.task_manager._get_or_create_pause_event(filename)
        while not pause_event.is_set():
            try:
                await asyncio.wait_for(pause_event.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                # Check if we're still paused
                if not pause_event.is_set():
                    return  # Exit if still paused

        return await self._download_m3u8_media_segment(session,headers, filename, segment_url, segment_path, segment_size, total_size, segment_id, uuid)


    async def download_and_throw_pause_resume_events_for_normal_media(self, session, headers,filename, address, segment_path,  segment_start, segment_end, seg_no, segment_size, file_size, uuid):
        pause_event = self.task_manager._get_or_create_pause_event(filename)
        while not pause_event.is_set():
            try:
                await asyncio.wait_for(pause_event.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                # Check if we're still paused
                if not pause_event.is_set():
                    return  # Exit if still paused

        return await self._download_normal_media_segment(session, headers,filename, address, segment_path,  segment_start, segment_end, seg_no, segment_size, file_size, uuid)


