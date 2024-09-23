from pathlib import Path 
import storage
class AppSettings():
    def __init__(self):
                      
        path = Path.home() / "Downloads" / "VenaApp"
        self.default_download_path = storage.get_setting('DEFAULT_DOWNLOAD_PATH') if storage.get_setting('DEFAULT_DOWNLOAD_PATH') is not None else path


        self.settings_dict = {
            'NAME': 'VenaApp',
            'VERSION': 'v2.0',
            'DEFAULT_DOWNLOAD_PATH': f'{path}',
            'ENABLE_TASKS_INDICATOR_POPUP': 'True',
            'MAX_CONCURRENT_DOWNLOADS': '5',
            'AUTO_RESUME_DOWNLOAD': 'False',
            'AUTO_START_APP_WITH_SYSTEM': 'True',
            'LANGUAGE': 'English',
            'DEFAULT_BROWSER' : 'Chrome \n',
            'BANDWIDTH_THROTTLING': 'unlimited',
            'DOWNLOAD_PRIORITY': 'Normal',
            'ENABLE_BROWSER_EXTENSION': 'True',
            'FILE_TYPE_ASSOCIATION': '.mp4, .mp3, .mkv, .avi, .flv, .mov, .wmv, .wav, .aac, .ogg',
            'ENABLE_DOWNLOAD_CONFIRMATION_POPUPS': 'True',
            'ENABLE_CONTEXT_MENU_OPTIONS': 'True',
            'THEME': 'Light'
        }
        self.default_download_path = storage.get_setting('DEFAULT_DOWNLOAD_PATH') if storage.get_setting('DEFAULT_DOWNLOAD_PATH') is not None else self.settings_dict['DEFAULT_DOWNLOAD_PATH']
        self.enable_tasks_indicator_popup = storage.get_setting('ENABLE_TASKS_INDICATOR_POPUP') if storage.get_setting('ENABLE_TASKS_INDICATOR_POPUP') is not None else self.settings_dict['ENABLE_TASKS_INDICATOR_POPUP']
        self.max_concurrent_downloads = storage.get_setting('MAX_CONCURRENT_DOWNLOADS') if storage.get_setting('MAX_CONCURRENT_DOWNLOADS') is not None else self.settings_dict['MAX_CONCURRENT_DOWNLOADS']
        self.auto_resume_download = storage.get_setting('AUTO_RESUME_DOWNLOAD') if storage.get_setting('AUTO_RESUME_DOWNLOAD') is not None else self.settings_dict['AUTO_RESUME_DOWNLOAD']
        self.language = storage.get_setting('LANGUAGE') if storage.get_setting('LANGUAGE') is not None else self.settings_dict['LANGUAGE']
        self.bandwidth_throttling = storage.get_setting('BANDWIDTH_THROTTLING') if storage.get_setting('BANDWIDTH_THROTTLING') is not None else self.settings_dict['BANDWIDTH_THROTTLING']
        self.download_priority = storage.get_setting('DOWNLOAD_PRIORITY') if storage.get_setting('DOWNLOAD_PRIORITY') is not None else self.settings_dict['DOWNLOAD_PRIORITY']
        self.enable_browser_extension = storage.get_setting('ENABLE_BROWSER_EXTENSION') if storage.get_setting('ENABLE_BROWSER_EXTENSION') is not None else self.settings_dict['ENABLE_BROWSER_EXTENSION']
        self.file_type_association = storage.get_setting('FILE_TYPE_ASSOCIATION') if storage.get_setting('FILE_TYPE_ASSOCIATION') is not None else self.settings_dict['FILE_TYPE_ASSOCIATION']
        self.enable_download_confirmation_popups = storage.get_setting('ENABLE_DOWNLOAD_CONFIRMATION_POPUPS') if storage.get_setting('ENABLE_DOWNLOAD_CONFIRMATION_POPUPS') is not None else self.settings_dict['ENABLE_DOWNLOAD_CONFIRMATION_POPUPS']
        self.enable_context_menu_options = storage.get_setting('ENABLE_CONTEXT_MENU_OPTIONS') if storage.get_setting('ENABLE_CONTEXT_MENU_OPTIONS') is not None else self.settings_dict['ENABLE_CONTEXT_MENU_OPTIONS']
        self.auto_start_with_system = storage.get_setting('AUTO_START_APP_WITH_SYSTEM') if storage.get_setting('AUTO_START_APP_WITH_SYSTEM') is not None else self.settings_dict['AUTO_START_APP_WITH_SYSTEM']
        self.theme = storage.get_setting('THEME') if storage.get_setting('THEME') is not None else self.settings_dict['THEME']


    def set_all_settings_to_database(self):
        if storage.get_setting('NAME') is None:
            for key , value in self.settings_dict.items():
                storage.insert_setting(key, value)


    def reset(self):
        for key , value in self.settings_dict.items():
                storage.insert_setting(key, value)

