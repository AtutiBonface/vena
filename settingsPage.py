import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QCheckBox, QComboBox, QSpinBox, 
                             QSlider, QStackedWidget, QFileDialog,  QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import storage
from settings import AppSettings

class SettingsWindow(QFrame):
    def __init__(self, app):
        super().__init__() 
        self.app = app  # Store reference to main app
        self.app_config = app.app_config
       
        self.default_download_path = storage.get_setting('DEFAULT_DOWNLOAD_PATH')
        self.enable_tasks_indicator_popup = storage.get_setting('ENABLE_TASKS_INDICATOR_POPUP')
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

        # Set page container styling
        self.setObjectName('settings-page')
        self.setContentsMargins(2, 2, 2, 2)
        self.setProperty('class', 'page-container')

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
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
        save_button.setObjectName('reset-btn')
        save_button.clicked.connect(self.return_settings_to_default)
        button_layout.addWidget(save_button)
        main_layout.addLayout(button_layout)

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.topbar.update_button_styles(index)
    def return_settings_to_default(self):
        self.general_settings.download_path.setText(self.app_config.settings_dict['DEFAULT_DOWNLOAD_PATH'])
        self.general_settings.auto_start.setChecked(self.app_config.settings_dict['AUTO_START_APP_WITH_SYSTEM'].strip().lower()== 'true')
        self.general_settings.tasks_popup.setChecked(self.app_config.settings_dict['ENABLE_TASKS_INDICATOR_POPUP'].strip().lower()== 'true')

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
        self.setObjectName('settings-topbar')
        self.create_widgets()

    def create_widgets(self):
        self.setMaximumHeight(50)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        
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
        self.update_button_styles(0)  # Set initial active button

    def update_button_styles(self, active_index):
        for i, (btn, icon_paths) in enumerate(self.buttons):
            if i == active_index:
                btn.setIcon(QIcon(icon_paths['outline']))
                btn.setProperty('active', True)
            else:
                btn.setIcon(QIcon(icon_paths['filled']))
                btn.setProperty('active', False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def add_icon_button(self, layout, icon_paths, text, index):
        btn = QPushButton(QIcon(icon_paths['outline']), text)
        btn.setObjectName('settings-nav-btn')
        btn.setMinimumHeight(35)
        btn.clicked.connect(lambda: self.parent_cont.switch_page(index))
        layout.addWidget(btn)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.buttons.append((btn, icon_paths))
        return btn
    

class General(QFrame):
    def __init__(self, master):
        super().__init__()    
        self.setProperty('class', 'settings-page')
        self.master = master 

        general_layout = QVBoxLayout()
        general_layout.setSpacing(16)
        general_layout.setContentsMargins(16, 16, 16, 16)

        # Download Directory Section
        section1 = self.create_section()
        download_dir = QHBoxLayout()
        download_dir.setContentsMargins(0, 0, 0, 0)
        
        path_label = QLabel("Download Folder:")
        path_label.setObjectName('settings-label')
        self.download_path = QLineEdit()
        self.download_path.setObjectName('settings-input')
        self.download_path.setDisabled(True)
        self.download_path.setText(master.default_download_path)
        
        download_button = QPushButton("Browse")
        download_button.setObjectName('settings-button')
        download_button.clicked.connect(self.choose_directory)
        
        download_dir.addWidget(path_label)
        download_dir.addWidget(self.download_path, 1)
        download_dir.addWidget(download_button)
        section1.setLayout(download_dir)
        general_layout.addWidget(section1)

        # Auto-start and Tasks Section
        section2 = self.create_section()
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(8)

        self.auto_start = QCheckBox("Auto-Start VenaApp with system")
        self.auto_start.setObjectName('settings-checkbox')
        state = master.auto_start_with_system.strip().lower() == 'true'
        self.auto_start.setChecked(state)
        self.auto_start.stateChanged.connect(self.auto_start_app)

        self.tasks_popup = QCheckBox("Enable Tasks Indicator Popup")
        self.tasks_popup.setObjectName('settings-checkbox')
        popup_state = master.enable_tasks_indicator_popup.strip().lower() == 'true'
        self.tasks_popup.setChecked(popup_state)
        self.tasks_popup.stateChanged.connect(self.change_state_tasks_popup)

        checkbox_layout.addWidget(self.tasks_popup)
        checkbox_layout.addWidget(self.auto_start)
        section2.setLayout(checkbox_layout)
        general_layout.addWidget(section2)
        
        # Browser Section
        section3 = self.create_section()
        browser_layout = QHBoxLayout()
        browser_layout.setContentsMargins(0, 0, 0, 0)
        
        browser_label = QLabel("Default Browser:")
        browser_label.setObjectName('settings-label')
        self.browser_combo = QComboBox()
        self.browser_combo.setObjectName('settings-combobox')
        self.browser_combo.addItems(["Chrome", "Firefox", "Edge", "Safari"])
        browser_layout.addWidget(browser_label)
        browser_layout.addWidget(self.browser_combo, 1)
        section3.setLayout(browser_layout)
        general_layout.addWidget(section3)

        general_layout.addStretch()
        self.setLayout(general_layout)

    def create_section(self):
        section = QFrame()
        section.setObjectName('settings-section')
        return section

    def auto_start_app(self, state):
        if state == 0:
            storage.insert_setting('AUTO_START_APP_WITH_SYSTEM', 'True')
        else:
           storage.insert_setting('AUTO_START_APP_WITH_SYSTEM', 'False')

    def change_state_tasks_popup(self, state):
        if state == 0:
            storage.insert_setting('ENABLE_TASKS_INDICATOR_POPUP', 'False')
        else:
            storage.insert_setting('ENABLE_TASKS_INDICATOR_POPUP', 'True')

    def choose_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_path.setText(str(folder))
            self.master.app_config.default_download_path = str(folder)
            storage.insert_setting('DEFAULT_DOWNLOAD_PATH', str(folder))

class DownloadManagement(QFrame):
    def __init__(self, master):
        super().__init__()
        self.setProperty('class', 'settings-page')
        
        download_layout = QVBoxLayout()
        download_layout.setSpacing(16)
        download_layout.setContentsMargins(16, 16, 16, 16)
        
        # Simultaneous Downloads Section
        section1 = self.create_section()
        simultaneous_downloads = QHBoxLayout()
        simul_label = QLabel("Simultaneous Downloads:")
        simul_label.setObjectName('settings-label')
        self.simultaneous_spin = QSpinBox()
        self.simultaneous_spin.setObjectName('settings-spinbox')
        self.simultaneous_spin.setRange(1, 10)
        self.simultaneous_spin.setValue(int(master.max_concurrent_downloads))
        self.simultaneous_spin.valueChanged.connect(self.save_no_od_simult_downloads)
        simultaneous_downloads.addWidget(simul_label)
        simultaneous_downloads.addWidget(self.simultaneous_spin)
        simultaneous_downloads.addStretch()
        section1.setLayout(simultaneous_downloads)
        download_layout.addWidget(section1)

        # Bandwidth Throttling Section
        section2 = self.create_section()
        bandwidth_throttle = QHBoxLayout()
        bandwidth_label = QLabel("Bandwidth Throttling:")
        bandwidth_label.setObjectName('settings-label')
        bandwidth_slider = QSlider(Qt.Orientation.Horizontal)
        bandwidth_slider.setRange(0, 100)
        bandwidth_throttle.addWidget(bandwidth_label)
        bandwidth_throttle.addWidget(bandwidth_slider)
        bandwidth_throttle.addStretch()
        section2.setLayout(bandwidth_throttle)
        download_layout.addWidget(section2)

        # Download Priority Section
        section3 = self.create_section()
        priority_layout = QHBoxLayout()
        priority_label = QLabel("Download Priority:")
        priority_label.setObjectName('settings-label')
        priority_combo = QComboBox()
        priority_combo.addItems(["High", "Normal", "Low"])
        priority_layout.addWidget(priority_label)
        priority_layout.addWidget(priority_combo)
        priority_layout.addStretch()
        section3.setLayout(priority_layout)
        download_layout.addWidget(section3)

        # Auto-resume Section
        section4 = self.create_section()
        self.resume_pause = QCheckBox("Auto-resume paused or interrupted downloads")
        self.resume_pause.setObjectName('settings-checkbox')
        state = master.auto_resume_download.strip().lower() == 'true'
        self.resume_pause.setChecked(state)
        self.resume_pause.stateChanged.connect(self.save_resume_pause_plus)
        section4.setLayout(QVBoxLayout())
        section4.layout().addWidget(self.resume_pause)
        download_layout.addWidget(section4)

        download_layout.addStretch()
        self.setLayout(download_layout)

    def create_section(self):
        section = QFrame()
        section.setObjectName('settings-section')
        return section

    def save_no_od_simult_downloads(self, state):        
        storage.insert_setting('MAX_CONCURRENT_DOWNLOADS', f'{self.simultaneous_spin.value()}') 

    def save_resume_pause_plus(self, state):
        if state == 0:
            storage.insert_setting('AUTO_RESUME_DOWNLOAD', 'False')
        else:
           storage.insert_setting('AUTO_RESUME_DOWNLOAD', 'True') 

class BrowserInteraction(QFrame):
    def __init__(self, master):
        super().__init__()   
        self.setProperty('class', 'settings-page')
    
        browser_layout = QVBoxLayout()
        browser_layout.setSpacing(16)
        browser_layout.setContentsMargins(16, 16, 16, 16)
        
        # Browser Extension Section
        section1 = self.create_section()
        self.extension_toggle = QCheckBox("Enable Browser Extension")
        self.extension_toggle.setObjectName('settings-checkbox')
        enable_browser = master.enable_browser_extension.strip().lower() == 'true'
        self.extension_toggle.setChecked(enable_browser)
        self.extension_toggle.stateChanged.connect(lambda state: self.save_data_to_database(state, 'ENABLE_BROWSER_EXTENSION'))
        section1.setLayout(QVBoxLayout())
        section1.layout().addWidget(self.extension_toggle)
        browser_layout.addWidget(section1)

        # File Type Association Section
        section2 = self.create_section()
        file_type_layout = QHBoxLayout()
        file_type_label = QLabel("File Type Association:")
        file_type_label.setObjectName('settings-label')
        file_types = QLineEdit()
        file_types.setObjectName('settings-input')
        file_types.setDisabled(True)
        file_types.setText(master.file_type_association)
        file_type_layout.addWidget(file_type_label)
        file_type_layout.addWidget(file_types, 1)
        section2.setLayout(file_type_layout)
        browser_layout.addWidget(section2)

        # Download Confirmation Section
        section3 = self.create_section()
        confirm_layout = QVBoxLayout()
        self.download_confirm = QCheckBox("Enable download confirmation pop-ups")
        self.download_confirm.setObjectName('settings-checkbox')
        confirm_popup = master.enable_download_confirmation_popups.strip().lower() == 'true'
        self.download_confirm.setChecked(confirm_popup)
        self.download_confirm.stateChanged.connect(lambda state: self.save_data_to_database(state, 'ENABLE_DOWNLOAD_CONFIRMATION_POPUPS'))
        
        self.context_menu = QCheckBox("Enable context menu options in browser")
        self.context_menu.setObjectName('settings-checkbox')
        context_menu_bool = master.enable_context_menu_options.strip().lower() == 'true'
        self.context_menu.setChecked(context_menu_bool)
        self.context_menu.stateChanged.connect(lambda state: self.save_data_to_database(state, 'ENABLE_CONTEXT_MENU_OPTIONS'))
        
        confirm_layout.addWidget(self.download_confirm)
        confirm_layout.addWidget(self.context_menu)
        section3.setLayout(confirm_layout)
        browser_layout.addWidget(section3)

        browser_layout.addStretch()
        self.setLayout(browser_layout)

    def create_section(self):
        section = QFrame()
        section.setObjectName('settings-section')
        return section

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
        self.master = master
        self.setProperty('class', 'settings-page')
        
        preferences_layout = QVBoxLayout()
        preferences_layout.setSpacing(16)
        preferences_layout.setContentsMargins(16, 16, 16, 16)
        
        # Theme Section
        section1 = self.create_section()
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setObjectName('settings-label')
        theme_combo = QComboBox()
        theme_combo.setObjectName('settings-combobox')
        theme_combo.addItems(["System", "Light", "Dark"])
        current_theme = storage.get_setting('THEME') or 'system'
        theme_combo.setCurrentText(current_theme.capitalize())
        theme_combo.currentTextChanged.connect(self.change_theme)
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(theme_combo, 1)
        section1.setLayout(theme_layout)
        preferences_layout.addWidget(section1)

        preferences_layout.addStretch()
        self.setLayout(preferences_layout)

    def create_section(self):
        section = QFrame()
        section.setObjectName('settings-section')
        return section

    def change_theme(self, theme_name):
        theme = theme_name.lower()
        self.master.app.switch_theme(theme)


