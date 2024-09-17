from pathlib import Path 
import storage
class AppSettings():
    def __init__(self):
        self.default_download_path = Path.home() / "Downloads" / "VenaApp"


        self.settings_dict = {
            'NAME': 'VenaApp',
            'VERSION': 'v2.0',
            'DEFAULT_DOWNLOAD_PATH': f'{self.default_download_path}',
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

    def set_all_settings_to_database(self):
        if storage.get_setting('NAME') is None:
            for key , value in self.settings_dict.items():
                storage.insert_setting(key, value)


    def reset(self):
        for key , value in self.settings_dict.items():
                storage.insert_setting(key, value)

