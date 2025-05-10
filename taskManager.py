import os, asyncio,aiohttp, ssl, certifi, time
from asyncio import Queue

from websockets import ConnectionClosedOK 
import  storage
import  m3u8
from venaUtils import OtherMethods
from urllib.parse import urlparse, urlunparse, urljoin
from fileManager import FileManager
from progressManager import ProgressManager
from collections import defaultdict
from networkManager import NetworkManager

from venaWorker import SQLiteProgressTracker

class Config:
    CHUNK_SIZE = 256 * 1024  # 256 kb
    SEGMENT_SIZE = 10 * 1024 * 1024  # 10 MB segments
    PROGRESS_UPDATE_INTERVAL = 1024 * 1024
    MAX_CONCURRENT_DOWNLOADS = 5
    RETRY_ATTEMPTS = 3
    CONCURRENCY_DELAY = 0.1
    MAX_CONCURRENT_SEGMENTS = 4

class TaskManager(): 
    def __init__(self, parent) -> None:
            # Initialize configuration settings
            self.config = Config()
            self.database_progress_tracker = SQLiteProgressTracker()            
            self.network_manager = NetworkManager(self.config, self)
            self.file_manager = FileManager(self.config, self)
            self.progress_manager = ProgressManager(self, parent)
            self.headers = self.network_manager.headers
            self.file_locks = defaultdict(asyncio.Lock)
            self.lock = asyncio.Lock()  
            self.size_downloaded_dict = {}  
            self.other_methods = OtherMethods()              
            self.name = ''
            self.links_and_filenames = Queue() # Queue for managing download tasks
            self.ui_files = []
            self.parent = parent
            self.file_semaphore = asyncio.Semaphore(self.config.MAX_CONCURRENT_DOWNLOADS)
            self.segment_semaphore = asyncio.Semaphore(self.config.MAX_CONCURRENT_SEGMENTS)
            self.ui_callback = parent
            self.condition = asyncio.Condition() # Condition to notify when the queue is not empty
            self.number_of_tasks = 0 #asyncio.all_tasks() #if task is not asyncio.current_task()
           
            self.paused_downloads = {} # Dictionary to keep track of paused downloads
            self.pause_events = defaultdict(asyncio.Event)
            self.paused_downloads = {}
            self.is_downloading = False
    async def append_file_details_to_storage(self, filename, path, address, cookies, date):
     
        # Append file details to storage
        if not path:
            path = str(self.parent.app_config.default_download_path)
            
        await asyncio.to_thread(self.parent.add_download_to_list ,filename, address, path, date, cookies)
        await asyncio.to_thread(storage.add_data,filename,address, '---', '---', 'Waiting...', date, path, cookies)

     
    def return_filename_with_extension(self, path, filename, content_type):
        content_type = content_type.lower()
        extension = self.other_methods.content_type_to_extension.get(content_type, '')
        new_filename = f'{filename}{extension}'
        new_filename = self.file_manager.validate_filename(new_filename, path)
        return new_filename
    

    async def update_changed_filename(self, old_f_name, new_f_name):
        await asyncio.to_thread(self.parent.update_filename,old_f_name, new_f_name )
        await asyncio.to_thread(storage.update_filename, old_f_name, new_f_name)


    async def addQueue(self, file):  
        # Add a file to the download queue     
        self.links_and_filenames.put_nowait(file)        # adds to queue,              
        async with self.condition:
            self.condition.notify_all()
        return
        # sends a notification that a queue was added        
    ## this adds index to file name if file exists
    
    async def download_tasks(self):
        self.is_downloading = True
        while True:
            async with self.condition:
                await self.condition.wait()           
            while not self.links_and_filenames.empty():
                file = await self.links_and_filenames.get()
                link, filename, path, cookies, filesize = file  # Unpack filesize
                if not filename in self.paused_downloads:
                    filename = self.file_manager.validate_filename(filename, path)
                    name_with_no_path = os.path.basename(filename)
                    await self.append_file_details_to_storage(name_with_no_path, path, link, cookies, time.strftime('%Y-%m-%d %H:%M')) 
                file = (link, filename, path, cookies, filesize)  # Include filesize                
                async with self.file_semaphore:
                    asyncio.create_task(self.start_task(file))
                self.links_and_filenames.task_done()
            if self.links_and_filenames.empty():
                self.is_downloading = False


    async def start_task(self, file): 
        link, filename, path, cookies, filesize = file  # Unpack filesize
        if cookies is not None:
            self.headers = self.headers.copy()
            self.headers['Cookie'] = cookies
            self.headers['Referer'] = link
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=None, limit_per_host=10)
        created_session = await self.network_manager.create_session(connector, self.headers)
        async with created_session as session:        
            downloaded_chunk = self.paused_downloads.get(filename, {}).get('downloaded', 0)            
            speed = 0            
            try:                
                async with session.get(link, headers=self.headers) as resp:                   
                    if resp.status in (200, 206):                     
                        # Check if link is m3u8
                        is_m3u8_link = self.other_methods.get_m3u8_in_link(link)                       
                        _, ext = os.path.splitext(filename)
                        
                        if is_m3u8_link and not  ext.lower() == '.m3u8': # this is weird but it works ni juu nishaa validate kwa add link na nikaasign extension if .m3u8 exists still in the filename so the file is corrupted or has no media files
                            await self.network_manager.download_m3u8_media(session, resp, filename, link, path, filesize)
                        else:
                            await self.network_manager.download_normal_media(session, resp, downloaded_chunk, filename, link, path, filesize)
                    else:
                        error_message = f"failed! : Unexpected status {resp.status}"
                        await self.progress_manager.update_file_details_on_storage_during_download(
                            filename, link, filesize, downloaded_chunk, error_message, speed, '---', time.strftime('%Y-%m-%d %H:%M'))
                        
            
            except aiohttp.ClientError as e: 
                error_message = f"failed! : ClientError - {str(e)}"
                print(error_message)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, filesize, downloaded_chunk, error_message, speed, '---', time.strftime('%Y-%m-%d %H:%M')
                )
            except asyncio.TimeoutError as e:
                error_message = f"failed! : TimeoutError - {str(e)}"
                print(error_message)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, filesize, downloaded_chunk, error_message, speed, '---', time.strftime('%Y-%m-%d %H:%M')
                )
            except ssl.SSLError as e:
                error_message = f"failed! : SSLError - {str(e)}"
                print(error_message)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, filesize, downloaded_chunk, error_message, speed, '---', time.strftime('%Y-%m-%d %H:%M')
                )
            except OSError as e:
                error_message = f"failed! : OSError - {str(e)}"
                print(error_message)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, filesize, downloaded_chunk, error_message, speed, '---', time.strftime('%Y-%m-%d %H:%M')
                )
            except ValueError as e:
                error_message = f"failed! : ValueError - {str(e)}"
                print(error_message)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, filesize, downloaded_chunk, error_message, speed, '---', time.strftime('%Y-%m-%d %H:%M')
                )
            except RuntimeError as e:
                error_message = f"failed! : RuntimeError - {str(e)}"
                print(error_message)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, filesize, downloaded_chunk, error_message, speed, '---', time.strftime('%Y-%m-%d %H:%M')
                )
            except Exception as e:
                error_message = f"failed! : {str(e)}"
                print("Error is", e)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, filesize, downloaded_chunk, error_message, speed, '---', time.strftime('%Y-%m-%d %H:%M')
                )

                

    
    def _get_or_create_pause_event(self, filename):
        if filename not in self.pause_events:
            self.pause_events[filename] = asyncio.Event()
            self.pause_events[filename].set()  # Initially not paused
        return self.pause_events[filename]

    async def pause_downloads_fn(self, filename, size, link ,downloaded):
        pause_event = self._get_or_create_pause_event(filename)
        pause_event.clear()  # Set the pause flag for this file
        self.paused_downloads[filename] = {
                        'downloaded': downloaded,
                        'size': size,
                        'link': link,
                        'resume': False
                    }       
        await self.update_all_active_downloads('Paused.', filename)

    async def resume_downloads_fn(self, name, address, downloaded, cookies=None):
        print('Resuming--------------')

        pause_event = self._get_or_create_pause_event(name)
        pause_event.set()  # Clear the pause flag for this file
        self.paused_downloads[name] = {
            'downloaded': downloaded,
            'size': '---',
            'link': address,
            'resume': True
        }        
        for filename, info in self.paused_downloads.items():
            if name == filename:                          
                await self.addQueue((info['link'], filename, None, cookies))

        async with self.file_locks[filename]:
            if name in self.size_downloaded_dict:
                pass
            else:
                self.size_downloaded_dict[name] = [downloaded, time.time()]                
            
        await self.update_all_active_downloads('Resuming..', name)


        async with self.condition:
            self.condition.notify_all()

        


    async def update_all_active_downloads(self, status, filename):
        speed = 0
        info = self.paused_downloads.get(filename, {})
        await self.progress_manager.update_file_details_on_storage_during_download(
            filename, info.get('link', ''), info.get('size', '---'), 
            info.get('downloaded', 0), status, speed, '---', 
            time.strftime('%Y-%m-%d %H:%M')
        )



