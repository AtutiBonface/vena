import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QCheckBox, QComboBox, QSpinBox, 
                             QSlider, QStackedWidget, QFileDialog,  QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import storage
from settings import AppSettings
class SettingsWindow(QFrame):
    def __init__(self , app):
        super().__init__() 
        self.app_config = AppSettings()
       
        self.default_download_path = storage.get_setting('DEFAULT_DOWNLOAD_PATH')
        self.max_concurrent_downloads = storage.get_setting('MAX_CONCURRENT_DOWNLOADS')
        self.auto_resume_download = storage.get_setting('AUTO_RESUME_DOWNLOAD')
        self.language = storage.get_setting('LANGUAGE')
        self.bandwidth_throttling = storage.get_setting('BANDWIDTH_THROTTLING')
        self.download_priority = storage.get_setting('DOWNLOAD_PRIORITY')
        self.enable_browser_extension = storage.get_setting('ENABLE_BROWSER_EXTENSION')
        self.file_type_association = storage.get_setting('FILE_TYPE_ASSOCIATION')
        self.enable_download_confirmation_popups = storage.get_setting('ENABLE_DOWNLOAD_CONFIRMATION_POPUPS')
        self.enable_context_menu_options = storage.get_setting('ENABLE_CONTEXT_MENU_OPTIONS')
        self.auto_start_with_system = storage.get_setting('AUTO_START_APP_WITH_SYSTEM')
        self.theme = storage.get_setting('THEME') 

        
        
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("""            
            SettingsWindow{
                background-color: white;
                border-radius: 10px;
                border: 1px solid #ccc;
                padding: 0;
                margin: 0px 5px 5px 0;
            }
            QPushButton {
                border: none;
                padding: 0 16px;
                text-align: center;
                text-decoration: none;
                font-size: 13px;
                margin: 4px 2px;
                border-radius: 5px;
            }
           
            QLineEdit, QComboBox, QSpinBox {
                padding: 6px;
                font-size: 14px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
           
        """)        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0, 0, 0)
        self.topbar = SettingsTobBar(self)
        main_layout.addWidget(self.topbar)

        self.stacked_widget = QStackedWidget()
        self.general_settings = General(self)
        self.management_settings = DownloadManagement(self)
        self.browser_settings = BrowserInteraction(self)
        self.user_prefferences = UserPreferences(self)
        self.stacked_widget.addWidget(self.general_settings)
        self.stacked_widget.addWidget(self.management_settings)
        self.stacked_widget.addWidget(self.browser_settings)
        self.stacked_widget.addWidget(self.user_prefferences)

        main_layout.addWidget(self.stacked_widget, 1)        

        # Add save and cancel buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton(QIcon('images/reset-filled.png'), " Reset")
        save_button.clicked.connect(self.return_settings_to_default)
        save_button.setStyleSheet("""
                QPushButton{
                    border-radius: 5px;
                    margin: 0;
                    height: 40px;
                    background-color: #e2e7eb;
                    margin: 5px;
                    max-width: 100px;
                }
                QPushButton:hover{
                    background-color:  #48D1CC;
                    icon : url('images/reset-outline.png')
                }
            """)
       
        button_layout.addWidget(save_button)
        main_layout.addLayout(button_layout)

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.topbar.update_button_styles(index)
    def return_settings_to_default(self):
        self.general_settings.download_path.setText(self.app_config.settings_dict['DEFAULT_DOWNLOAD_PATH'])
        self.general_settings.auto_start.setChecked(self.app_config.settings_dict['AUTO_START_APP_WITH_SYSTEM'].strip().lower()== 'true')

        self.management_settings.simultaneous_spin.setValue(int(self.app_config.settings_dict['MAX_CONCURRENT_DOWNLOADS'].strip()))
        self.management_settings.resume_pause.setChecked(self.app_config.settings_dict['AUTO_RESUME_DOWNLOAD'].strip().lower()== 'true')

        self.browser_settings.extension_toggle.setChecked(self.app_config.settings_dict['ENABLE_BROWSER_EXTENSION'].strip().lower()== 'true')

        self.browser_settings.context_menu.setChecked(self.app_config.settings_dict['ENABLE_CONTEXT_MENU_OPTIONS'].strip().lower()== 'true')
        self.browser_settings.download_confirm.setChecked(self.app_config.settings_dict['ENABLE_DOWNLOAD_CONFIRMATION_POPUPS'].strip().lower()== 'true')
        self.app_config.reset()


class SettingsTobBar(QFrame):
    
    def __init__(self, master):
        super().__init__()
        self.buttons = [] 
        self.parent_cont = master   
        self.create_widgets()
    def create_widgets(self):
        self.setStyleSheet("""
            #topbar {
                background-color: transparent;
                padding: 5px;
                margin: 0 5px;
            }
            QPushButton {
                border-radius: 5px;
                margin: 0;
                height: 40px;
                background-color: #e2e7eb;
                
            }
        """)
        self.setObjectName('topbar')
        self.setMaximumHeight(50)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)        
        separator.setStyleSheet("color : #e2e7eb;")  # Set to black
        separator.setLineWidth(1)
        navigation_layout = QHBoxLayout() 
        
        main_layout.addLayout(navigation_layout)
        self.setLayout(main_layout)        
         
        self.add_icon_button(navigation_layout, {"outline": "images/general-outline.png", "filled": "images/general-filled.png"}, "General", 0)
        self.add_icon_button(navigation_layout, {"outline": "images/management-outline.png", "filled": "images/management-filled.png"}, "Download Management", 1)
        self.add_icon_button(navigation_layout, {"outline": "images/extension-outline.png", "filled": "images/extension-filled.png"}, "Browser Integrations", 2) 
        self.add_icon_button(navigation_layout, {"outline": "images/tools-outline.png", "filled": "images/tools-filled.png"}, "User Preferences", 3)     
        
        navigation_layout.addStretch()   
        navigation_layout.setContentsMargins(0, 0, 0, 0)
        navigation_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(separator) 
        self.update_button_styles(0)  # Set initial active button

    def update_button_styles(self, active_index):
        for i, (btn, icon_paths) in enumerate(self.buttons):
            if i == active_index:
                btn.setIcon(QIcon(icon_paths['outline']))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color:  #48D1CC;
                    }
                """)
            else:
                btn.setIcon(QIcon(icon_paths['filled']))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #e2e7eb;
                    }}
                    QPushButton:hover {{
                        background-color:  #48D1CC;
                    }}
                    QPushButton:hover {{
                        icon: url('{icon_paths['outline']}');
                    }}
                """)

        
    def add_icon_button(self, layout, icon_paths, text, index):
        btn = QPushButton(QIcon(icon_paths['outline']), text)
        btn.setObjectName(f'{index}-btn')    
        btn.setMaximumHeight(40)    
        btn.clicked.connect(lambda: self.parent_cont.switch_page(index))
        layout.addWidget(btn)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.buttons.append((btn, icon_paths))
        return btn
    

class General(QFrame):
    def __init__(self, master):
        super().__init__()    
       # General Settings Tab
        general_layout = QVBoxLayout()
        general_layout.setContentsMargins(0, 0, 0, 0)   
        general_layout.setSpacing(0)
        download_dir = QHBoxLayout()
        download_dir_frame = QFrame()
        download_dir_frame.setObjectName('frame1')
        download_dir_frame.setLayout(download_dir)
        download_dir.setContentsMargins(0,0,0,0)
        download_dir.setSpacing(0)
        self.download_path = QLineEdit()
        self.download_path.setDisabled(True)
        self.download_path.setText(master.default_download_path)
        download_button = QPushButton("Browse")
        download_button.clicked.connect(self.choose_directory)
        download_dir.addWidget(QLabel("Download Folder:"))
        download_dir.addStretch()
        download_dir.addWidget(self.download_path)
        download_dir.addWidget(download_button)
        general_layout.addWidget(download_dir_frame)

        self.auto_start = QCheckBox("Auto-Start VenaApp with system")
        state = master.auto_start_with_system.strip().lower() == 'true'
        self.auto_start.setChecked(state)
        self.auto_start.stateChanged.connect(self.auto_start_app)
        general_layout.addWidget(self.auto_start)
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["Chrome", "Firefox", "Edge", "Safari"])
        browser_layout = QHBoxLayout()
        browser_frame =  QFrame()
        browser_frame.setObjectName('frame2')
        browser_frame.setLayout(browser_layout)
        browser_layout.setContentsMargins(0,0,0,0)
        browser_layout.setSpacing(0)
        browser_layout.addWidget(QLabel("Default Browser:"))
        browser_layout.addWidget(self.browser_combo)
        general_layout.addWidget(browser_frame)

        general_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setLayout(general_layout)

        self.setStyleSheet("""
            General{
                margin: 0 10px;
            }
            QPushButton{
                background-color: #48D1CC;
                color: while;
                border-radius: 5px;
                height: 40px;
                padding : 0 15px;
                           
            }
            QLineEdit{
                width : 250px;
                height: 40px;
                color: black;
                padding: 0 10px;
                min-width: 400px;
            }
            QLabel{
                padding 10px 0 10px 0;
                height: 40px;
            }
            #frame1{
                margin-bottom: 20px;
            }
             #frame2{
                margin-top: 20px;
            }

        """)

    def auto_start_app(self, state):
        if state == 0:
          
            storage.insert_setting('AUTO_START_APP_WITH_SYSTEM', 'True')
        else:
        
           storage.insert_setting('AUTO_START_APP_WITH_SYSTEM', 'False')
    def choose_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_path.setText(str(folder))
            storage.insert_setting('DEFAULT_DOWNLOAD_PATH', folder)

class DownloadManagement(QFrame):
    def __init__(self, master):
        super().__init__()

        self.setStyleSheet("""
            #frame{
                margin-bottom: 10px;
            }
        """)
        
        # Download Management Tab        
        download_layout = QVBoxLayout()
        simultaneous_downloads = QHBoxLayout()
        simultaneous_downloads_frame = QFrame()
        simultaneous_downloads_frame.setLayout(simultaneous_downloads)
        simultaneous_downloads_frame.setObjectName('frame')
        simultaneous_downloads.addWidget(QLabel("Simultaneous Downloads:"))
        self.simultaneous_spin = QSpinBox()
        self.simultaneous_spin.setRange(1, 10)
        self.simultaneous_spin.setValue(int(master.max_concurrent_downloads))
        self.simultaneous_spin.valueChanged.connect(self.save_no_od_simult_downloads)
        simultaneous_downloads.addWidget(self.simultaneous_spin)
        download_layout.addWidget(simultaneous_downloads_frame)

        bandwidth_throttle = QHBoxLayout()
        bandwidth_throttle_frame = QFrame()
        bandwidth_throttle_frame.setLayout(bandwidth_throttle)
        bandwidth_throttle_frame.setObjectName('frame')
        bandwidth_throttle.addWidget(QLabel("Bandwidth Throttling:"))
        bandwidth_slider = QSlider(Qt.Orientation.Horizontal)

        bandwidth_slider.setRange(0, 100)
        bandwidth_throttle.addStretch()
        bandwidth_throttle.addWidget(bandwidth_slider)
        download_layout.addWidget(bandwidth_throttle_frame)

        priority_combo = QComboBox()
        priority_combo.addItems(["High", "Normal", "Low"])
        priority_layout = QHBoxLayout()
        priority_layout_frame = QFrame()
        priority_layout_frame.setLayout(priority_layout)
        priority_layout_frame.setObjectName('frame')
        priority_layout.addWidget(QLabel("Download Priority:"))
        priority_layout.addWidget(priority_combo)
        download_layout.addWidget(priority_layout_frame)

        self.resume_pause = QCheckBox("Auto-resume paused or interrupted downloads")
        state = master.auto_resume_download.strip().lower() == 'true'
        self.resume_pause.setChecked(state)
        self.resume_pause.stateChanged.connect(self.save_resume_pause_plus)
        self.resume_pause.setStyleSheet("margin-left: 1px; padding-left: 10px;")
        download_layout.addWidget(self.resume_pause)
        self.setLayout(download_layout)
        download_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    def save_no_od_simult_downloads(self, state):        
        storage.insert_setting('MAX_CONCURRENT_DOWNLOADS', f'{self.simultaneous_spin.value()}') 
    def save_resume_pause_plus(self, state):
        print('state is ', state)
        if state == 0:
            storage.insert_setting('AUTO_RESUME_DOWNLOAD', 'False')
        else:
           storage.insert_setting('AUTO_RESUME_DOWNLOAD', 'True') 
class BrowserInteraction(QFrame):
    def __init__(self, master):
        super().__init__()   
    
        browser_layout = QVBoxLayout()
        self.extension_toggle = QCheckBox("Enable Browser Extension")
        enable_browser = master.enable_browser_extension.strip().lower() == 'true'
        self.extension_toggle.setChecked(enable_browser)
        self.extension_toggle.stateChanged.connect(lambda state: self.save_data_to_database(state, 'ENABLE_BROWSER_EXTENSION'))
        self.extension_toggle.setStyleSheet("padding: 10px;")
        browser_layout.addWidget(self.extension_toggle)
        file_types = QLineEdit()
        file_types.setDisabled(True)
        file_types.setText(master.file_type_association)
        file_type_layout = QHBoxLayout()
        file_type_layout.setContentsMargins(0,0,0,0)
        file_type_frame = QFrame()
        file_type_frame.setLayout(file_type_layout)
        file_type_frame.setStyleSheet("padding: 5px;")
        file_type_layout.addWidget(QLabel("File Type Association:"))
        file_type_layout.addWidget(file_types)
        browser_layout.addWidget(file_type_frame)
        self.download_confirm = QCheckBox("Enable download confirmation pop-ups")
        confirm_popup = master.enable_download_confirmation_popups.strip().lower() == 'true'
        self.download_confirm.setChecked(confirm_popup)
        self.download_confirm.stateChanged.connect(lambda state: self.save_data_to_database(state, 'ENABLE_DOWNLOAD_CONFIRMATION_POPUPS'))
        self.download_confirm.setStyleSheet("padding: 10px;")
        browser_layout.addWidget(self.download_confirm)
        self.context_menu = QCheckBox("Enable context menu options in browser")
        context_menu_bool = master.enable_context_menu_options.strip().lower() == 'true'
        self.context_menu.setChecked(context_menu_bool)
        self.context_menu.stateChanged.connect(lambda state: self.save_data_to_database(state, 'ENABLE_CONTEXT_MENU_OPTIONS'))
        self.context_menu.setStyleSheet("padding: 10px;")
        browser_layout.addWidget(self.context_menu)
        self.setLayout(browser_layout)
        browser_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def save_resume_pause_plus(self, state):
        if state == 0:
            storage.insert_setting('AUTO_RESUME_DOWNLOAD', 'False')
        else:
           storage.insert_setting('AUTO_RESUME_DOWNLOAD', 'True') 
    def save_data_to_database(self, state, key):
        if state == 0:
            storage.insert_setting(key, 'False')
        else:
           storage.insert_setting(key, 'True') 


class UserPreferences(QFrame):
    def __init__(self, master):
        super().__init__()

            


        preferences_layout = QVBoxLayout()
        language_combo = QComboBox()
        language_combo.addItems(["English", "Swahili", "Hindu"])
        language_layout = QHBoxLayout()
        language_layout_frame = QFrame()
        language_layout_frame.setLayout(language_layout)
        language_layout.addWidget(QLabel("Language:"))
        language_layout.addWidget(language_combo)
        preferences_layout.addWidget(language_layout_frame)
        theme_combo = QComboBox()
        theme_combo.addItems(["Light", "Dark", "System"])
        theme_layout = QHBoxLayout()
        theme_layout_frame = QFrame()
        theme_layout_frame.setLayout(theme_layout)
        theme_layout.addWidget(QLabel("Theme:"))
        theme_layout.addWidget(theme_combo)
        preferences_layout.addWidget(theme_layout_frame)
        
        self.setLayout(preferences_layout)
        preferences_layout.setAlignment(Qt.AlignmentFlag.AlignTop)


