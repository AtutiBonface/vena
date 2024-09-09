import sys, os , re
from PyQt6.QtWidgets import QFileDialog, QPushButton,QFrame,QLineEdit,QApplication, QWidget, QVBoxLayout,QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from settings import AppSettings
from pathlib import Path
from urllib.parse import urlparse , urlunparse ,urlsplit
import asyncio
class AddLink(QWidget):
    def __init__(self, url=None ,filename=None, bjdm =None):
        super().__init__()
        self.setWindowTitle("Download file")
        self.setWindowIcon(QIcon('images/main.ico'))
        self.setGeometry(150, 150, 400, 220)
        self.center_window()
        self.app_settings = AppSettings()
        self.xdm_instance = bjdm
        self.download_path = str(self.app_settings.default_download_path)

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
        

        address_frame = QFrame()
        address_frame.setObjectName("input-label")
        address_layout = QHBoxLayout()
        address_layout.setContentsMargins(5,0,25,0)
        address_label = QLabel('Address')
        address_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        address_label.setObjectName('label')
        self.address_entry = QLineEdit()
        self.address_entry.setText(url)
        self.address_entry.setObjectName('entry')
        self.address_entry.textChanged.connect(self.getInputValue)
        address_layout.addWidget(address_label)
        address_layout.addWidget(self.address_entry)
        address_frame.setLayout(address_layout)

        filename_frame = QFrame()
        filename_frame.setObjectName("input-label")
        filename_layout = QHBoxLayout()
        filename_layout.setContentsMargins(5,0,25,0)
        filename_label = QLabel('File')
        filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filename_label.setObjectName('label')
        self.filename_entry = QLineEdit()
        self.filename_entry.setText(filename)
        self.filename_entry.setObjectName('entry')
        filename_layout.addWidget(filename_label)
        filename_layout.addWidget(self.filename_entry)
        filename_frame.setLayout(filename_layout)

        savein_frame = QFrame()
        savein_frame.setObjectName("input-label")
        savein_layout = QHBoxLayout()
        savein_layout.setContentsMargins(5,0,25,0)
        savein_label = QLabel('Save in')
        savein_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        savein_label.setObjectName("label")
        self.savein_entry = QLineEdit()
        self.savein_entry.setText(self.download_path)
        self.savein_entry.setObjectName("entry")
        savein_more_btn = QPushButton(QIcon('images/change.png'), "")
        savein_more_btn.setObjectName("change-path-btn")
        savein_more_btn.clicked.connect(self.openDownloadToFolder)
        savein_layout.addWidget(savein_label)
        savein_layout.addWidget(self.savein_entry)
        savein_layout.addWidget(savein_more_btn)
        savein_frame.setLayout(savein_layout)


        download_button_frame = QFrame()
        download_button_layout = QHBoxLayout()        
        download_button = QPushButton(QIcon('images/downloading.png'),' Download')
        download_button.setIconSize(QSize(13, 13))
        download_button.setObjectName('submit-btn')        
        download_button.setMaximumWidth(120)
        download_button.clicked.connect(self.add_task_to_downloads)
        download_button_frame.setLayout(download_button_layout)
        download_button_layout.addWidget(download_button)
        
        main_layout.addWidget(self.warning_label)
        main_layout.addWidget(address_frame)
        main_layout.addWidget(filename_frame)
        main_layout.addWidget(savein_frame)
        ##main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        main_layout.addWidget(download_button_frame)

        

        self.setLayout(main_layout)
        self.setStyleSheet("""
            AddLink{
                background-color: #e2e7eb;
            }
            #input-label{
                background-color : transparent;
                height: 30px;
                margin: 0;
                padding: 0;
            }
            #label{
                background-color : transparent;
                height: 30px;
                min-width: 50px;
                padding : 0;
                font-weight: bold;
            }
            #entry{
                height: 30px;
                border: none;
                border-radius: 3px;               
                
            }
            #change-path-btn{
                height: 30px;
                border: none;
                border-radius: 3px;  
                background-color : #48D1CC;
                width: 30px;
            }
            #submit-btn{
                height: 40px;
                border: none;
                border-radius: 3px;  
                background-color : #48D1CC;
                width: 70px;
                margin: 0, 0, 20px, 10px;
                color: white;
                font-weight: bold;
            }
            #warning-label{
                height: 30px;
                margin: 0;
                padding:0;
            }
        """)
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

            self.filename_entry.setText(filename)
        else:
            custom_name = link.split('//')[1].split('.')[0]
            self.filename_entry.setText(custom_name)
    def sanitize_filename(self, filename):
        # Remove any invalid characters for filenames on most operating systems
        return re.sub(r'[\\/*?:"<>|]', "", filename)


    def add_task_to_downloads(self):
        link = self.address_entry.text()
        filename = self.filename_entry.text() 

       
        if not urlparse(link).scheme:
            link = f'http://{link}'

        if not urlparse(link).netloc:
            self.warning_label.setText('Insert correct address!')
            self.warning_label.setStyleSheet("color : brown;")


        
        else:
            url_parsed = urlparse(link)

            if '.' in link:
                
                initial_filename = self.filename_entry.text()
                name, extension = os.path.splitext(initial_filename)

                
                if not name:
                    self.warning_label.setText('No file name!')
                    self.warning_label.setStyleSheet("color : brown;")
                else:
                    name = self.sanitize_filename(name)# removes \\/*?:"<>| which are invalid characters

                    filename_and_path = name + extension
                    
                    filename = os.path.basename(filename_and_path)

                    

                    self.selected_filename = filename
                    self.selected_link = link
                    
                    ## adds link filename and path if selected to a queue
                    asyncio.run_coroutine_threadsafe(self.xdm_instance.addQueue((link, filename, self.selected_path)),self.xdm_instance.loop)
                    
                    if self.xdm_instance.is_downloading:
                        
                        self.warning_label.setText("Task Added!")
                        self.warning_label.setStyleSheet("color: green;")

                    else:                        
                        self.warning_label.setText("Started Downloading")
                        self.warning_label.setStyleSheet("color: green;")

                    self.selected_path = None # resets path stored
                    self.close()## once link is added the add_link is destroyed while the process toplevel is packed
