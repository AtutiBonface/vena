import os, asyncio,aiohttp, ssl, certifi, time, threading, re
from asyncio import Queue 
from settings import AppSettings
import  storage
import shutil, m3u8
from venaUtils import OtherMethods
from urllib.parse import urlparse, urlunparse, urljoin
from fileManager import FileManager
from networkManager import NetworkManager
from progressManager import ProgressManager

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
            self.network_manager = NetworkManager(self.config, self)
            self.file_manager = FileManager(self.config, self)
            self.progress_manager = ProgressManager(self, parent)
            self.headers = self.network_manager.headers

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
            self.paused_downloads = {} # Dictionary to keep track of paused downloads
            self.is_paused = False
            self.is_downloading = False
    async def append_file_details_to_storage(self, filename, path, address, date):
        # Append file details to storage
        if not path:
            path = AppSettings().default_download_path.__str__()
            
        await asyncio.to_thread(self.parent.add_download_to_list ,filename, address, path, date)
        await asyncio.to_thread(storage.add_data,filename,address, '---', '---', 'waiting...', date, path)

     
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
            # waits for self.links and filename queue to have link if it there are links it continues 
            # otherwise it keeps waiting this prevents while True not to run forever as it consumes alot cpu
            async with self.condition:
                await self.condition.wait()           
            while not self.links_and_filenames.empty():
                file = await self.links_and_filenames.get()
                link, filename, path = file
                if not filename in self.paused_downloads:## filename in paused downloads has path with it but if it does not exist it creates name together with path selected
                    filename = self.file_manager.validate_filename(filename, path)
                    name_with_no_path = os.path.basename(filename)
                    await self.append_file_details_to_storage(name_with_no_path, path, link, time.strftime(r'%Y-%m-%d')) 
                file = (link, filename, path)                
                async with self.file_semaphore:  # Limit concurrent file downloads
                    asyncio.create_task(self.start_task(file))
                self.links_and_filenames.task_done()
            if self.links_and_filenames.empty():
                self.is_downloading = False

    async def start_task(self, file): 
        link, filename ,path= file
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=None, limit_per_host=10)
        created_session = await self.network_manager.create_session(connector)
        async with created_session as session:        
            downloaded_chunk = self.paused_downloads.get(filename, {}).get('downloaded', 0)
            size = 0
            speed =0            
            try:
                async with session.get(link) as resp:                   
                    if resp.status in (200, 206):                     
                        m3u8_extension_in_link = self.other_methods.get_m3u8_in_link(link)
                        if m3u8_extension_in_link:                            
                            segments_urls = []
                            m3u8_tasks = []
                            url_parsed = urlparse(link)
                            base_url = f"{url_parsed.scheme}://{url_parsed.netloc}{url_parsed.path.rsplit('/', 1)[0]}/"
                            content = await resp.text()
                            # Parse the M3U8 content
                            playlist = m3u8.loads(content)
                            if not playlist.is_variant:                               
                                for segment in playlist.segments:
                                    segment_url = urljoin(base_url, segment.uri)                                   
                                    segments_urls.append(segment_url)                                    
                                new_filename = await self.network_manager.get_filename_from_m3u8_content(session,path, segments_urls[0], filename)
                                await self.update_changed_filename(filename, new_filename)
                                filename = new_filename
                                size = await self.network_manager.get_total_size_of_m3u8(session, link, base_url)
                                for url ,seg_no,  in zip(segments_urls, range(len(segments_urls))):
                                    async with self.segment_semaphore:
                                        m3u8_tasks.append(self.network_manager.download_m3u8_segment(session, url,filename, seg_no, self.headers, size))
                            await asyncio.gather(*m3u8_tasks)
                            await self.file_manager.combine_segments(filename, link, size, len(segments_urls))
                            async with self.lock:
                                if filename in self.size_downloaded_dict:
                                    del self.size_downloaded_dict[filename]

                        else:## if it is not a .m3u8 file
                            size = int(resp.headers.get('Content-Length', 0))
                            content_type = resp.headers.get('Content-Type', '')                            

                            pursed_url = urlparse(link)

                            f_n, ex = os.path.splitext(os.path.basename(filename))

                            if not (f_n and ex):
                               
                                new_filename = self.return_filename_with_extension(path, filename, content_type)

                                await self.update_changed_filename(filename, new_filename)
                                filename = new_filename

                            range_supported = 'Accept-Ranges' in resp.headers
                            
                            if size > self.config.SEGMENT_SIZE * 3 and range_supported:
                                
                                num_segments = (size + self.config.SEGMENT_SIZE - 1) // self.config.SEGMENT_SIZE

                                tasks = []
                                for seg_no in range(num_segments):
                                    start = seg_no * self.config.SEGMENT_SIZE
                                    end = start + self.config.SEGMENT_SIZE - 1 if seg_no < num_segments - 1 else size - 1
                                    async with self.segment_semaphore:
                                        tasks.append(self.network_manager.fetch_segment(session, link, start, end, num_segments, filename, seg_no, size))

                                    await asyncio.sleep(self.config.CONCURRENCY_DELAY)

                                await asyncio.gather(*tasks)
                                await self.file_manager.combine_segments(filename,link,size, num_segments)

                                async with self.lock:
                                    if filename in self.size_downloaded_dict:
                                        del self.size_downloaded_dict[filename]  
                            else:                               
                                await self.file_manager._handle_download(resp, filename, link, downloaded_chunk)
                               
                    else:
                        error_message = f"failed! : Unexpected status {resp.status}"
                        await self.progress_manager.update_file_details_on_storage_during_download(
                filename,link, size, downloaded_chunk, error_message, speed, time.strftime('%Y-%m-%d'))
                        
            
            except aiohttp.ClientError as e: 
                error_message = f"failed! : ClientError - {str(e)}"
                print(e)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, size, downloaded_chunk, error_message, speed, time.strftime('%Y-%m-%d')
                )
            except asyncio.TimeoutError as e:
                error_message = f"failed! : TimeoutError - {str(e)}"
                print(e)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, size, downloaded_chunk, error_message, speed, time.strftime('%Y-%m-%d')
                )
            except ssl.SSLError as e:
                error_message = f"failed! : SSLError - {str(e)}"
                print(e)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, size, downloaded_chunk, error_message, speed, time.strftime('%Y-%m-%d')
                )
            except OSError as e:
                error_message = f"failed! : OSError - {str(e)}"
                print(e)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, size, downloaded_chunk, error_message, speed, time.strftime('%Y-%m-%d')
                )
            except ValueError as e:
                error_message = f"failed! : ValueError - {str(e)}"
                print(e)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, size, downloaded_chunk, error_message, speed, time.strftime('%Y-%m-%d')
                )
            except RuntimeError as e:
                error_message = f"failed! : RuntimeError - {str(e)}"
                print(e)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, size, downloaded_chunk, error_message, speed, time.strftime('%Y-%m-%d')
                )
            except Exception as e:
                error_message = f"failed! : {str(e)}"
                print("Error is", e)
                await self.progress_manager.update_file_details_on_storage_during_download(
                    filename, link, size, downloaded_chunk, error_message, speed, time.strftime('%Y-%m-%d')
                )

                

    


    async def pause_downloads_fn(self, filename, size, link ,downloaded):
        self.paused_downloads[filename] = {
                        'downloaded': downloaded,
                        'size': size,
                        'link': link,
                        'resume': False
                    }
       
        await self.update_all_active_downloads('paused.')

    async def resume_downloads_fn(self, name, address, downloaded):

        self.paused_downloads[name] = {
            'downloaded': downloaded,
            'size': '---',
            'link': address,
            'resume': True
        }
        
        for filename, info in self.paused_downloads.items():
            if name == filename:                          
                await self.addQueue((info['link'], filename, None))
            
        await self.update_all_active_downloads('resuming...')      
        async with self.condition:
            self.condition.notify_all()




    async def update_all_active_downloads(self, status):
        speed = 0
        for filename, info in self.paused_downloads.items():
            await self.progress_manager.update_file_details_on_storage_during_download(
                filename, info['link'], info['size'], info['downloaded'], status,speed, time.strftime(r'%Y-%m-%d')
            )

                
                        
        
