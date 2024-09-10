import os,  asyncio , websockets, threading , json
from venaUtils import OtherMethods, Colors, Images
import storage, queue
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,QScrollArea,QLineEdit,
    QPushButton, QFrame, QStackedWidget
)
from venaWorker import Worker
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtCore import Qt, QPoint,QSize ,QThread
from addlink import AddLink
from qasync import asyncSlot
import pystray 
from taskManager import TaskManager


class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        storage.initiate_database()        
        self.setup_data()
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()
        self.bind_events()
        self.start_background_tasks()
        self.display_all_downloads_on_page()
        

    def setup_window(self):
        self.setWindowTitle('VenaApp')
        self.setWindowIcon(QIcon('images/main.ico'))
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
        self.about_page_opened = False
        self.settings_page_opened = False
        self.home_page_opened = True
        self.about_frame = None
        self.settings_frame = None
        self.previously_clicked_btn = None
        self.details_of_file_clicked = None
        self.more_actions = None
        self.running_tasks = {}
        self.file_widgets = {}
        self.last_mtime = None
        self.multi_file_picker_window = None
        self.files_to_be_downloaded = []   
        self.add_link_top_window = None
        self.progress_toplevels = {} 
        self.stray_icon = None
        

    def create_widgets(self):   
        self.create_app_container()    
        self.create_sidebar()
        self.create_content_area()
        self.create_file_list()
        self.create_file_list_order_labels()
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
        self.about_page = AboutPage()
        self.settings_page = SettingsPage()
        
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.about_page)
        self.stacked_widget.addWidget(self.settings_page)

    def setup_layout(self):
        self.content_area.content_area.addWidget(self.topbar)
        self.content_area.content_area.addWidget(self.file_list)
        self.content_area.content_area.addWidget(self.bottom_bar)
        self.body_layout.addWidget(self.sidebar)
        self.body_layout.addWidget(self.stacked_widget, 1)

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.sidebar.update_button_styles(index)

    def bind_events(self):
        # Event binding code here
        pass
    def closeEvent(self, event):      
        if self.add_link_top_window is not None:
            self.add_link_top_window.close()
        event.accept()

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
    def create_file_list_order_labels(self):
        pass
    # File list related methods
    def create_file_list(self):
        self.file_list = FileList()
        
    def create_bottom_bar(self):
        self.bottom_bar = BottomBar()

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
                            self.add_link_top_window = AddLink(url=url, filename=filename, task_manager=self.task_manager)                               
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
            'path': path
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
        else:
            self.add_new_file_widget(filename, status, size, date)

    def add_new_file_widget(self, filename, status, size, date):      
        file_item = FileItemWidget(
                filename=f"{filename}",
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
                filename=f"{filename}",
                file_size=f"{detail['filesize']}",
                downloaded=f"{detail['downloaded']}",
                modified_date=f"{detail['modification_date']}",
                status=detail['status'],
                percentage= detail['percentage'],
                speed=" "
            )           
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
            if name == f_name and not (details['status'] == 'completed.' or details['status'] == '100.0%'):
                size = details['filesize']
                link = details['url']
                downloaded = details['downloaded']           
                #asyncio.run_coroutine_threadsafe(self.task_manager.pause_downloads_fn(filename_with_path, size, link ,downloaded), self.task_manager.loop)
                if f_name in self.progress_toplevels:                  
                    
                    del self.progress_toplevels[f_name]


    def resume_paused_file(self, filename_with_path):
        f_name = os.path.basename(filename_with_path) 
        self.load_downloads_from_db()## reasign values to xengine_downloads to get updated values for downloaded chuck
        for name , details in self.xengine_downloads.items():
            if name == f_name and not (details['status'] == 'completed.' or details['status'] == '100.0%'):
                self.downloaded_chuck = 0
                try:
                    self.downloaded_chuck = int(details['downloaded'])                    

                except Exception as e:                   
                    self.downloaded_chuck = 0
                
                
                #asyncio.run_coroutine_threadsafe(self.task_manager.resume_downloads_fn(filename_with_path,  details['url'], self.downloaded_chuck), self.task_manager.loop)

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

            #if file_widget.winfo_exists():
                #file_widget.update_filename(new_name)

        


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
       pass

    def clear_displayed_files_widgets(self):
        for widget in self.file_widgets.items():
            pass
            #widget.destroy()
        self.file_widgets = {}
        
          

class TopBar(QFrame):
    def __init__(self, app):
        super().__init__()  
        self.app = app  
        self.task_manager = app.task_manager   
        self.create_widgets()
        
    def create_widgets(self):
        self.setObjectName('topbar')
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)        
        separator.setStyleSheet("color : #e2e7eb;")  # Set to black
        separator.setLineWidth(1)  #

        
        

        navigation_layout = QHBoxLayout() 
        open_linkbox_btn = QPushButton(QIcon('images/link-outline.png'), "") 
        open_linkbox_btn.setObjectName('open_linkbox_btn') 
        open_linkbox_btn.clicked.connect(self.open_link_box)

        active_btn = QPushButton(QIcon('images/active.png'), ' Active')
        active_btn.setIconSize(QSize(12, 12))
        active_btn.setObjectName('active-btn')       
        downloaded_btn = QPushButton(QIcon('images/complete.png'),' Downloaded')
        downloaded_btn.setIconSize(QSize(12, 12))
        downloaded_btn.setObjectName('downloaded-btn')
        main_layout.addLayout(navigation_layout)
        self.setLayout(main_layout)
        navigation_layout.addWidget(open_linkbox_btn)
        navigation_layout.addStretch()
        navigation_layout.addWidget(active_btn)
        navigation_layout.addWidget(downloaded_btn)
        navigation_layout.setContentsMargins(0, 0, 0, 0)
        navigation_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(separator)  

    def filter_all_downloads(self):        
        pass
    def filter_complete_downloads(self):        
        pass      

    def open_link_box(self):       
        self.app.add_link_top_window = AddLink(task_manager=self.task_manager)
        self.app.add_link_top_window.show()   
        pass

class BottomBar(QFrame):
    def __init__(self):
        super().__init__() 
        self.setObjectName('bottombar')
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
        btn = QPushButton(QIcon(icon_path), "")
        btn.setObjectName(f'{text}-btn')
        layout.addWidget(btn)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

class FileListOrderLabel():
    def __init__(self, master, app):
        super().__init__(master, fg_color='transparent', height=20)
        self.create_widgets()
    def create_widgets(self):
        pass

class ContentArea(QFrame):
    def __init__(self):
        super().__init__()
        
        self.create_widgets()        
    
    def create_widgets(self):
        self.content_area = QVBoxLayout()
        self.content_area.setContentsMargins(0, 0, 0, 0)    
        self.setObjectName("content-container")
        self.setLayout(self.content_area)
        
    def show_more_popup(self):
        pass
        

class Sidebar(QFrame):
    def __init__(self, app):
        super().__init__()    
        self.main_app = app
        self.buttons = []
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
        btn = QPushButton(QIcon(icon_paths['outline']), "")
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
                btn.setIcon(QIcon(icon_paths['filled']))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                    }
                """)
            else:
                btn.setIcon(QIcon(icon_paths['outline']))
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
        
class FileList(QScrollArea):
    def __init__(self):
        super().__init__()       
        self.setObjectName('scroll-area')
        # Create a widget to contain the layout
        self.scroll_widget = QFrame()
        self.scroll_widget.setStyleSheet('background-color: transparent;')
        self.file_layout = QVBoxLayout(self.scroll_widget)
        self.file_layout.setAlignment(Qt.AlignmentFlag.AlignTop)     
       
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded) 


        # Set the scrollable widget
        

class FileItemWidget(QFrame):
    def __init__(self, filename, file_size, downloaded,status, percentage, speed,modified_date):
        super().__init__()
        other_methods = OtherMethods()       
        file_size = other_methods.return_filesize_in_correct_units(file_size)
        downloaded = other_methods.return_filesize_in_correct_units(downloaded)
        image = other_methods.return_file_type(filename)
        self.setFixedHeight(60)
        # Create a horizontal layout to hold the icon and the text information
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(5, 0, 5, 0)

        icon_label = QLabel()
        icon_label.setObjectName('icon-label')
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(QIcon(image).pixmap(20, 20))

        main_layout.addWidget(icon_label)        

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        # Filename (top row)
        self.filename_label = QLabel(filename)
        text_layout.addWidget(self.filename_label)
        text_layout.setObjectName("filename")

        details_layout = QHBoxLayout()
        self.download_status = QLabel(f"{status}")
        self.download_status.setObjectName('status')
        self.download_info = QLabel(f"[ {downloaded} / {file_size} ]")
        self.download_info.setObjectName("info")
        self.download_speed = QLabel(f"{speed}")
        self.download_speed.setObjectName('speed')
        self.download_failed = QPushButton('retry')
        self.download_failed.setObjectName('retry')
        details_layout.addWidget(self.download_status)
        details_layout.addWidget(self.download_info)
        details_layout.addWidget(self.download_speed) 

        if 'failed' in status.lower():
            details_layout.addWidget(self.download_failed)       
        self.modified_label = QLabel(modified_date)
        self.modified_label.setObjectName('modified_date')
        self.modified_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        details_layout.addWidget(self.modified_label)

        text_layout.addLayout(details_layout)
        
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
                color: green;                           
            }
            #retry:hover{
                color: #48D1CC; 
            }
            
        """)
         
    def enterEvent(self, event):
        """Triggered when mouse enters the widget."""
        self.setStyleSheet("""
            FileItemWidget {
                background-color: #e0e0e0;  /* Light gray background on hover */
                border-radius: 5px;
            }
            #icon-label {
                max-width: 40px;
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
                color: green; 
            }
            #retry:hover{
                color: #48D1CC; 
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Triggered when mouse leaves the widget."""
        self.setStyleSheet("""
            FileItemWidget {
                background-color: transparent;  /* Restore background on leave */
                border-radius: 5px;
            }
            #icon-label {
                max-width: 40px;
            }
            #status{
                color: grey;
                max-width: 150px;
            }
            #info{
                color: grey;
                max-width: 150px;
            }
            #speed{
                color: grey;
                max-width: 70px;
            }
            #retry{
                max-width: 60px;
                color: green; 
            }
            #retry:hover{
                color: #48D1CC; 
            }
        """)
        super().leaveEvent(event)

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
        elif 'failed' in status.lower():
            self.download_status.setText(f"Failed!")
        else:
            self.download_status.setText(f"{status} {percentage}")

        # Update download speed
        if not speed == '0':
            self.download_speed.setText(f"{speed}")
        else:
            self.download_speed.setText(f"")
        # Update modified date
        self.modified_label.setText(modified_date)

    def mousePressEvent(self, event):
        """Triggered when the widget is clicked."""
        self.setStyleSheet("""
            FileItemWidget {
                background-color: #e2e7eb;  /* Darker gray on click */
                border-radius: 5px;
            }
            #icon-label {
                max-width: 40px;
            }
            #status{
                color: grey;
                max-width: 150px;
            }
            #info{
                color: grey;
                max-width: 150px;
            }
            #speed{
                color: grey;
                max-width: 70px;
            }
            #retry{
                max-width: 60px;
                color: green; 
            }
            #retry:hover{
                color: #48D1CC; 
            }
            
        """)
        super().mousePressEvent(event)

class CustomTitleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        self.setFixedHeight(40)
        
        
        # Create the layout for the title bar
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Window icon
        self.window_icon = QLabel()
        self.window_icon.setPixmap(QIcon('images/main.ico').pixmap(24, 24))
        self.window_icon.setStyleSheet("background-color: transparent; margin: 0 15px;")


        layout.addWidget(self.window_icon)

        self.back_btn = QPushButton(QIcon('images/left-chevron-dull.png'), "")
        self.back_btn.setObjectName("navigation-btn")
        self.forward_btn = QPushButton(QIcon('images/chevron-right-dull.png'), "")
        self.forward_btn.setObjectName("navigation-btn")

        layout.addWidget(self.back_btn)
        layout.addWidget(self.forward_btn)

        search_action = QAction(QIcon('images/search.png'), "", self)
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
        layout.addStretch()

        self.more_btn = QPushButton(QIcon('images/menu-outline.png'), "")
        self.more_btn.setIconSize(QSize(13, 13))
        self.more_btn.setStyleSheet("""
            QPushButton{
                background-color: transparent;
            }
            QPushButton:hover{
                icon : url('images/menu-filled.png')                
            }
        """)
        layout.addWidget(self.more_btn)

        # Minimize button
        self.minimize_button = QPushButton(QIcon('images/minus.png'), "")
        self.minimize_button.setIconSize(QSize(14, 14))
        self.minimize_button.setObjectName('window-maxi-min')
        self.minimize_button.setFixedSize(40, 40)
        self.minimize_button.clicked.connect(self.minimize_window)
        layout.addWidget(self.minimize_button)
        
        # Maximize button
        self.maximize_button = QPushButton(QIcon('images/maximize.png'), "")
        self.maximize_button.setIconSize(QSize(13, 13))
        self.maximize_button.setObjectName('window-maxi-min')
        self.maximize_button.setFixedSize(40, 40)
        self.maximize_button.clicked.connect(self.maximize_restore_window)
        layout.addWidget(self.maximize_button)
        
        # Close button
        self.close_button = QPushButton(QIcon('images/close.png'), "")
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

    def minimize_window(self):
        self.parent.showMinimized()

    def maximize_restore_window(self):
        if not self.is_maximized:
            self.parent.showMaximized()
            self.is_maximized = True
            self.maximize_button.setIcon(QIcon('images/squares.png'))
            self.maximize_button.setIconSize(QSize(12, 12))
        
        else:
            self.parent.showNormal()
            self.is_maximized = False
            self.maximize_button.setIcon(QIcon('images/maximize.png'))
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



class AboutPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        label = QLabel("About Page")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        label = QLabel("Settings Page")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)







