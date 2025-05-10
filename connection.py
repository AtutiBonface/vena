import asyncio
import socket
import aiohttp
import logging
import time
from typing import Optional, List

class InternetConnectivityManager:
    def __init__(self, 
                 check_interval: int = 5, 
                 timeout: float = 5.0, 
                 hosts_to_check: Optional[List[str]] = None):
        """
        Initialize Internet Connectivity Manager
        
        Args:
            check_interval (int): Interval between connectivity checks (seconds)
            timeout (float): Timeout for connection checks
            hosts_to_check (List[str]): List of hosts to check for connectivity
        """
        self.logger = logging.getLogger(__name__)
        
        # Default hosts to check, prioritized by reliability
        self.hosts_to_check = hosts_to_check or [
            'https://www.google.com',
            'https://www.cloudflare.com',
            'https://www.microsoft.com',
            'https://dns.google'
        ]
        
        self.check_interval = check_interval
        self.timeout = timeout
        
        # Connectivity states
        self.is_connected = False
        self.last_connection_check = None
        
        # Event for tracking connectivity
        self.connectivity_event = asyncio.Event()
        
        # Retry mechanism
        self.connection_retry_count = 0
        self.max_connection_retries = 10
        
        # Download queue for resuming
        self.pending_downloads = asyncio.Queue()
        
    async def check_internet_connectivity(self) -> bool:
        """
        Check internet connectivity by attempting to connect to reliable hosts
        
        Returns:
            bool: True if internet is available, False otherwise
        """
        for host in self.hosts_to_check:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(host, timeout=self.timeout) as response:
                        if response.status == 200:
                            self.is_connected = True
                            self.last_connection_check = time.time()
                            self.connection_retry_count = 0
                            self.connectivity_event.set()
                            return True
            except (aiohttp.ClientError, asyncio.TimeoutError, 
                    socket.gaierror, ConnectionError) as e:
                self.logger.debug(f"Connection check failed for {host}: {e}")
                continue
        
        # If all checks fail
        self.is_connected = False
        self.connectivity_event.clear()
        return False
    
    async def monitor_connectivity(self):
        """
        Continuous monitoring of internet connectivity
        """
        while True:
            try:
                # Check connectivity
                connected = await self.check_internet_connectivity()
                
                if not connected:
                    self.connection_retry_count += 1
                    
                    # Exponential backoff for retry
                    backoff_time = min(
                        2 ** self.connection_retry_count, 
                        60  # Max wait of 1 minute
                    )
                    
                    self.logger.warning(
                        f"No internet connection. Retry {self.connection_retry_count}. "
                        f"Waiting {backoff_time} seconds."
                    )
                    
                    # Handle prolonged disconnection
                    if (self.connection_retry_count >= self.max_connection_retries):
                        await self.handle_prolonged_disconnection()
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
            
            except Exception as e:
                self.logger.error(f"Connectivity monitoring error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def handle_prolonged_disconnection(self):
        """
        Handle scenarios of prolonged internet disconnection
        """
        self.logger.critical("Prolonged internet disconnection detected")
        # You could implement additional logic here like:
        # - Send notification
        # - Log detailed system state
        # - Trigger specific recovery mechanisms
    
    async def wait_for_connection(self):
        """
        Wait until internet connection is restored
        """
        while not self.is_connected:
            await self.connectivity_event.wait()
    
    async def resume_downloads(self, download_manager):
        """
        Resume pending downloads when internet is restored
        
        Args:
            download_manager: Your download manager instance
        """
        while True:
            # Wait for connection restoration
            await self.wait_for_connection()
            
            try:
                # Process pending downloads
                while not self.pending_downloads.empty():
                    download_task = await self.pending_downloads.get()
                    
                    try:
                        # Attempt to resume download
                        await download_manager.resume_download(download_task)
                    except Exception as e:
                        self.logger.error(f"Failed to resume download: {e}")
                        # Optionally, you could re-queue the download
                        await self.pending_downloads.put(download_task)
            
            except Exception as e:
                self.logger.error(f"Error in download resumption: {e}")
            
            # Prevent tight looping
            await asyncio.sleep(self.check_interval)

# Integration with TaskManager
class TaskManager:
    def __init__(self, parent):
        # Existing initialization
        self.connectivity_manager = InternetConnectivityManager()
        
        # Start connectivity monitoring
        asyncio.create_task(self.connectivity_manager.monitor_connectivity())
        asyncio.create_task(
            self.connectivity_manager.resume_downloads(self)
        )
    
    async def start_task(self, file):
        link, filename, path, cookies = file
        try:
            # Existing download logic
            await self._download_file(link, filename, path, cookies)
        
        except aiohttp.ClientError as e:
            # Check if failure is due to connectivity
            if not self.connectivity_manager.is_connected:
                # Add to pending downloads
                await self.connectivity_manager.pending_downloads.put(file)
                
                self.logger.warning(
                    f"Download interrupted. Waiting for internet restoration: {filename}"
                )
            else:
                # Handle other client errors
                self.logger.error(f"Download failed: {e}")
    
    async def _download_file(self, link, filename, path, cookies):
        """
        Actual file download logic with connectivity check
        """
        # Wait if no internet connection
        await self.connectivity_manager.wait_for_connection()
        
        # Existing download implementation
        # ... download logic ...

# Usage example
async def main():
    #task_manager = TaskManager(parent)
    
    # Start download tasks
    #await task_manager.download_tasks()

    pass

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)