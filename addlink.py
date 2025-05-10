import asyncio
import sys, os , re, shutil, aiohttp, m3u8
from urllib.parse import urljoin
from PyQt6.QtWidgets import (QFileDialog, QPushButton, QFrame, QLineEdit, 
                            QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QProgressBar)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon
from settings import AppSettings
from pathlib import Path
from urllib.parse import urlparse , urlunparse ,urlsplit
from qasync import asyncSlot
import storage
from themes import ThemeColors
from venaUtils import OtherMethods

class LoadingSpinner(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setTextVisible(False)
        self.setMaximumWidth(200)  # Increased width
        self.setMaximumHeight(3)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #e0e0e0;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: #48D1CC;
                border-radius: 1px;
            }
        """)
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._update_value)
        self.setValue(0)
        
    def start(self):
        self.setMaximum(0)
        self._animation_timer.start(30)
        self.show()
        
    def stop(self):
        self._animation_timer.stop()
        self.hide()
        
    def _update_value(self):
        value = self.value()
        if value >= 100:
            self.setValue(0)
        else:
            self.setValue(value + 1)

class AddLink(QWidget):
    def __init__(self, app= None, url=None ,filename=None,cache = None, task_manager=None):
        super().__init__()
        self.setWindowTitle("Download file")
        self.setWindowIcon(QIcon('images/main.ico'))
        self.setGeometry(150, 150, 500, 280)  # Made window wider
        self.setFixedSize(500, 280)  # Prevent window resizing
        self.center_window()
        self.app_settings = AppSettings()
        self.indicator = app.show_less_popup
        self.app = app
        self.cache = cache
        self.task_manager = task_manager
        self.download_path = str(self.app_settings.default_download_path)
        self.theme_manager = ThemeColors()
        self.current_theme = storage.get_setting('THEME') or 'system'
        self.other_methods = OtherMethods()

        self.selected_path = None
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.CustomizeWindowHint  |
            Qt.WindowType.WindowCloseButtonHint            
        )
        
        self.setContentsMargins(0, 0, 0, 0)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 0, 5, 10)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.warning_label = QLabel("")
        self.warning_label.setObjectName('warning-label')
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.current_step = 1  # Track current step
        self.file_details = None  # Store validated file details
        
        # Create stacked frames for steps
        self.step1_frame = QFrame()
        self.step2_frame = QFrame()
        self.loading_spinner = LoadingSpinner()
        self.loading_spinner.hide()
        self.setup_step1()
        self.setup_step2()
        self.step2_frame.hide()

        main_layout.addWidget(self.step1_frame)
        main_layout.addWidget(self.step2_frame)

        self.setLayout(main_layout)
        self.apply_theme()

    def apply_theme(self):
        stylesheet = self.theme_manager.get_stylesheet(self.current_theme)
        self.setStyleSheet(stylesheet)

    def center_window(self):
        # Get the screen's geometry (size and position)
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        # Get the size of the window
        window_geometry = self.frameGeometry()
        # Calculate the center point
        center_point = screen_geometry.center()
        # Move the window's top-left corner to center it
        window_geometry.moveCenter(center_point)
        # Move the window to the calculated position
        self.move(window_geometry.topLeft())

    def setup_step1(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)  # Match step 2 margins
        layout.setSpacing(10)  # Match step 2 spacing
        
        # Warning and loading area
        warning_container = QVBoxLayout()
        warning_container.setSpacing(0)
        
        self.warning_label.setFixedHeight(20)
        warning_container.addWidget(self.warning_label)
        
        spinner_container = QHBoxLayout()
        spinner_container.addStretch()
        spinner_container.addWidget(self.loading_spinner)
        spinner_container.addStretch()
        warning_container.addLayout(spinner_container)
        
        layout.addLayout(warning_container)

        # Create input frames
        for label_text, widget_name, with_button in [
            ('Address', 'address', None), 
            ('File', 'filename', None),
            ('Save in', 'savein', True)
        ]:
            frame = QFrame()
            frame.setObjectName("input-label")
            frame.setFixedHeight(50)  # Fixed height for input containers
            
            layout_h = QHBoxLayout()
            layout_h.setContentsMargins(5, 0, 5, 0)
            
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setObjectName('label')
            label.setFixedWidth(50)
            
            entry = QLineEdit()
            entry.setObjectName('entry')
            entry.setFixedHeight(40)
            setattr(self, f"{widget_name}_entry", entry)
            
            layout_h.addWidget(label)
            layout_h.addWidget(entry)
            
            if with_button:
                btn = QPushButton(QIcon('images/change.png'), "")
                btn.setObjectName("change-path-btn")
                btn.setFixedSize(40, 40)
                btn.clicked.connect(self.openDownloadToFolder)
                layout_h.addWidget(btn)
            
            frame.setLayout(layout_h)
            layout.addWidget(frame)

        # Connect address entry signal
        self.address_entry.textChanged.connect(self.getInputValue)
        self.savein_entry.setDisabled(True)
        self.savein_entry.setText(self.download_path)

        # Button frame 
        button_frame = QFrame()
        button_frame.setFixedHeight(60)  # Give the frame fixed height
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 10)  # Even padding top and bottom
        button_layout.setSpacing(0)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        validate_button = QPushButton(QIcon('images/downloading.png'), ' Validate')
        validate_button.setIconSize(QSize(14, 14))
        validate_button.setObjectName('submit-btn')
        validate_button.setMinimumHeight(40)  # Set minimum height
        validate_button.setFixedSize(120, 40)  # Set fixed size
        validate_button.clicked.connect(self.validate_file)
        
        button_layout.addWidget(validate_button)
        button_frame.setLayout(button_layout)
        
        layout.addWidget(button_frame)
        # Remove stretches that could affect button size
        self.step1_frame.setLayout(layout)

    def setup_step2(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # Summary header
        summary_label = QLabel("Download Summary")
        summary_label.setObjectName("summary-label")
        layout.addWidget(summary_label)

        # Details container
        details_frame = QFrame()
        details_frame.setObjectName("details-frame")
        details_layout = QVBoxLayout()
        details_layout.setSpacing(8)

        # File details group with fixed heights and ellipsis for long text
        for label_name in ['file_size', 'disk_space', 'final_path', 'final_name']:
            label = QLabel()
            label.setObjectName('info-label')
            label.setFixedHeight(25)  # Fixed height for each info label
            label.setWordWrap(False)  # Prevent word wrap
            setattr(self, f'{label_name}_label', label)
            details_layout.addWidget(label)

        details_frame.setLayout(details_layout)
        layout.addWidget(details_frame)
        layout.addStretch()

        # Buttons container at bottom
        button_frame = QFrame()
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        back_button = QPushButton('Back')
        back_button.setObjectName('back-btn')
        back_button.setFixedSize(120, 40)
        
        download_button = QPushButton('Download')
        download_button.setObjectName('download-btn')
        download_button.setFixedSize(120, 40)
        
        back_button.clicked.connect(self.show_step1)
        download_button.clicked.connect(self.start_download)
        
        button_layout.addStretch()
        button_layout.addWidget(back_button)
        button_layout.addWidget(download_button)
        
        button_frame.setLayout(button_layout)
        layout.addWidget(button_frame)

        self.step2_frame.setLayout(layout)

    def show_step1(self):
        self.step2_frame.hide()
        self.step1_frame.show()
        self.current_step = 1

    def show_step2(self):
        self.step1_frame.hide()
        self.step2_frame.show()
        self.current_step = 2

    def openDownloadToFolder(self):
        home = str(Path.home())
        options = QFileDialog.Option.DontUseNativeDialog
        file_location = QFileDialog.getExistingDirectory(parent=self, caption="Select Folder", directory=home, options=QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog)
        if file_location:
            self.selected_path = file_location
            self.savein_entry.setText(file_location)
        else:
            self.selected_path = None
            if self.savein_entry.text().strip() == "":
                self.savein_entry.setText(self.download_path)
        
    def getInputValue(self):        
        link = self.address_entry.text()
        filename = self.filename_entry.text() 

        if not urlparse(link).scheme:
            link = f'http://{link}'

        url_parsed = urlparse(link)

        if os.path.basename(url_parsed.path):
            filename = os.path.basename(url_parsed.path)
            # Strip .m3u8 extension if present
            if filename.lower().endswith('.m3u8'):
                filename = os.path.splitext(filename)[0]
            self.filename_entry.setText(filename)
        else:
            custom_name = link.split('//')[1].split('.')[0]
            self.filename_entry.setText(custom_name)

    def sanitize_filename(self, filename):
        # Remove any invalid characters for filenames on most operating systems
        return re.sub(r'[\\/*?:"<>|]', "", filename)

    @asyncSlot()
    async def validate_file(self):
        self.warning_label.setText("")
        self.loading_spinner.start()

        link = self.address_entry.text()
        filename = self.filename_entry.text()

        if not urlparse(link).scheme:
            link = f'http://{link}'

        if not urlparse(link).netloc:
            self.warning_label.setText('Please enter a valid URL!')
            self.warning_label.setStyleSheet("color: brown;")
            self.loading_spinner.stop()
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(link) as response:
                    if response.status == 200:
                        pursed_url = urlparse(link)
                        file_path = pursed_url.path
                        is_m3u8 = 'application/x-mpegURL' in response.headers.get('Content-Type', '').lower() or file_path.lower().endswith('.m3u8')

                        
                        
                        if is_m3u8:
                            url_parsed = urlparse(link)
                            base_url = f"{url_parsed.scheme}://{url_parsed.netloc}{url_parsed.path.rsplit('/', 1)[0]}/"
                            
                            retry_count = 0
                            max_retries = 5
                            while retry_count < max_retries:
                                try:
                                    async with session.get(link) as m3u8_response:
                                        content = await m3u8_response.text()
                                        playlist = m3u8.loads(content)
                                        
                                        if not playlist.is_variant:
                                            segments_urls = [urljoin(base_url, segment.uri) for segment in playlist.segments]
                                            segments_urls = list(dict.fromkeys(segments_urls))
                                            
                                            # Get content type from first segment
                                            first_segment_url = segments_urls[0]
                                            async with session.head(first_segment_url) as seg_response:
                                                seg_content_type = seg_response.headers.get('Content-Type', '').lower()
                                                # Update filename with proper extension based on segment content type
                                                name = os.path.splitext(filename)[0]  # Remove any existing extension
                                                extension = self.other_methods.content_type_to_extension.get(seg_content_type, '.m3u8')
                                                filename = name + extension
                                                self.filename_entry.setText(filename)
                                            
                                            # Concurrent size fetching
                                            async def fetch_segment_size(seg_url):
                                                try:
                                                    async with session.head(seg_url) as seg_response:
                                                        if seg_response.status == 200 and 'Content-Length' in seg_response.headers:
                                                            return int(seg_response.headers['Content-Length'])
                                                except:
                                                    return 0
                                                return 0
                                                
                                            tasks = [fetch_segment_size(url) for url in segments_urls]
                                            segment_sizes = await asyncio.gather(*tasks)
                                            size = sum(segment_sizes)
                                            
                                        else:
                                            highest_res = max(playlist.playlists, 
                                                            key=lambda p: p.stream_info.resolution[0] if p.stream_info.resolution else 0)
                                            highest_url = urljoin(base_url, highest_res.uri)
                                            
                                            async with session.get(highest_url) as high_res_response:
                                                high_res_content = await high_res_response.text()
                                                high_res_playlist = m3u8.loads(high_res_content)
                                                segments_urls = [urljoin(base_url, segment.uri) for segment in high_res_playlist.segments]
                                                segments_urls = list(dict.fromkeys(segments_urls))
                                                
                                                # Concurrent size fetching for variant playlist
                                                tasks = [fetch_segment_size(url) for url in segments_urls]
                                                segment_sizes = await asyncio.gather(*tasks)
                                                size = sum(segment_sizes)
                                        
                                        break  # Success - exit retry loop
                                        
                                except Exception as e:
                                    retry_count += 1
                                    if retry_count == max_retries:
                                        raise
                                    await asyncio.sleep(retry_count * 2)
                            
                            # Get content type from first segment
                            first_segment_url = segments_urls[0]
                            async with session.head(first_segment_url) as seg_response:
                                content_type = seg_response.headers.get('Content-Type', '')
                                
                        else:
                            size = int(response.headers.get('Content-Length', 0))
                        
                        content_type = response.headers.get('Content-Type', '')
                        
                        # Get disk space
                        save_path = self.selected_path or self.download_path
                        disk_usage = shutil.disk_usage(save_path)
                        free_space = disk_usage.free
                        
                        # Format sizes
                        size_str = self.format_size(size)
                        free_space_str = self.format_size(free_space)
                        
                        # Store details with content type
                        self.file_details = {
                            'size': size,
                            'content_type': content_type,
                            'free_space': free_space,
                            'filename': filename
                        }
                        
                        # Update step 2 labels
                        self.file_size_label.setText(f"File size: {size_str}")
                        self.disk_space_label.setText(f"Free disk space: {free_space_str}")
                        self.final_path_label.setText(f"Download path: {save_path}")
                        self.final_name_label.setText(f"File name: {filename}")
                        
                        # Show step 2
                        self.show_step2()
                    else:
                        error_messages = {
                            404: "Resource not found - The file does not exist on the server",
                            403: "Access denied - You don't have permission to access this resource",
                            500: "Server error - The server encountered an error",
                            502: "Bad gateway - The server received an invalid response",
                            503: "Service unavailable - The server is temporarily down",
                        }
                        error_msg = error_messages.get(
                            response.status, 
                            f"Server returned status {response.status}"
                        )
                        self.warning_label.setText(f"Error: {error_msg}")
                        self.warning_label.setStyleSheet("color: brown;")
        except aiohttp.ClientConnectorError:
            self.warning_label.setText("Network Error: Please check your internet connection")
            self.warning_label.setStyleSheet("color: brown;")
        except Exception as e:
            if "Name or service not known" in str(e):
                self.warning_label.setText("Network Error: Unable to resolve host - Check URL or internet connection")
            else:
                self.warning_label.setText(f"Error: Unable to connect to server")
            self.warning_label.setStyleSheet("color: brown;")
        finally:
            self.loading_spinner.stop()

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

    @asyncSlot()
    async def start_download(self):
        if self.file_details:
            await self.add_task_to_downloads()

    @asyncSlot()
    async def add_task_to_downloads(self):
        link = self.address_entry.text()
        filename = self.filename_entry.text() 

        if not urlparse(link).scheme:
            link = f'http://{link}'

        if not urlparse(link).netloc:
            self.warning_label.setText('Insert correct address!')
            self.warning_label.setStyleSheet("color : brown;")
        else:
            if self.file_details:
                name, extension = os.path.splitext(filename)
                
                if not name:
                    self.warning_label.setText('No file name!')
                    self.warning_label.setStyleSheet("color : brown;")
                else:
                    name = self.sanitize_filename(name)
                    
                    # Get content type based extension
                    content_type = self.file_details['content_type'].lower()
                    if not extension:
                        extension = self.other_methods.content_type_to_extension.get(content_type, '.unknown')
                    
                    # For m3u8 files that failed to get segment content type
                    if extension == '.unknown' and link.endswith('.m3u8'):
                        extension = '.m3u8'
                        
                    final_filename = name + extension
                    final_filename = os.path.basename(final_filename)

                    # Queue format: (link, filename, path, cache, filesize)
                    queue_data = (
                        link, 
                        final_filename,
                        self.selected_path,
                        self.cache,
                        self.file_details['size']
                    )
                    
                    await self.task_manager.addQueue(queue_data)
                    
                    if self.task_manager.is_downloading:
                        self.warning_label.setText("Task Added!")
                        self.warning_label.setStyleSheet("color: green;")
                    else:                        
                        self.warning_label.setText("Started Downloading")
                        self.warning_label.setStyleSheet("color: green;")

                    self.selected_path = None
                    self.close()

                    if self.app.isHidden() or not self.app.isActiveWindow() or self.app.isMinimized():
                        self.indicator.file_added()
                        self.indicator.show()


