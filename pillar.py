import os,  asyncio , websockets, json, subprocess, platform
from venaUtils import OtherMethods, Colors, Images
import storage, queue
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,QScrollArea,QLineEdit,
    QPushButton, QFrame, QStackedWidget,QSystemTrayIcon,QMenu
)
from venaWorker import Worker, SetAppTray
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtCore import Qt, QPoint,QSize ,QThread, QEvent
from addlink import AddLink
from qasync import asyncSlot
from downloadingIndicator import DownloadIndicator
from taskManager import TaskManager
from settingsPage  import SettingsWindow
from aboutPage import AboutWindow
from fileNotFound_plus import DeletionConfirmationWindow, FileNotFoundDialog



class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        storage.initiate_database()        
        self.setup_data()
        self.setup_tray_icon()
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()
        self.other_methods.set_rounded_corners(self)
        self.start_background_tasks()
        
        

    def setup_window(self):
        self.setWindowTitle('VenaApp')
        self.setWindowIcon(QIcon(self.other_methods.resource_path('images/main.ico')))
        self.setGeometry(100, 100, 800, 540)
        self.center_window()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        


    def setup_styles(self):
        self.xe_images =Images()
        self.colors = Colors()
        self.setStyleSheet(self.other_methods.get_qss())

    def setup_data(self):
        self.xengine_downloads  = {}
        self.load_downloads_from_db()
        self.task_manager = TaskManager(self)
        self.other_methods = OtherMethods()
        self.update_queue = queue.Queue()
        self.show_less_popup = DownloadIndicator(self)
        self.other_methods.set_rounded_corners(self.show_less_popup)
        self.previously_clicked_btn = None
        self.details_of_file_clicked = None
        self.running_tasks = {}
        self.file_widgets = {}
        self.files_to_be_downloaded = []   
        self.add_link_top_window = None
        self.tray_icon = None
        

    def create_widgets(self):   
        self.create_app_container()    
        self.create_sidebar()
        self.create_content_area()
        self.create_file_list()
        self.create_complete_filelist()
        self.create_bottom_bar()
        self.create_top_bar()
        self.create_pages()

    def create_app_container(self):
        self.setContentsMargins(0, 0, 0, 0)
        central_widget = QWidget(self)
        central_widget.setObjectName("hero")
        central_widget.setContentsMargins(0, 0, 0, 0)
        title_bar = CustomTitleBar(self)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout = QHBoxLayout()
        self.main_layout.addWidget(title_bar)
        self.main_layout.addLayout(self.body_layout)        
        self.setCentralWidget(central_widget)
       

    def create_pages(self):
        self.stacked_widget = QStackedWidget()
        self.home_page = self.content_area
        self.about_page = AboutWindow()
        self.settings_page = SettingsWindow()
        
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.about_page)
        self.stacked_widget.addWidget(self.settings_page)

    def setup_layout(self):
        self.file_list_stacked_widget = QStackedWidget()
        self.file_list_stacked_widget.addWidget(self.complete_file_list)
        self.file_list_stacked_widget.addWidget(self.file_list)

        self.content_area.content_area.addWidget(self.topbar)
        self.content_area.content_area.addWidget(self.file_list_stacked_widget)
        self.content_area.content_area.addWidget(self.bottom_bar)
        self.body_layout.addWidget(self.sidebar)
        self.body_layout.addWidget(self.stacked_widget, 1)

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.sidebar.update_button_styles(index)

    def switch_filelist_page(self, index):
        self.file_list_stacked_widget.setCurrentIndex(index)
        self.topbar.update_button_styles(index)


    
    
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

    def create_complete_filelist(self):
        self.complete_file_list = CompleteFileList(self)
        
    def create_bottom_bar(self):
        self.bottom_bar = BottomBar(self)

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
                            # Create the top window only once
                            self.add_link_top_window = AddLink(app=self, url=url, filename=filename, task_manager=self.task_manager)                               
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
            id, filename, address, filesize, downloaded, status, percentage,modification_date, path = download
            self.xengine_downloads[filename] = {
                'url': address,
                'status': status,
                'downloaded': downloaded,
                'filesize': filesize,
                'modification_date': modification_date,
                'path': path,
                'percentage': percentage
            }

    # File management methods
    def add_download_to_list(self, filename, address, path, date):        
        self.xengine_downloads[filename] = {
            'url': address,
            'status': 'Waiting..',
            'downloaded': '---',
            'filesize': '---',
            'modification_date': date,
            'path': path,
            'percentage' : '0%'
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
        if filename in self.file_widgets:
            self.file_widgets[filename].update_widget(filename, status,size, downloaded, date, speed, percentage)
            if 'Finished' in status :
                self.show_less_popup.download_completed()
            elif "failed" in status.lower():
                self.show_less_popup.download_failed()
        else:
            self.add_new_file_widget(filename, status, size, date)

        

    def add_new_file_widget(self, filename, status, size, date): 
        path = self.xengine_downloads[filename]['path']     
        file_item = FileItemWidget(
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
        self.file_widgets[filename] = file_item 
        self.file_list.file_layout.insertWidget(0, file_item)
       
    
    def display_all_downloads_on_page(self):
        for filename, detail in self.return_all_downloads().items():
           
            file_item = FileItemWidget(
                app = self,
                filename=f"{filename}",
                path = detail['path'],
                file_size=f"{detail['filesize']}",
                downloaded=f"{detail['downloaded']}",
                modified_date=f"{detail['modification_date']}",
                status=detail['status'],
                percentage= detail['percentage'],
                speed=" "
            ) 
            self.file_widgets[filename] =file_item          
            self.file_list.file_layout.addWidget(file_item)
           


    def display_complete_downloads_on_page(self):
       
        for filename, detail in self.return_all_downloads().items():
            if filename  in self.file_widgets  and  detail['status'] == 'completed.':
                pass
            elif filename in self.file_widgets and  self.file_widgets[filename].winfo_exists():
                pass
            else:
                if detail['status'] == 'completed.':
                    self.add_new_file_widget(filename, detail['status'], detail['filesize'], detail['modification_date'])


    # File operations
    def pause_downloading_file(self, filename_with_path):
        f_name = os.path.basename(filename_with_path)
        self.load_downloads_from_db()## reasign values to xengine_downloads to get updated values for downloaded chuck
        for name , details in self.xengine_downloads.items():
            if name == f_name and not  ( 'Finished' in details['status']or details['status'] == '100.0%'):
                size = details['filesize']
                link = details['url']
                downloaded = details['downloaded']           
                #asyncio.run_coroutine_threadsafe(self.task_manager.pause_downloads_fn(filename_with_path, size, link ,downloaded), self.task_manager.loop)
                
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
        for name , details in self.xengine_downloads.items():
            if name == f_name and not ('Finished' in details['status'] or details['percentage'] == '100.0%'):
                self.downloaded_chuck = safe_int(details.get('downloaded', 0))
                self.file_size = safe_int(details.get('filesize', 0))               
    
                asyncio.create_task(self.task_manager.resume_downloads_fn(filename_with_path,  details['url'], self.downloaded_chuck))
        
    def update_filename(self, old_name, new_name):     
        pathless_old_name = os.path.basename(old_name)
        pathless_new_name = os.path.basename(new_name)

        if pathless_old_name in self.xengine_downloads:
            value = self.xengine_downloads.pop(pathless_old_name)

            self.xengine_downloads[pathless_new_name] = value
                      
        if pathless_old_name in self.file_widgets:
            value = self.file_widgets.pop(pathless_old_name) 

            self.file_widgets[pathless_new_name] = value

            file_widget = self.file_widgets[pathless_new_name]

            if file_widget.isVisible():
                file_widget.update_filename(new_name)

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
        widget = self.file_widgets[filename]         
        self.file_list.file_layout.removeWidget(widget)
        widget.hide()
        self.previously_clicked_btn = None
        self.details_of_file_clicked = None
       
       

    def clear_displayed_files_widgets(self):
        for widget in self.file_widgets.items():
            pass
           
        self.file_widgets = {}
        
          

class TopBar(QFrame):
    def __init__(self, app):
        super().__init__()  
        self.app = app  
        self.task_manager = app.task_manager 
        self.other_methods = OtherMethods()  
        self.buttons = []
        self.create_widgets()
        self.setStyleSheet("""
            #active-btn, #downloaded-btn{
                background-color: #e2e7eb;
                width: 110px;
                height: 30px;
                border-radius: 5px;
                margin: 5px 5px 0  0;
            }
           

        """)
        
    def create_widgets(self):
        self.setObjectName('topbar')
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)        
        separator.setStyleSheet("color : #e2e7eb;")  # Set to black
        separator.setLineWidth(1)  #
        navigation_layout = QHBoxLayout() 
        open_linkbox_btn = QPushButton(QIcon(self.other_methods.resource_path('images/link-outline.png')), "") 
        open_linkbox_btn.setObjectName('open_linkbox_btn') 
        open_linkbox_btn.clicked.connect(self.open_link_box)
        
        main_layout.addLayout(navigation_layout)
        self.setLayout(main_layout)
        navigation_layout.addWidget(open_linkbox_btn)
        navigation_layout.addStretch()
        self.add_icon_button(navigation_layout, {"outline": "images/active.png", "filled": "images/inactive.png"}, "Active", 0)
        self.add_icon_button(navigation_layout, {"outline": "images/complete-active.png", "filled": "images/complete.png"}, "Downloaded", 1)
        navigation_layout.setContentsMargins(0, 0, 0, 0)
        navigation_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(separator)  
        self.update_button_styles(1)
    

    def open_link_box(self):       
        self.app.add_link_top_window = AddLink(app=self.app, task_manager=self.task_manager)
        self.app.add_link_top_window.show() 

    def add_icon_button(self, layout, icon_paths, text, index):
        btn = QPushButton(QIcon(self.other_methods.resource_path(icon_paths['outline'])), f" {text}")
        btn.setObjectName(f'{text.lower()}-btn')
        btn.setIconSize(QSize(12, 12))
        btn.clicked.connect(lambda: self.app.switch_filelist_page(index))
        layout.addWidget(btn)
        self.buttons.append((btn, icon_paths))
        return btn  

    def update_button_styles(self, active_index):
        for i, (btn, icon_paths) in enumerate(self.buttons):
            if i == active_index:
                btn.setIcon(QIcon(self.other_methods.resource_path(icon_paths['outline'])))
                btn.setStyleSheet("""
                    QPushButton {
                       background-color: #48D1CC;
                    }
                """)
            else:
                btn.setIcon(QIcon(self.other_methods.resource_path(icon_paths['filled'])))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e2e7eb;
                    }
                    
                """)

class BottomBar(QFrame):
    def __init__(self, app):
        super().__init__()
        self.other_methods = OtherMethods() 
        self.app = app
        self.setObjectName('bottombar')
        #app.previously_clicked_btn = None
        #app.details_of_file_clicked = None
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)        
        separator.setStyleSheet("color : #e2e7eb;")  # Set to black
        separator.setLineWidth(1)  #
        main_layout.addWidget(separator)       
        navigation_layout2 = QHBoxLayout()
        navigation_layout2.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(navigation_layout2)
        self.setLayout(main_layout)
        self.add_icon_button_to_actions_bar(navigation_layout2, "images/open-outline.png", "Open")
        self.add_icon_button_to_actions_bar(navigation_layout2, "images/trash-bin-outline.png", "Delete")
        self.add_icon_button_to_actions_bar(navigation_layout2, "images/pause-outline.png", "Pause")
        self.add_icon_button_to_actions_bar(navigation_layout2, "images/play-button-outline.png", "Resume")
        self.add_icon_button_to_actions_bar(navigation_layout2, "images/refresh-outline.png", "Restart")

    def add_icon_button_to_actions_bar(self, layout, icon_path, text):
        btn = QPushButton(QIcon(self.other_methods.resource_path(icon_path)), "")
        btn.setObjectName(f'{text}-btn')
        btn.clicked.connect(lambda : self.do_action(text))
        layout.addWidget(btn)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)


    def do_action(self, text):
        if self.app.details_of_file_clicked:
            f_name , path = self.app.details_of_file_clicked 
            path_and_file = os.path.join(path, f_name)
            if text.strip() == 'Open':
                if not os.path.exists(path_and_file):
                    self.file_not_found_popup = FileNotFoundDialog(self.app, f_name)
                    self.file_not_found_popup.show()
                        
                else:
                    system_name = platform.system()   
                
                    if system_name == 'Windows':
                        os.startfile(path_and_file)

                    elif system_name == 'Linux':
                        subprocess.Popen(["xdg-open", path_and_file])
                pass ## open file
            elif text.strip() == 'Delete':              

                file_to_delete = os.path.join(path, f_name)
                self.confirm = DeletionConfirmationWindow(self.app, f_name, file_to_delete)
                self.confirm.show()
                    
            elif text.strip() == 'Pause':
                pass ## pause downloading
            elif text.strip() == 'Resume':
                pass ## resume downloading
            elif text.strip() == 'Restart':
                pass ### restart donwload
            
       



class ContentArea(QFrame):
    def __init__(self):
        super().__init__()
        
        self.create_widgets()        
    
    def create_widgets(self):
        self.content_area = QVBoxLayout()
        self.content_area.setContentsMargins(0, 0, 0, 0)    
        self.setObjectName("content-container")
        self.setLayout(self.content_area)
        
    

class Sidebar(QFrame):
    def __init__(self, app):
        super().__init__()    
        self.main_app = app
        self.buttons = []
        self.other_methods = OtherMethods()
        self.create_widgets()

        self.setStyleSheet("""
            #sidebar {
                background-color: #e2e7eb;
            }
            QPushButton {
                border-radius: 10px;
                margin: 0;
                width: 40px;
                height: 40px;
                margin-bottom: 10px;
            }
        """)

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
        sidebar.setSpacing(0)
        sidebar.setContentsMargins(5, 5, 5, 5)
        self.add_icon_button(sidebar, {"outline": "images/home-outline.png", "filled": "images/home-filled.png"}, "Home", 0)
        self.add_icon_button(sidebar, {"outline": "images/about-outline.png", "filled": "images/about-filled.png"}, "About", 1)
        self.add_icon_button(sidebar, {"outline": "images/settings-outline.png", "filled": "images/settings-filled.png"}, "Settings", 2)
        self.setLayout(sidebar)
        self.setObjectName('sidebar')
        self.setFixedWidth(50)
        self.update_button_styles(0)  # Set initial active button

    def update_button_styles(self, active_index):
        for i, (btn, icon_paths) in enumerate(self.buttons):
            if i == active_index:
                btn.setIcon(QIcon(self.other_methods.resource_path(icon_paths['filled'])))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                    }
                """)
            else:
                btn.setIcon(QIcon(self.other_methods.resource_path(icon_paths['outline'])))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #e2e7eb;
                    }}
                    QPushButton:hover {{
                        background-color: white;
                    }}
                    QPushButton:hover {{
                        icon: url('{icon_paths['filled']}');
                    }}
                """)
        
class ActiveFileList(QScrollArea):
    def __init__(self, app):
        super().__init__()       
        self.setObjectName('scroll-area')
        self.app = app
        # Create a widget to contain the layout
        self.scroll_widget = QFrame()
        self.scroll_widget.setStyleSheet('background-color: transparent;')
        self.file_lay = QVBoxLayout(self.scroll_widget)
        self.file_lay.setAlignment(Qt.AlignmentFlag.AlignTop)     
        self.display_incomplete_downloads_on_page()

        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded) 

    def display_incomplete_downloads_on_page(self):
        for filename, detail in self.app.return_all_downloads().items():
            if 'finished' not in detail['status'].lower():
                file_item = FileItemWidget(
                    app = self.app,
                    filename=f"{filename}",
                    path = detail['path'],
                    file_size=f"{detail['filesize']}",
                    downloaded=f"{detail['downloaded']}",
                    modified_date=f"{detail['modification_date']}",
                    status=detail['status'],
                    percentage= detail['percentage'],
                    speed=" "
                ) 
                self.app.file_widgets[filename] = file_item          
                self.file_lay.addWidget(file_item)

class CompleteFileList(QScrollArea):
    def __init__(self, app):
        super().__init__()       
        self.setObjectName('scroll-area')
        self.app = app

        self.scroll_widget = QFrame()
        self.scroll_widget.setStyleSheet('background-color: transparent;')
        self.file_layout = QVBoxLayout(self.scroll_widget)
        self.file_layout.setAlignment(Qt.AlignmentFlag.AlignTop)     
        self.display_complete_downloads_on_page()
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded) 
      


        # Set the scrollable widget
    def display_complete_downloads(self):
        for filename, detail in self.app.return_all_downloads().items():
            if 'finished' in detail['status'].lower():
                self.add_file_widget(filename, detail)

    def add_file_widget(self, filename, detail):
        if filename not in self.app.file_widgets:
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
            self.app.file_widgets[filename] = file_item
            self.file_layout.addWidget(file_item)
           


class FileItemWidget(QFrame):
    def __init__(self,app, filename,path, file_size, downloaded,status, percentage, speed,modified_date):
        super().__init__()
        self.app = app

        self.is_selected = False
        self.file_path = path
        self.filename  = filename
        self.other_methods = OtherMethods()       
        file_size = self.other_methods.return_filesize_in_correct_units(file_size)
        downloaded = self.other_methods.return_filesize_in_correct_units(downloaded)
        self.image = self.other_methods.return_file_type(filename)
        self.setFixedHeight(60)
        # Create a horizontal layout to hold the icon and the text information
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(5, 0, 5, 0)

        self.icon_label = QLabel()
        self.icon_label.setObjectName('icon-label')
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setPixmap(QIcon(self.other_methods.resource_path(self.image)).pixmap(20, 20))

        main_layout.addWidget(self.icon_label)        

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        # Filename (top row)
        self.filename_label = QLabel(filename)
        text_layout.addWidget(self.filename_label)
        text_layout.setObjectName("filename")

        self.details_layout = QHBoxLayout()
        self.download_status = QLabel(f"{status}")
        self.download_status.setObjectName('status')
        self.download_info = QLabel(f"[ {downloaded} / {file_size} ]")
        self.download_info.setObjectName("info")
        self.download_speed = QLabel(f"{speed}")
        self.download_speed.setObjectName('speed')
        self.download_failed = QPushButton('retry')
        self.download_failed.setObjectName('retry')
        
        if 'failed' in status.lower():
            self.download_status.setText("Failed!")
        self.details_layout.addWidget(self.download_status)
        self.details_layout.addWidget(self.download_info)
        self.details_layout.addWidget(self.download_speed) 
           

        if 'failed' in status.lower():
            self.details_layout.addWidget(self.download_failed) 
            self.download_failed.clicked.connect(self.retry_downloading)  
            
             
        self.modified_label = QLabel(modified_date)
        self.modified_label.setObjectName('modified_date')
        self.modified_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.details_layout.addWidget(self.modified_label)

        text_layout.addLayout(self.details_layout)
        
        main_layout.addLayout(text_layout)

        self.apply_font(self.filename_label, 'Lato', 10)
        self.apply_font(self.download_status, 'Arial', 10)
        self.apply_font(self.download_info, 'Arial', 9)
        self.apply_font(self.download_speed, 'Exo 2', 10)
        self.apply_font(self.download_failed, 'Arial', 9, underline=True, italic=True)
        
        self.setLayout(main_layout)

        self.setStyleSheet("""
            FileItemWidget {
                background-color: transparent;
                border-radius: 5px;
                height: 60px;
                margin: 0;
            }
            #icon-label {
                max-width: 40px;
            }
            #filename{
                background-color: transparent;
            }
            #status{               
                max-width: 150px;
                color: grey;
            }
            #info{                
                max-width: 150px;
                color: grey;
            }
            #speed{               
                max-width: 70px;
                color: grey;
            }
            #retry{
                max-width: 60px;
                color: orange;                           
            }
            #retry:hover{
                color: #48D1CC; 
            }
            
        """)
         



    def enterEvent(self, event):
        """Triggered when mouse enters the widget."""
        if not self.is_selected:
            self.setStyleSheet(self.get_hover_style())
        super().enterEvent(event)
    def leaveEvent(self, event):
        """Triggered when mouse leaves the widget."""
        if not self.is_selected:
            self.setStyleSheet(self.get_normal_style())
        super().leaveEvent(event)
    def mousePressEvent(self, event):
        """Triggered when the widget is clicked."""
        if self.app.previously_clicked_btn:
            self.app.previously_clicked_btn.is_selected = False
            self.app.previously_clicked_btn.setStyleSheet(self.get_normal_style())
        
        self.is_selected = True
        self.setStyleSheet(self.get_selected_style())
        self.app.previously_clicked_btn = self
        self.app.details_of_file_clicked = (
            self.filename,
            self.file_path,
            # Add other details as needed
        )
        super().mousePressEvent(event)
    def get_normal_style(self):
        return """
            FileItemWidget {
                background-color: transparent;
                border-radius: 5px;
            }
            #icon-label {
                max-width: 40px;
            }
            #status {
                color: grey;
                max-width: 150px;
            }
            #info {
                color: grey;
                max-width: 150px;
            }
            #speed {
                color: grey;
                max-width: 70px;
            }
            #retry {
                max-width: 60px;
                color: orange;
            }
            #retry:hover {
                color: #48D1CC;
            }
        """

    def get_hover_style(self):
        return """
            FileItemWidget {
                background-color: #e0e0e0;
                border-radius: 5px;
            }
            #icon-label {
                max-width: 40px;
            }
            #status {
                color: grey;
                max-width: 150px;
            }
            #info {
                color: grey;
                max-width: 150px;
            }
            #speed {
                color: grey;
                max-width: 70px;
            }
            #retry {
                max-width: 60px;
                color: orange;
            }
            #retry:hover {
                color: #48D1CC;
            }
        """

    def get_selected_style(self):
        return """
            FileItemWidget {
                background-color: #e2e7eb;
                border-radius: 5px;
            }
            #icon-label {
                max-width: 40px;
            }
            #status {
                color: grey;
                max-width: 150px;
            }
            #info {
                color: grey;
                max-width: 150px;
            }
            #speed {
                color: grey;
                max-width: 70px;
            }
            #retry {
                max-width: 60px;
                color: grey;
            }
            #retry:hover {
                color: #e0e0e0;
            }
        """
    
    def update_filename(self, new_name):
        new_name = os.path.basename(new_name)
        self.filename_label.setText(new_name)
        self.image = self.other_methods.return_file_type(new_name)
        self.icon_label.setPixmap(QIcon(self.other_methods.resource_path(self.image)).pixmap(20, 20))

    def apply_font(self, widget, family,size, italic = False, bold=False, underline=False):
        font = QFont(family, size)
        font.setBold(bold)
        font.setUnderline(underline)
        font.setItalic(italic)
        widget.setFont(font)

    def update_widget(self, filename, status ,size, downloaded, modified_date, speed, percentage):
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
            if self.download_failed.isVisible():
                self.details_layout.removeWidget(self.download_failed)   
        elif 'failed' in status.lower():
            self.download_status.setText(f"Failed!") 
            self.details_layout.removeWidget(self.modified_label)                       
            self.details_layout.addWidget(self.download_failed) 
            self.details_layout.addWidget(self.modified_label)
            self.download_failed.clicked.connect(self.retry_downloading)
        else:
            self.download_status.setText(f"{status} {percentage}")
        # Update download speed
        if not speed == '0':
            self.download_speed.setText(f"{speed}")
        else:
            self.download_speed.setText(f"")
        # Update modified date
        self.modified_label.setText(modified_date)

    def retry_downloading(self):        
        filename_with_path = os.path.join(self.file_path, self.filename )
        self.app.resume_paused_file(filename_with_path)


    

class CustomTitleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        self.setFixedHeight(40)
        
        self.other_methods = OtherMethods()
        # Create the layout for the title bar
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Window icon
        self.window_icon = QLabel()
        self.window_icon.setPixmap(QIcon(self.other_methods.resource_path('images/main.ico')).pixmap(24, 24))
        self.window_icon.setStyleSheet("background-color: transparent; margin: 0 15px;")


        layout.addWidget(self.window_icon)

        self.back_btn = QPushButton(QIcon(self.other_methods.resource_path('images/left-chevron-dull.png')), "")
        self.back_btn.setObjectName("navigation-btn")
        self.forward_btn = QPushButton(QIcon(self.other_methods.resource_path('images/chevron-right-dull.png')), "")
        self.forward_btn.setObjectName("navigation-btn")

        layout.addWidget(self.back_btn)
        layout.addWidget(self.forward_btn)

        search_action = QAction(QIcon(self.other_methods.resource_path('images/search.png')), "", self)
        text_input = QLineEdit()
        text_input.addAction(search_action)
        
        text_input.setPlaceholderText("Search")
       
        layout.addWidget(text_input)


        text_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid white;
                border-radius: 5px;
                background-color: white;
                color: #2c3e50;
                height: 25px;
                width: 400px;    
                margin-left: 20px;                             
            }
            QLineEdit:focus {
                border-color:  #48D1CC;
            }
        """)

        
        # Window title
        
        
        # Add spacer to push the buttons to the right
        

        self.more_btn = QPushButton()
        
        self.more_btn.setStyleSheet("""
             QPushButton::menu-indicator {
                image: none;  /* Hide the dropdown arrow */
                padding: 0;
                icon : none;
                margin: 0;
                height : 0;
                width: 0;
            }
            QPushButton{
                background-color: transparent;
                margin-left: 10px;
                padding: 0 5px;
            }
            QPushButton:hover{
                icon : url('images/menu-filled.png') 
                           
            }
           
        """)

        # Create the dropdown menu
        self.menu = QMenu(self)
        #self.menu.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Add menu items with icons
        add_action = self.menu.addAction(QIcon("images/add-link.png"), "Add Multiple Links")
        clear_action = self.menu.addAction(QIcon("images/clean.png"), "Clear Finished")
        delete_action = self.menu.addAction(QIcon("images/remove.png"), "Delete Selected")

        

        add_action.triggered.connect(self.add_links)
        clear_action.triggered.connect(self.clear_finished)
        delete_action.triggered.connect(self.delete_selected)
       

        # Set the menu for the dropdown button
        self.more_btn.setMenu(self.menu)
        self.more_btn.setIcon(QIcon(self.other_methods.resource_path('images/menu-outline.png')),)
        self.more_btn.setIconSize(QSize(13, 13))
        layout.addWidget(self.more_btn)

        layout.addStretch()

        # Minimize button
        self.minimize_button = QPushButton(QIcon(self.other_methods.resource_path('images/minus.png')), "")
        self.minimize_button.setIconSize(QSize(14, 14))
        self.minimize_button.setObjectName('window-maxi-min')
        self.minimize_button.setFixedSize(40, 40)
        self.minimize_button.clicked.connect(self.minimize_window)
        layout.addWidget(self.minimize_button)
        
        # Maximize button
        self.maximize_button = QPushButton(QIcon(self.other_methods.resource_path('images/maximize.png')), "")
        self.maximize_button.setIconSize(QSize(13, 13))
        self.maximize_button.setObjectName('window-maxi-min')
        self.maximize_button.setFixedSize(40, 40)
        self.maximize_button.clicked.connect(self.maximize_restore_window)
        layout.addWidget(self.maximize_button)
        
        # Close button
        self.close_button = QPushButton(QIcon(self.other_methods.resource_path('images/close.png')), "")
        self.close_button.setIconSize(QSize(11, 11))
        self.close_button.setObjectName('window-close')
        self.close_button.setFixedSize(40, 40)
        self.close_button.clicked.connect(self.close_window)
        layout.addWidget(self.close_button)        
        self.is_maximized = False
        self.setStyleSheet("""
            *{
                background-color: #e2e7eb;                          
            }
            
            #navigation-btn{
                background-color: transparent;
            }
            #window-maxi-min{
                background-color: transparent; 
                border: none;
                
            }
            #window-maxi-min:hover{
                background-color: #F1F1F1;
            }
            #window-close{
                background-color: transparent; 
                border: none; 
                padding-right: 15px; 
                padding-left: 15px;
            }
            #window-close:hover{
                background-color: red;
            }
            

        """)
        self.menu.setStyleSheet("""
            QMenu {
                width: 200px;
                padding: 5px;
                height: 150px;
                border-radius: 5px;
                background-color: #48D1CC;
            }
            QMenu::item {
                padding: 5px 20px 5px 25px;
                border-radius: 5px;
                width: 145px;
                height: 25px;
                background-color:  #e6e6e6;
                margin-bottom: 10px;
               
            }
            QMenu::item:selected {
                background-color: #e2e7eb;
            }
            QMenu::icon {
                position: absolute;
                left: 10px;
                top: 5px;
            }
        """)
    def minimize_window(self):
        self.parent.showMinimized()

    def maximize_restore_window(self):
        if not self.is_maximized:
            self.parent.showMaximized()
            self.is_maximized = True
            self.maximize_button.setIcon(QIcon(self.other_methods.resource_path('images/squares.png')))
            self.maximize_button.setIconSize(QSize(12, 12))
        
        else:
            self.parent.showNormal()
            self.is_maximized = False
            self.maximize_button.setIcon(QIcon(self.other_methods.resource_path('images/maximize.png')))
            self.maximize_button.setIconSize(QSize(13, 13))

    def close_window(self):
        self.parent.close()

    def mousePressEvent(self, event):
        """Override to capture the position of the window when the user clicks."""
        self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Override to move the window when the user drags the title bar."""
        delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
        self.parent.move(self.parent.x() + delta.x(), self.parent.y() + delta.y())
        self.old_pos = event.globalPosition().toPoint()

    def add_links(self):
        print("Add Links selected")

    def clear_finished(self):
        print("Clear Finished selected")

    def delete_selected(self):
        print("Delete Selected selected")


