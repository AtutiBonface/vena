import  asyncio , time, re
import aiofiles, storage
from venaUtils import OtherMethods
from urllib.parse import urlparse, urlunparse, urljoin

class ProgressManager:
    def __init__(self, task_manager, my_app):
        self.task_manager = task_manager
        self.parent = my_app
        self.other_methods = OtherMethods()
        self.last_update_time = {}  # Store the last update time for each file
        self.update_interval = 0.8  # Update every 0.8 seconds 

    async def update_file_details_on_storage_during_download(self, filename, address,size, downloaded, status, speed, date):
        # Update file details in storage during download
        await asyncio.to_thread(self.parent.update_download, filename, status, size,downloaded, date, speed)
        await asyncio.to_thread(storage.update_data, filename, address,size, downloaded, status, date)

    async def _handle_segments_downloads_ui(self,filename, link, total_size):
        
        current_time = time.time()
        
        # Check if enough time has passed since the last update
        if filename not in self.last_update_time or current_time - self.last_update_time.get(filename, 0) >= self.update_interval:
            async with self.task_manager.lock:
                if filename in self.task_manager.size_downloaded_dict:
                    total_downloaded, start_time = self.task_manager.size_downloaded_dict[filename]
                    unit_time = time.time() - start_time
                    if total_downloaded > 0 and unit_time > 1:
                        down_in_mbs = total_downloaded / (1024 * 1024)
                        speed = down_in_mbs / unit_time
                        new_speed = round(speed, 3)
                        speed_str = self.other_methods.returnSpeed(new_speed)
                        percentage = round((total_downloaded / total_size) * 100, 0)

                        await self.update_file_details_on_storage_during_download(
                            filename, link, total_size, total_downloaded, f'{percentage}%', speed_str, time.strftime(r'%Y-%m-%d')
                        )

                        # Update the last update time for this file
                        self.last_update_time[filename] = current_time                       

    async def _update_progress(self,filename, link, size, downloaded_chunk, start_time):

        current_time = time.time()


        if filename not in self.last_update_time or current_time - self.last_update_time.get(filename, 0) >= self.update_interval:
            unit_time = time.time() - start_time

            if downloaded_chunk > 0 and unit_time > 1:  # Ensure some time has passed and some data is downloaded
                down_in_mbs = downloaded_chunk / (1024 * 1024)
                speed = down_in_mbs / unit_time
                new_speed = round(speed, 3)
                speed_str = self.other_methods.returnSpeed(new_speed)
                percentage = round((downloaded_chunk / size) * 100, 0)
            
                
                await self.update_file_details_on_storage_during_download(
                    filename, link, size, downloaded_chunk, f'{percentage}%', speed_str, time.strftime(r'%Y-%m-%d')
                )

                # Update the last update time for this file
                self.last_update_time[filename] = current_time 
            else:           
                pass
