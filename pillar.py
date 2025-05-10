import os,  asyncio , websockets, json, subprocess, platform
from venaUtils import OtherMethods, Colors, Images
import storage, queue
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,QScrollArea,QLineEdit,
    QPushButton, QFrame, QStackedWidget,QSystemTrayIcon,QMenu, QCheckBox
)
from venaWorker import Worker, SetAppTray
from PyQt6.QtGui import QIcon, QAction, QFont,QFontMetrics,QPixmap
from PyQt6.QtCore import Qt, QPoint,QSize ,QThread, QEvent
from addlink import AddLink
from qasync import asyncSlot
from downloadingIndicator import DownloadIndicator
from taskManager import TaskManager
from settingsPage  import SettingsWindow
from aboutPage import AboutWindow
from fileNotFound_plus import DeletionConfirmationWindow, FileNotFoundDialog
from settings import AppSettings
from themes import ThemeColors


class MainApplication(QMainWindow):
    def __init__(self, loop, *args, **kwargs):
        super().__init__(*args, **kwargs)
        storage.initiate_database()  
        storage.create_settings_database()   
        self.loop = loop
        self.setup_data()
        self.setup_tray_icon()
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()
        self.start_background_tasks()
        self.theme_manager = ThemeColors()
        self.current_theme = storage.get_setting('THEME') or 'system'
        self.apply_theme()

    def apply_theme(self):
        stylesheet = self.theme_manager.get_stylesheet(self.current_theme)
        self.setStyleSheet(stylesheet)
        
    def switch_theme(self, theme_name):
        self.current_theme = theme_name
        storage.insert_setting('THEME', theme_name)
        self.apply_theme()
        if hasattr(self, 'show_less_popup'):
            self.show_less_popup.update_theme(theme_name)

    def setup_window(self):
        self.setWindowTitle('VenaApp')
        self.setWindowIcon(QIcon(self.other_methods.resource_path('images/main.ico')))
        self.setGeometry(100, 100, 1000, 640)
        self.center_window()
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6f7;
            }
            #content-container {
                background-color: white;
                border: 1px solid #e1e4e8;
                border-radius: 8px;
                margin: 8px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e1e4e8;
            }
            #sidebar {
                background-color: #f1f2f3;
                border-right: 1px solid #e1e4e8;
                padding: 8px;
            }
        """)

    def setup_styles(self):
        self.xe_images =Images()
        self.setStyleSheet(self.other_methods.get_qss())

    def setup_data(self):
        self.xengine_downloads  = {}
        self.load_downloads_from_db()
        self.task_manager = TaskManager(self)
        self.other_methods = OtherMethods()
        self.update_queue = queue.Queue()
        self.show_less_popup = DownloadIndicator(self)
        self.app_config =  AppSettings()
        self.app_config.set_all_settings_to_database()   
        self.other_methods.set_rounded_corners(self.show_less_popup)
        self.previously_clicked_btn = None
        self.details_of_file_clicked = None
        self.running_tasks = {}
        self.active_file_widgets = {}
        self.complete_file_widgets = {}
        self.file_widgets = {}
        self.files_to_be_downloaded = []   
        self.add_link_top_window = None
        self.tray_icon = None
        

    def create_widgets(self):   
        self.create_app_container()    
        self.create_sidebar()
        self.create_content_area()
        self.create_file_list()
        self.create_top_bar()
        self.create_pages()

    def create_app_container(self):
        central_widget = QWidget(self)
        central_widget.setObjectName("hero")
        self.main_layout = QVBoxLayout(central_widget)
        self.body_layout = QHBoxLayout()
        self.main_layout.addLayout(self.body_layout)        
        self.setCentralWidget(central_widget)

    def create_pages(self):
        self.stacked_widget = QStackedWidget()
        self.home_page = self.content_area
        self.about_page = AboutWindow()
        self.settings_page = SettingsWindow(self)
        
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.about_page)
        self.stacked_widget.addWidget(self.settings_page)

    def setup_layout(self):
        self.content_area.content_area.addWidget(self.topbar)
        self.content_area.content_area.addWidget(self.file_list)
        self.body_layout.addWidget(self.sidebar)
        self.body_layout.addWidget(self.stacked_widget, 1)

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.sidebar.update_button_styles(index)
    
    def closeEvent(self, event):
        """ Override the close event to hide the window instead of quitting the application """
        event.ignore()
        self.hide()

    def restore_window(self):
        """ Restore the main window from the system tray """
        self.showNormal()
        self.activateWindow()

    def quit_application(self):
        """ Quit the application from the system tray icon menu """
        if self.add_link_top_window is not None:
            self.add_link_top_window.close()
        if self.show_less_popup.isVisible():
            self.show_less_popup.close()        
        self.loop.stop()

        QApplication.quit()

    def on_tray_icon_activated(self, reason):
        """ Handle tray icon activation to show the main window """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.restore_window() 

    def setup_tray_icon(self):
        self.tray_icon = SetAppTray(self)
        self.tray_icon.tray_icon.show()

    async def run_all_tasks(self):    
        await asyncio.gather(# Run both websocket_main and TaskManager's download_tasks
            self.websocket_main(),
            self.task_manager.download_tasks()
        ) 

    def start_background_tasks(self):
        self.worker = Worker(self.update_queue)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker.update_signal.connect(self.update_file_widget)
        self.worker_thread.started.connect(self.worker.start_working)
        self.worker_thread.start()

    def do_action(self, text):
        """Handle actions for file operations"""
        if self.details_of_file_clicked:
            f_name, path = self.details_of_file_clicked
            path_and_file = os.path.join(path, f_name)
            
            if text == 'Open':
                if not os.path.exists(path_and_file):
                    self.file_not_found_popup = FileNotFoundDialog(self, f_name)
                    self.file_not_found_popup.show()
                else:
                    system_name = platform.system()
                    if system_name == 'Windows':
                        os.startfile(path_and_file)
                    elif system_name == 'Linux':
                        subprocess.Popen(["xdg-open", path_and_file])
                        
            elif text == 'Delete':
                self.confirm = DeletionConfirmationWindow(self, f_name, path_and_file)
                self.confirm.show()
                    
            elif text == 'Pause':
                self.pause_downloading_file(path_and_file)
                
            elif text == 'Resume':
                self.resume_paused_file(path_and_file)
                
            elif text == 'Restart':
                # Add restart functionality here if needed
                pass

    # Sidebar related methods
    def create_sidebar(self):       
        self.sidebar = Sidebar(self)
    # Content area related methods
    def create_content_area(self):       
        self.content_area = ContentArea()
        
    # Top bar related methods
    def create_top_bar(self):          
        self.topbar = TopBar(self)
    
    # File list related methods
    def create_file_list(self):
        self.file_list = ActiveFileList(self)

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

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            # Check if the window is minimized
            if self.isMinimized():
                if not self.show_less_popup.isVisible():
                    self.show_less_popup.show()
           
            elif self.isActiveWindow():
                if  self.show_less_popup.isVisible():
                    self.show_less_popup.hide()
                
            
        

    # WebSocket related methods
    @asyncSlot()
    async def handle_websockets(self, websocket, path):
        #handling sockets from extension here
        try:
            async for message in websocket:
                if message:
                    data = json.loads(message)              
                    count = int(data['count'])
                    digit = 1
                    if count > 1:
                        self.files_to_be_downloaded = data['files']                         
                                                                  
                    else:
                        url = ''
                        filename = ''            
                        for file in data['files']:
                            url = file['link']
                            filename = file['name'] 

                            cookies = file.get('cookies', None)

                            if cookies is not None:
                                cookies = self.other_methods.format_cookies(cookies)                           
                            
                            # Create the top window only once
                            self.add_link_top_window = AddLink(app=self,cache=cookies, url=url, filename=filename, task_manager=self.task_manager)                               
                            self.add_link_top_window.show()                  
  
                else:
                    print("No message")
        except Exception as e:
            pass

    async def websocket_main(self):  
        server = await websockets.serve(self.handle_websockets, '127.0.0.1', 65432)        
        await server.wait_closed()  

    # Database related methods
    def load_downloads_from_db(self):
        all_downloads = storage.get_all_data()
        for download in all_downloads:
            id, filename, address, filesize, downloaded, status, percentage,modification_date, path, cookies = download
            self.xengine_downloads[filename] = {
                'url': address,
                'status': status,
                'downloaded': downloaded,
                'filesize': filesize,
                'modification_date': modification_date,
                'path': path,
                'percentage': percentage,
                'cookies': cookies
            }

    # File management methods
    def add_download_to_list(self, filename, address, path, date, cookies):        
        self.xengine_downloads[filename] = {
            'url': address,
            'status': 'Waiting..',
            'downloaded': '---',
            'filesize': '---',
            'modification_date': date,
            'path': path,
            'percentage' : '0%',
            'cookies': cookies
        }
        self.update_queue.put((filename, 'Waiting..', '---','---','---','---', date))
    
    def update_download(self, filename, status, size, downloaded ,date, speed, percentage):
        size = str(size)
        downloaded = str(downloaded)
        name = os.path.basename(filename)
        path = self.xengine_downloads[name]['path']       
        if name in self.xengine_downloads:
            updateDict = self.xengine_downloads[name]           
            if 'failed' in status.lower():  # Convert status to lowercase for case-insensitive comparison
                updateDict['status'] = 'Failed!'
            else:
                updateDict['status'] = status
            updateDict['filesize'] = size
            updateDict['modification_date'] = date
            updateDict['downloaded'] = downloaded
            if not percentage == '---'  or not  percentage.strip() == '':
                updateDict['percentage'] = percentage

            self.update_queue.put((name, updateDict['status'], size, downloaded,speed,percentage,date))

    def update_file_widget(self, filename, status, size, downloaded,speed, percentage ,date):                  
        if 'finished' in status.lower():
            self.show_less_popup.download_completed()
            if filename in self.active_file_widgets:
                widget = self.active_file_widgets.pop(filename)
                self.file_list.file_layout.removeWidget(widget)
                widget.setParent(None)
            
            if filename not in self.complete_file_widgets:
                new_widget = FileItemWidget(
                    app=self,
                    filename=filename,
                    path=self.xengine_downloads[filename]['path'],
                    file_size=size,
                    downloaded=downloaded,
                    modified_date=date,
                    status=status,
                    percentage=percentage,
                    speed=speed
                )
                self.complete_file_widgets[filename] = new_widget
                self.file_list.file_layout.addWidget(new_widget)
        else:
            if filename in self.active_file_widgets:
                if "failed" in status.lower():
                    self.show_less_popup.download_failed()
                self.active_file_widgets[filename].update_widget(filename, status, size, downloaded, date, speed, percentage)
            else:
                self.add_new_file_widget(filename, status, size, date)

        

    def add_new_file_widget(self, filename, status, size, date): 
        path = self.xengine_downloads[filename]['path']     
        new_widget = FileItemWidget(
                app = self,
                filename=f"{filename}",
                path = path,
                file_size=f"{size}",
                downloaded=f"---",
                modified_date=f"{date}",
                status=status,
                percentage= f"---",
                speed="---"
            )
        self.active_file_widgets[filename] = new_widget       
        self.file_list.file_layout.insertWidget(0, new_widget)
       
    def toggle_file_details(self, filename,file_path):       
       
         
        modification_date = self.xengine_downloads[filename]['modification_date']
        file_size =  self.xengine_downloads[filename]['filesize']
        address =  self.xengine_downloads[filename]['url']
        filestatus =  self.xengine_downloads[filename]['status']

        file_size = self.other_methods.return_filesize_in_correct_units(file_size)

        thumbnail = self.other_methods.return_thumbnail(filename, file_path, filestatus)     

   

        self.content_area.edit_fileinfo(thumbnail, filename, file_path, modification_date, file_size, address, filestatus )

    def update_file_details(self, filename, status, downloaded,size,speed):
        path = self.xengine_downloads[filename]['path']
        thumbnail = self.other_methods.return_thumbnail(filename, path, status)
        self.content_area.update_fileinfo(thumbnail, filename, status, size)


       
    # File operations
    def pause_downloading_file(self, filename_with_path):
        f_name = os.path.basename(filename_with_path)
        self.load_downloads_from_db()## reasign values to xengine_downloads to get updated values for downloaded chuck
        for name , details in self.xengine_downloads.items():
            if name == f_name and not  ( 'finished' in details['status'].lower() or details['status'] == '100.0%'):
                size = details['filesize']
                link = details['url']
                downloaded = details['downloaded']           
                asyncio.run_coroutine_threadsafe(self.task_manager.pause_downloads_fn(filename_with_path, size, link ,downloaded), self.loop)
                
    def resume_paused_file(self, filename_with_path):
        def safe_int(value):
            try:
                return int(value)
            except ValueError:
                return 0    
        f_name = os.path.basename(filename_with_path) 
        self.load_downloads_from_db()## reasign values to xengine_downloads to get updated values for downloaded chuck
        self.downloaded_chuck = 0
        self.file_size = 0
        exclude_statuses = ['finished', 'waiting', 'resuming']
        for name , details in self.xengine_downloads.items():
                            
            # Check if the download should be resumed based on status and progress
            if name == f_name and not (
                any(status in details['status'].lower() for status in exclude_statuses) or 
                details['percentage'] == '100.0%'
            ):                
                self.downloaded_chuck = safe_int(details.get('downloaded', 0))
                self.file_size = safe_int(details.get('filesize', 0))    
                cookies = details.get('cookies', None)          
                
                asyncio.run_coroutine_threadsafe(self.task_manager.resume_downloads_fn(filename_with_path,  details['url'], self.downloaded_chuck, cookies)  ,self.loop)
        
    def update_filename(self, old_name, new_name):
        """Update filename in UI and data structures"""     
        pathless_old_name = os.path.basename(old_name)
        pathless_new_name = os.path.basename(new_name)

        # First update the downloads dictionary
        if pathless_old_name in self.xengine_downloads:
            value = self.xengine_downloads.pop(pathless_old_name)
            self.xengine_downloads[pathless_new_name] = value
                      
        # Then update active widgets dictionary and UI
        if pathless_old_name in self.active_file_widgets:
            value = self.active_file_widgets.pop(pathless_old_name) 
            self.active_file_widgets[pathless_new_name] = value
            file_widget = self.active_file_widgets[pathless_new_name]
            file_widget.update_filename(pathless_new_name)
        
        # Also check completed widgets
        elif pathless_old_name in self.complete_file_widgets:
            value = self.complete_file_widgets.pop(pathless_old_name)
            self.complete_file_widgets[pathless_new_name] = value
            file_widget = self.complete_file_widgets[pathless_new_name]
            file_widget.update_filename(pathless_new_name)

    def return_all_downloads(self):
        return self.xengine_downloads
    
    def delete_complete_download(self):            
        completed_files = [filename for filename, detail in self.return_all_downloads().items() if detail['status'] == 'completed.']
        for filename in completed_files:
            del self.xengine_downloads[filename]       
        storage.clear_download_finished()
   
    def delete_details_or_make_changes(self, filename):      
        storage.delete_individual_file(filename)## delete from storage       
        self.remove_individual_file_widget(filename) ## destroy widget

    def remove_individual_file_widget(self, filename):  
        if filename in  self.active_file_widgets:
            widget = self.active_file_widgets[filename]
            self.file_list.file_layout.removeWidget(widget) 
            widget.setParent(None)
        elif filename in  self.complete_file_widgets: 
             widget = self.complete_file_widgets[filename] 
             self.file_list.file_layout.removeWidget(widget)
             widget.setParent(None)
        
        
        self.previously_clicked_btn = None
        self.details_of_file_clicked = None
       
       

    def clear_displayed_files_widgets(self):
        for filename,widget in self.complete_file_widgets.items():
            self.file_list.file_layout.removeWidget(widget)
            widget.setParent(None)


        self.previously_clicked_btn = None
        self.previously_clicked_file = None             
        storage.clear_download_finished()        
        self.complete_file_widgets = {}

    def clear_failed_files_plus_their_widgets(self):       
        failed_files = []
        for filename , details in self.xengine_downloads.items():
            if 'failed' in details['status'].lower():
                failed_files.append(filename)

        for name , widget in self.active_file_widgets.items():
            if name in failed_files:
                self.file_list.file_layout.removeWidget(widget)
                widget.setParent(None)

        self.previously_clicked_btn = None
        self.previously_clicked_file = None             
        storage.clear_download_failed()        
        #self.active_file_widgets = {}
          

class TopBar(QFrame):
    def __init__(self, app):
        super().__init__()  
        self.app = app  
        self.task_manager = app.task_manager 
        self.other_methods = OtherMethods()  
        self.create_widgets()
        self.setObjectName('topbar')
        
    def create_widgets(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(8, 0, 8, 0)

        # Add link button with spacing
        add_link_btn = QPushButton(QIcon(self.other_methods.resource_path('images/link-outline.png')), "Add Link")
        add_link_btn.setObjectName('add-link-btn')
        add_link_btn.setIconSize(QSize(14, 14))
        add_link_btn.clicked.connect(self.open_link_box)
        add_link_btn.setFixedHeight(35)
        
        # Action buttons with proper spacing
        open_btn = QPushButton(QIcon(self.other_methods.resource_path('images/open-filled.png')), "Open")
        delete_btn = QPushButton(QIcon(self.other_methods.resource_path('images/trash-bin-filled.png')), "Delete")
        pause_btn = QPushButton(QIcon(self.other_methods.resource_path('images/pause-filled.png')), "Pause")
        resume_btn = QPushButton(QIcon(self.other_methods.resource_path('images/play-button-filled.png')), "Resume")
        restart_btn = QPushButton(QIcon(self.other_methods.resource_path('images/refresh-filled.png')), "Restart")

        # Set fixed height and style for all buttons
        for btn in [add_link_btn, open_btn, delete_btn, pause_btn, resume_btn, restart_btn]:
            btn.setFixedHeight(35)
            btn.setIconSize(QSize(14, 14))  # Smaller icon size
            btn.setStyleSheet("""
                QPushButton {
                    text-align: center;
                    padding-left: 8px;
                }
                QPushButton QIcon {
                    margin-right: 4px;
                }
            """)

        # Add buttons to layout
        actions_layout.addWidget(add_link_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(open_btn)
        actions_layout.addWidget(delete_btn)
        actions_layout.addWidget(pause_btn)
        actions_layout.addWidget(resume_btn)
        actions_layout.addWidget(restart_btn)

        # Connect action buttons
        open_btn.clicked.connect(lambda: self.app.do_action('Open'))
        delete_btn.clicked.connect(lambda: self.app.do_action('Delete'))
        pause_btn.clicked.connect(lambda: self.app.do_action('Pause'))
        resume_btn.clicked.connect(lambda: self.app.do_action('Resume'))
        restart_btn.clicked.connect(lambda: self.app.do_action('Restart'))

        main_layout.addLayout(actions_layout)
        self.setLayout(main_layout)

    def open_link_box(self):       
        self.app.add_link_top_window = AddLink(app=self.app, task_manager=self.task_manager)
        self.app.add_link_top_window.show()

class ContentArea(QFrame):
    def __init__(self):
        super().__init__()
        self.create_widgets()
        self.setObjectName("content-container")
        # Remove individual styling as it's handled by theme system
        
    def create_widgets(self):
        self.both_sides = QHBoxLayout()
        self.both_sides.setContentsMargins(0, 0, 0, 0)   
        self.content_area = QVBoxLayout()
        self.content_area.setContentsMargins(0, 0, 0, 0)    
        self.details_area = QVBoxLayout()
        self.details_area.setContentsMargins(0, 0, 0, 0)   
        self.both_sides.addLayout(self.content_area)

        self.file_info = FileInfoBox()
        self.details_area.addWidget(self.file_info)    
        
       
        self.both_sides.addLayout(self.details_area)
        self.setLayout(self.both_sides)
        self.details_opened = False

       

    def edit_fileinfo(self, thumbnail, filename, filepath, fileadded_at, filesize, fileaddress, filestatus):
        self.details_opened = True
        self.pixmap = QPixmap(f"{thumbnail}")  # Adjust image path
        self.pixmap = self.pixmap.scaledToWidth(100)        
        self.file_info.image_label.setPixmap(self.pixmap)

        self.file_info.file_name_label.setText(f"{filename}")
        self.file_info.added_at_label.setText(f"Added at: {fileadded_at}")
        self.file_info.path_label.setText(f"Path: {filepath}")
        self.file_info.link_label.setText(f'Address: <a href="{fileaddress}">{fileaddress}</a>')
        self.file_info.status_label.setText(f"Status: {filestatus}")
        self.file_info.size_label.setText(f"Total size: {filesize}")

    def update_fileinfo(self, thumbnail, filename, filestatus, filesize):
        if self.details_opened:
            self.pixmap = QPixmap(f"{thumbnail}")  # Adjust image path
            self.pixmap = self.pixmap.scaledToWidth(100)        
            self.file_info.image_label.setPixmap(self.pixmap)
            self.file_info.file_name_label.setText(f"{filename}")
            self.file_info.status_label.setText(f"Status: {filestatus}")
            self.file_info.size_label.setText(f"Total size: {filesize}")
        

class Sidebar(QFrame):
    def __init__(self, app):
        super().__init__()    
        self.main_app = app
        self.buttons = []
        self.other_methods = OtherMethods()
        self.network_status = QLabel()
        self.network_status.setObjectName('network-status')
        self.network_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.network_status.setFixedSize(40, 40)  # Match sidebar button size
        self.network_status.hide()  # Hidden by default
        self.check_network_status()
        self.create_widgets()
        self.setObjectName('sidebar')

    def add_icon_button(self, layout, icon_paths, text, index):
        btn = QPushButton(QIcon(self.other_methods.resource_path(icon_paths['outline'])), "")
        btn.setObjectName(f'{text}-btn')
        btn.clicked.connect(lambda: self.main_app.switch_page(index))
        layout.addWidget(btn)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.buttons.append((btn, icon_paths))
        return btn

    def create_widgets(self):       
        sidebar = QVBoxLayout()
        sidebar.setSpacing(4)  # Reduce spacing between buttons
        sidebar.setContentsMargins(0, 0, 0 ,0)  # Minimal margins
        
        # Add buttons at the top
        buttons_container = QVBoxLayout()
        buttons_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.add_icon_button(buttons_container, {"outline": "images/home-filled.png", "filled": "images/home-outline.png"}, "Home", 0)
        self.add_icon_button(buttons_container, {"outline": "images/about-filled.png", "filled": "images/about-outline.png"}, "About", 1)
        self.add_icon_button(buttons_container, {"outline": "images/settings-filled.png", "filled": "images/settings-outline.png"}, "Settings", 2)
        
        # Add buttons container to main sidebar
        sidebar.addLayout(buttons_container)
        
        # Add stretch to push network status to bottom
        sidebar.addStretch()
        
        # Add network status at bottom
        sidebar.addWidget(self.network_status)
        
        self.setLayout(sidebar)
        self.update_button_styles(0)  # Set initial active button

    def update_button_styles(self, active_index):
        for i, (btn, icon_paths) in enumerate(self.buttons):
            if i == active_index:
                btn.setIcon(QIcon(self.other_methods.resource_path(icon_paths['filled'])))
                btn.setProperty('active', True)
            else:
                btn.setIcon(QIcon(self.other_methods.resource_path(icon_paths['outline'])))
                btn.setProperty('active', False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def check_network_status(self):
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=1)
            self.network_status.hide()
        except OSError:
            # Set pixmap with specific size to match button icons
            pixmap = QIcon(self.other_methods.resource_path('images/no-connection.png')).pixmap(24, 24)
            self.network_status.setPixmap(pixmap)
            self.network_status.show()
        
class ActiveFileList(QScrollArea):
    def __init__(self, app):
        super().__init__()       
        self.setObjectName('scroll-area')
        self.app = app
        
        self.scroll_widget = QFrame()
        self.scroll_widget.setObjectName('scroll-widget')
        self.file_layout = QVBoxLayout(self.scroll_widget)
        self.file_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.file_layout.setContentsMargins(0, 0, 0, 0)
        self.file_layout.setSpacing(0)
        
        self.display_incomplete_downloads()
        self.display_complete_downloads()

        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded) 

        

    def display_incomplete_downloads(self):
        self.sorted_downloads = sorted(
            self.app.return_all_downloads().items(),
            key=lambda x: x[1]['modification_date'],
            reverse=True
        )
        for filename, detail in self.sorted_downloads:
            if 'finished' not in detail['status'].lower():
                self.add_file_widget(filename, detail)

    def display_complete_downloads(self):
        self.sorted_downloads = sorted(
            self.app.return_all_downloads().items(),
            key=lambda x: x[1]['modification_date'],
            reverse=True
        )
        for filename, detail in self.sorted_downloads:
            if 'finished' in detail['status'].lower():
                self.add_file_widget(filename, detail)

    def add_file_widget(self, filename, detail):
        if filename not in self.app.active_file_widgets:
            file_item = FileItemWidget(
                app=self.app,
                filename=filename,
                path=detail['path'],
                file_size=detail['filesize'],
                downloaded=detail['downloaded'],
                modified_date=detail['modification_date'],
                status=detail['status'],
                percentage=detail['percentage'],
                speed=" "
            )
            self.app.active_file_widgets[filename] = file_item          
            self.file_layout.insertWidget(0, file_item)


class FileItemWidget(QFrame):
    def __init__(self, app, filename, path, file_size, downloaded, status, percentage, speed, modified_date):
        super().__init__()
        self.app = app
        if 'downloading' in status.lower().strip() or 'resuming' in status.lower().strip():
            status = 'Paused.'

        self.is_selected = False
        self.file_path = path
        self.filename = filename
        self.other_methods = OtherMethods()
        file_size = self.other_methods.return_filesize_in_correct_units(file_size)
        downloaded = self.other_methods.return_filesize_in_correct_units(downloaded)
        self.image = self.other_methods.return_file_type(filename)

        # Create main layout
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 8, 12, 8)

        # Left section - Checkbox and icon
        left_section = QHBoxLayout()
        left_section.setSpacing(10)  # Adjust spacing between checkbox and icon
        
        self.checkbox = QCheckBox()
        self.checkbox.setFixedSize(18, 18)  # Keep the size but remove custom styling
        
        self.icon_label = QLabel()
        self.icon_label.setObjectName('icon-label')
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setPixmap(QIcon(self.other_methods.resource_path(self.image)).pixmap(20, 20))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        left_section.addWidget(self.checkbox)
        left_section.addWidget(self.icon_label)
        main_layout.addLayout(left_section)

        # Center section - File info
        info_section = QVBoxLayout()
        info_section.setSpacing(4)
        
        # Filename row
        self.filename_label = QLabel()
        self.filename_label.setObjectName('filename-label')
        metrics = QFontMetrics(self.filename_label.font())
        elided_filename = metrics.elidedText(filename, Qt.TextElideMode.ElideMiddle, 380)
        self.filename_label.setText(elided_filename)
        self.filename_label.setToolTip(filename)  # Show full name on hover
        info_section.addWidget(self.filename_label)

        # Status row
        status_layout = QHBoxLayout()
        status_layout.setSpacing(12)
        
        # Progress info
        progress_text = f"{downloaded} of {file_size}"
        if '---' in downloaded or '---' in file_size:
            progress_text = "Waiting..."
        
        self.download_info = QLabel(progress_text)
        self.download_info.setObjectName('info-label')
        
        # Status label with progress
        status_text = status
        status_type = 'downloading'  # default status
        if 'failed' in status.lower():
            status_text = "Failed"
            status_type = 'failed'
        elif 'finished' in status.lower() or 'completed' in status.lower():
            status_text = "Completed"
            status_type = 'completed'
        elif 'paused' in status.lower():
            status_text = "Paused"
            status_type = 'paused'
        
        self.download_status = QLabel(status_text)
        self.download_status.setObjectName('status-label')
        self.download_status.setProperty('download-status', status_type)  # Changed property name
        self.download_status.style().polish(self.download_status)
        
        # Speed label
        self.download_speed = QLabel(speed if speed and speed.strip() not in ['0', '', '---'] else '')
        self.download_speed.setObjectName('speed-label')
        
        status_layout.addWidget(self.download_info)
        status_layout.addWidget(self.download_status)
        status_layout.addWidget(self.download_speed)
        
        if 'failed' in status.lower():
            self.download_failed = QPushButton('Retry')
            self.download_failed.setObjectName('retry-btn')
            self.download_failed.clicked.connect(self.retry_downloading)
            status_layout.addWidget(self.download_failed)
        
        status_layout.addStretch()
        info_section.addLayout(status_layout)
        
        main_layout.addLayout(info_section, 1)

        # Right section - Date
        self.modified_label = QLabel(modified_date)
        self.modified_label.setObjectName('date-label')
        main_layout.addWidget(self.modified_label)

        self.setLayout(main_layout)
        self.apply_fonts()
        self.setup_styles()

        # Update status label with proper status and color
        status_type = 'downloading'
        if 'finished' in status.lower():
            status_type = 'completed'
        elif 'failed' in status.lower():
            status_type = 'failed'
        elif 'paused' in status.lower():
            status_type = 'paused'
            
        self.download_status.setProperty('download-status', status_type)
        self.download_status.style().unpolish(self.download_status)
        self.download_status.style().polish(self.download_status)

    def setup_styles(self):
        # Remove hardcoded styles since they're now handled by theme system
        pass

    def apply_fonts(self):
        self.apply_font(self.filename_label, 'Segoe UI', 13)
        self.apply_font(self.download_status, 'Segoe UI', 12)
        self.apply_font(self.download_info, 'Segoe UI', 12)
        self.apply_font(self.download_speed, 'Segoe UI', 12)
        self.apply_font(self.modified_label, 'Segoe UI', 12)

    def apply_font(self, widget, family, size, italic=False, bold=False, underline=False):
        font = QFont(family, size)
        font.setBold(bold)
        font.setUnderline(underline)
        font.setItalic(italic)
        widget.setFont(font)

    def update_widget(self, filename, status, size, downloaded, modified_date, speed, percentage):
        # Update filename with ellipsis in middle
        metrics = QFontMetrics(self.filename_label.font())
        elided_filename = metrics.elidedText(filename, Qt.TextElideMode.ElideMiddle, 380)
        self.filename_label.setText(elided_filename)
        self.filename_label.setToolTip(filename)  # Update tooltip

        # Convert file size and downloaded size to correct units
        other_methods = OtherMethods()
        file_size = other_methods.return_filesize_in_correct_units(size)
        downloaded = other_methods.return_filesize_in_correct_units(downloaded)
        self.filename_label.setText(filename)
        # Update file size and downloaded information
        self.download_info.setText(f"[ {downloaded} / {file_size} ]")
        # Update download status
        if 'finished' in status.lower():
            self.download_status.setText(f"{status} ")
            if hasattr(self, 'download_failed') and self.download_failed.isVisible():
                self.download_failed.setParent(None)
            self.download_speed.setText(f"")
        elif 'failed' in status.lower():           
            self.download_status.setText(f"Failed!") 
            if hasattr(self, 'download_failed'):
                self.download_failed.setParent(None)
                self.download_failed = QPushButton('Retry')
                self.download_failed.setObjectName('retry-btn')
                self.download_failed.clicked.connect(self.retry_downloading)
                self.layout().addWidget(self.download_failed)
            self.download_speed.setText(f"")
        else:
            if not '---' in percentage:
                self.download_status.setText(f"{status} {percentage}")
            else:
                self.download_status.setText(f"{status}")
        # Update download speed
        if speed.strip() == '0' or speed.strip() == '' or speed.strip() == '---':
            self.download_speed.setText(f"")
        else:
            self.download_speed.setText(f"{speed}")
        # Update modified date
        self.modified_label.setText(modified_date)

        # Update status type and styling
        status_type = 'downloading'  # default status
        if 'finished' in status.lower() or 'completed' in status.lower():
            status_type = 'completed'
        elif 'failed' in status.lower():
            status_type = 'failed'
        elif 'paused' in status.lower():
            status_type = 'paused'

        self.download_status.setProperty('download-status', status_type)  # Changed property name
        self.download_status.style().unpolish(self.download_status)
        self.download_status.style().polish(self.download_status)

        # Add checkmark image in white
        if hasattr(self, 'checkbox'):
            self.checkbox.style().unpolish(self.checkbox)
            self.checkbox.style().polish(self.checkbox)

    def retry_downloading(self):        
        filename_with_path = os.path.join(self.file_path, self.filename)
        self.app.resume_paused_file(filename_with_path)

    def update_filename(self, new_name):
        """Update the displayed filename in the widget"""
        metrics = QFontMetrics(self.filename_label.font())
        self.filename = new_name
        elided_filename = metrics.elidedText(new_name, Qt.TextElideMode.ElideMiddle, 380)
        self.filename_label.setText(elided_filename)
        self.filename_label.setToolTip(new_name)


class FileInfoBox(QFrame):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setObjectName('file-info-box')
        # Remove background color from stylesheet since it's handled by theme system
        self.setStyleSheet("""
            QLabel {
                padding: 10px 0;
                margin: 0;
            }
            #link {
                color: #48D1CC;
            }
        """)

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.addStretch()
        self.image_label = QLabel()
        
        self.main_layout.addWidget(self.image_label)
        info_layout = QVBoxLayout()        
        # File name
        self.file_name_label = QLabel("")
        info_layout.addWidget(self.file_name_label)        
        # Status
        self.status_label = QLabel("")
        info_layout.addWidget(self.status_label)        
        # Total size
        self.size_label = QLabel("")
        info_layout.addWidget(self.size_label)        
        # Added at
        self.added_at_label = QLabel("")
        info_layout.addWidget(self.added_at_label)        
        # File path
        self.path_label = QLabel("")
        info_layout.addWidget(self.path_label)
        # Add info layout to the main layout
        # File link
        self.link_label = QLabel('')
        self.link_label.setObjectName('link')
        self.link_label.setWordWrap(True) 
        info_layout.addWidget(self.link_label)


        
        self.link_label.setOpenExternalLinks(True)
        self.main_layout.addLayout(info_layout)
        self.main_layout.addStretch()
       



        # Set main layout
        self.setLayout(self.main_layout)
        self.setMinimumWidth(200)
        self.setMaximumWidth(300)



