import os, asyncio,aiohttp, ssl, certifi, time, threading, re
from asyncio import Queue 
from settings import AppSettings
import aiofiles, storage
from pathlib import Path
import shutil, m3u8
from venaUtils import OtherMethods
from urllib.parse import urlparse, urlunparse, urljoin

class FileManager:
    def __init__(self, config, task_manager):
        self.config = config
        self.task_manager = task_manager

    def validate_filename(self, filename, selected_path):
       
        path = AppSettings().default_download_path
        ## the path stored in config file
        if selected_path:
            path = selected_path
        try:
            os.makedirs(path, exist_ok=True)## making directory if it does exist
        except Exception as e:
            pass
        file_path = os.path.join(path, filename)
        index = 1
        name, extension = os.path.splitext(filename)
        name_with_no_path = f'{name}{extension}'
        new_name = file_path

        while True:

            if os.path.exists(new_name):
            
                new_name = os.path.join(path, f'{name}_{index}{extension}')
                index += 1
                continue

            if storage.check_filename_existance(new_name):
                new_name = os.path.join(path, f'{name}_{index}{extension}')
                index += 1               

                continue
            break


        return new_name
        # Implementation of validate_filename method

    async def combine_segments(self, filename, link, size, num_segments, uuid):      
       
        tem_folder = f"{Path().home()}/.venaApp/temp/{uuid}"

        try:        
            async with aiofiles.open(filename, 'wb') as final_file:
                for i in range(num_segments):
                    segment_filename = f'{tem_folder}/part{i}'
                    async with aiofiles.open(segment_filename, 'rb') as segment_file:
                        while True:
                            chunk = await segment_file.read(self.config.CHUNK_SIZE)
                            if not chunk:
                                break
                            await final_file.write(chunk)
                   
            shutil.rmtree(tem_folder)
            
            await self.task_manager.progress_manager.update_file_details_on_storage_during_download(
                filename, link, size, size, 'Finished.', 0,'', time.strftime('%Y-%m-%d %H:%M'))
        except Exception as e:
            
            downloaded = self.task_manager.size_downloaded_dict[filename][0]
            await self.task_manager.progress_manager.update_file_details_on_storage_during_download(
                filename, link, size, downloaded, 'Failed!', 0,'', time.strftime('%Y-%m-%d %H:%M'))



    async def _handle_download(self, resp,filename, link, initial_chuck=0):
       
        downloaded_chunk = initial_chuck

        size = int(resp.headers.get('Content-Length', 0)) + initial_chuck
        mode = 'ab' if initial_chuck > 0 else 'wb'

    
        async with aiofiles.open(filename, mode) as f:
            start_time = time.time()
            speed = 0
            async for chunk in resp.content.iter_chunked(self.config.CHUNK_SIZE):
                if filename in self.task_manager.paused_downloads and self.task_manager.paused_downloads[filename]['resume'] == False:
                    self.task_manager.paused_downloads[filename] = {
                        'downloaded': downloaded_chunk,
                        'size': size,
                        'link': link
                    }
                    await self.task_manager.progress_manager.update_file_details_on_storage_during_download(
                        filename, link, size, downloaded_chunk, 'Paused.',speed,'', time.strftime('%Y-%m-%d %H:%M')
                    )
        
                    return
                await f.write(chunk)
                downloaded_chunk += len(chunk)
                await self.task_manager.progress_manager._update_progress(filename, link, size, downloaded_chunk, start_time)

            if filename in self.task_manager.paused_downloads:
                del self.task_manager.paused_downloads[filename]

            await self.task_manager.progress_manager.update_file_details_on_storage_during_download(
                filename, link, size, size, 'Finished.',speed,'', time.strftime('%Y-%m-%d %H:%M')
                
            )
        