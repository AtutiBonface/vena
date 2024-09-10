import os, asyncio, aiohttp, ssl, certifi, time
import aiofiles, m3u8, random, logging
from pathlib import Path
from venaUtils import OtherMethods
from urllib.parse import urlparse, urlunparse, urljoin

class NetworkManager:
    def __init__(self, config, task_manager):
        self.config = config
        self.other_methods = OtherMethods()
        self.task_manager = task_manager
       
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
        # SSL context to use certifi's certificates
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

    async def create_session(self, connector):
        # Create an aiohttp session with a custom connector and headers
        return aiohttp.ClientSession(connector=connector, headers=self.headers, timeout=aiohttp.ClientTimeout(total=None))
    
    async def fetch_m3u8_segment_size(self, session, url):
        # Fetch the size of a single m3u8 segment by checking the Content-Length header
        async with session.get(url) as response:
            if response.status == 200 and 'Content-Length' in response.headers:
                return int(response.headers['Content-Length'])
            else:
                return 0  # Return 0 if the size is not available

    async def get_total_size_of_m3u8(self, session, m3u8_url, baseurl):
        # Download and parse the m3u8 playlist
        async with session.get(m3u8_url) as response:
            m3u8_content = await response.text()
            playlist = m3u8.loads(m3u8_content)

        # Extract segment URLs and create a list of tasks to fetch segment sizes concurrently
        segment_urls = [urljoin(baseurl, segment.uri) for segment in playlist.segments]
        tasks = [self.fetch_m3u8_segment_size(session, segment_url) for segment_url in segment_urls]
        segment_sizes = await asyncio.gather(*tasks)

        return sum(segment_sizes)  # Return the total size of all segments
    
    async def get_filename_from_m3u8_content(self, session, f_path, url, filename):
        # Determine the final filename based on the m3u8 content's MIME type
        name, _ = os.path.splitext(filename)

        async with session.get(url) as response:
            if response.status == 200 and 'Content-Type' in response.headers:
                return self.task_manager.return_filename_with_extension(f_path, name, response.headers.get('Content-Type', ''))
            else:
                return self.task_manager.return_filename_with_extension(f_path, name,  '')

    async def fetch_segment(self, session, url, start, end, total_segments, filename, segment_id, original_filesize):
        retry_attempts = 0
        max_retries = 5
        success = False
        segment_downloaded = 0
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0'
        ]

        segment_path = Path(f"{Path().home()}/.venaApp/temp/.{os.path.basename(filename)}")
        segment_path.mkdir(parents=True, exist_ok=True)
        segment_filename = segment_path / f'part{segment_id}'

        # Check if the segment is partially or fully downloaded
        if segment_filename.exists():
            start += segment_filename.stat().st_size
        
        while retry_attempts < max_retries and not success:
            try:
                headers = self.headers.copy()
                headers['User-Agent'] = random.choice(user_agents)
                headers['Referer'] = self.other_methods.get_base_url(url)
                headers['Range'] = f'bytes={start}-{end}' if end else f'bytes={start}-'
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 206:
                        async with aiofiles.open(segment_filename, 'ab') as file:
                            async for chunk in response.content.iter_chunked(self.config.CHUNK_SIZE):
                                await file.write(chunk)
                                chunk_size = len(chunk)
                                segment_downloaded += chunk_size


                                # Lock and update UI for download progress
                                async with self.task_manager.lock:
                                    if filename in self.task_manager.size_downloaded_dict:
                                        self.task_manager.size_downloaded_dict[filename][0] += len(chunk)
                                    else:
                                        self.task_manager.size_downloaded_dict[filename] = [len(chunk), time.time()]
                                await self.task_manager.progress_manager._handle_segments_downloads_ui(filename, url, original_filesize)
                        success = True
                    else:
                        retry_attempts += 1
                        await asyncio.sleep(retry_attempts * 2)  # Exponential backoff
            except Exception as e:
                retry_attempts += 1
                await asyncio.sleep(retry_attempts * 2)

        if not success:
            print(f"Failed to download segment {segment_id} after {max_retries} attempts.")
        

        

    async def download_m3u8_segment(self, session, url, filename, seg_no, headers, original_filesize):

        retry_attempts = 0
        max_retries = 5
        success = False
        segment_downloaded = 0
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0'
        ]

        segment_path = Path(f"{Path().home()}/.venaApp/temp/.{os.path.basename(filename)}")
        segment_path.mkdir(parents=True, exist_ok=True)
        segment_filename = segment_path / f'part{seg_no}'

        # Check if the segment is partially or fully downloaded
        if segment_filename.exists():
            segment_downloaded += segment_filename.stat().st_size
        
        while retry_attempts < max_retries and not success:
            try:
                headers = self.headers.copy()
                headers['User-Agent'] = random.choice(user_agents)
                headers['Referer'] = self.other_methods.get_base_url(url)
                if segment_downloaded > 0:
                    headers['Range'] = f'bytes={segment_downloaded}-'
                else:
                    
                    headers.pop('Range', None)  # Remove Range header for full download
               
                
                async with session.get(url, headers=headers) as response:
                    if response.status in (206, 200):
                        async with aiofiles.open(segment_filename, 'ab') as file:
                            async for chunk in response.content.iter_chunked(self.config.CHUNK_SIZE):
                                await file.write(chunk)
                                chunk_size = len(chunk)
                                segment_downloaded += chunk_size

                                # Lock and update UI for download progress
                                async with self.task_manager.lock:
                                    if filename in self.task_manager.size_downloaded_dict:
                                        self.task_manager.size_downloaded_dict[filename][0] += len(chunk)
                                    else:
                                        self.task_manager.size_downloaded_dict[filename] = [len(chunk), time.time()]
                                await self.task_manager.progress_manager._handle_segments_downloads_ui(filename, url, original_filesize)
                        success = True
                    else:
                        self.logger.warning(f"Segment {seg_no} returned status {response.status}. Retry attempt {retry_attempts}.")
                        retry_attempts += 1
                        await asyncio.sleep(retry_attempts * 2 + random.uniform(0.5, 1.5))
            except Exception as e:
                self.logger.error(f"Exception during download of segment {seg_no}: {e}")
                retry_attempts += 1
                await asyncio.sleep(retry_attempts * 2 + random.uniform(0.5, 1.5))

        if not success:
            self.logger.error(f"Failed to download segment {seg_no} after {max_retries} attempts.")
       