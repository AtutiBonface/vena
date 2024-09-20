import os, asyncio, aiohttp, ssl, certifi, time
import aiofiles, m3u8, random, logging
from pathlib import Path
from venaUtils import OtherMethods
from urllib.parse import urlparse, urlunparse, urljoin
from venaWorker import SegmentTracker

class NetworkManager:
    def __init__(self, config, task_manager):
        self.config = config
        self.other_methods = OtherMethods()
        self.task_manager = task_manager
        self.segment_trackers = {}
       
        # Default headers to mimic a browser's behavior
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'identity;q=1, *;q=0',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)        
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())  # SSL context to use certifi's certificates

    async def create_session(self, connector):       
        return aiohttp.ClientSession(connector=connector, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10))  # Create an aiohttp session with a custom connector and headers
    
    async def fetch_m3u8_segment_size(self, session, url): # Fetch the size of a single m3u8 segment by checking the Content-Length header
        async with session.get(url) as response:
            if response.status == 200 and 'Content-Length' in response.headers:
                return url, int(response.headers['Content-Length'])
            else:
                return url, 0  # Return 0 if the size is not available

    async def get_total_size_of_m3u8(self, session, m3u8_url, baseurl):      
        async with session.get(m3u8_url) as response:  # Download and parse the m3u8 playlist
            m3u8_content = await response.text()
            playlist = m3u8.loads(m3u8_content)
        
        segment_urls = [urljoin(baseurl, segment.uri) for segment in playlist.segments] # Extract segment URLs and create a list of tasks to fetch segment sizes concurrently
        tasks = [self.fetch_m3u8_segment_size(session, segment_url) for segment_url in segment_urls]
        results = await asyncio.gather(*tasks) # Get results as tuples of (url, size)
        segments_with_sizes = {url: size for url, size in results} # Create a dictionary with segment_url as the key and size as the value
        total_size = sum(segments_with_sizes.values()) # Return the total size and the dictionary of segment URLs with their sizes
        return total_size, segments_with_sizes
    
    async def get_filename_from_m3u8_content(self, session, f_path, url, filename):       
        name, _ = os.path.splitext(filename) # Determine the final filename based on the m3u8 content's MIME type
        async with session.get(url) as response:
            if response.status == 200 and 'Content-Type' in response.headers:
                return self.task_manager.return_filename_with_extension(f_path, name, response.headers.get('Content-Type', ''))
            else:
                return self.task_manager.return_filename_with_extension(f_path, name,  '')
    async def download_m3u8_media_plus_in_segments(self, session, filename, address, headers, segment_start, segment_end, segment_id, segment_size, total_filesize):
        retry_attempts = 0
        max_retries = 5
        success = False
        segment_downloaded = 0
        self.paused = False
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0'
        ]  

        print('---------------------segment-----------------------------')      
        segment_path = Path(f"{Path().home()}/.venaApp/temp/.{os.path.basename(filename)}")
        segment_path.mkdir(parents=True, exist_ok=True)
        segment_filename = segment_path / f'part{segment_id}'

        if filename not in self.segment_trackers:
            self.segment_trackers[filename] = SegmentTracker(filename)
        
        segment_tracker = self.segment_trackers[filename]        
        await segment_tracker.load_progress()

        async with segment_tracker.segment_lock:   
            segment_progress = segment_tracker.get_segment_progress(segment_id)    
        segment_total = segment_size

        if segment_filename.exists():
            segment_downloaded = segment_progress['downloaded']
        
        while retry_attempts < max_retries and not success:
            try:
                headers = self.headers.copy()
                headers['User-Agent'] = random.choice(user_agents)
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
                                    async with segment_tracker.segment_lock:                                                                    
                                        await segment_tracker.save_progress()
                                    self.paused = True
                                    raise DownloadPausedError('segment-paused')
                                
                                await file.write(chunk)
                                chunk_size = len(chunk)
                                segment_downloaded += chunk_size
                            
                                async with segment_tracker.segment_lock:   
                                    segment_tracker.update_segment(segment_id, segment_downloaded, segment_total)
                                
                                async with self.task_manager.file_locks[segment_filename]:
                                    if filename in self.task_manager.size_downloaded_dict:
                                        self.task_manager.size_downloaded_dict[filename][0] += len(chunk)
                                    else:
                                        self.task_manager.size_downloaded_dict[filename] = [len(chunk), time.time()]
                                await self.task_manager.progress_manager._handle_segments_downloads_ui(filename, address, total_filesize)

                        async with segment_tracker.segment_lock:      
                            await segment_tracker.save_progress()
                        success = True
                        return True
                    else:
                        retry_attempts += 1
                        await asyncio.sleep(retry_attempts * 2 + random.uniform(0.5, 1.5))
            except asyncio.CancelledError:
                async with segment_tracker.segment_lock:      
                    await segment_tracker.save_progress()
                return False  
            
            except Exception as e:
                if not str(e).startswith('segment-paused'):            
                    retry_attempts += 1
                    await asyncio.sleep(retry_attempts * 2 + random.uniform(0.5, 1.5))
                    self.paused = False
                    if retry_attempts == 4:
                        raise SegmentDownloadError('Failed')
                else:
                    raise DownloadPausedError('Paused')

        if not self.paused:
            raise SegmentDownloadError('Failed')
        else:
            raise DownloadPausedError('Paused')

class SegmentDownloadError(Exception):
    """Custom exception raised when a segment fails to download after retries."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class DownloadPausedError(Exception):
    
    def __init__(self, message="Download paused."):
        self.message = message
        super().__init__(self.message)