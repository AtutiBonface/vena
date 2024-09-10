from PIL import Image
from pathlib import Path
import os, sys, logging
from urllib.parse import urljoin, urlparse, urlunparse 

class Images():
    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
    def __init__(self):
        self.document = self.resource_path('images/document.png')
        self.program = self.resource_path('images/program.png')
        self.zip = self.resource_path('images/zip.png')
        self.music = self.resource_path('images/music.png')
        self.video = self.resource_path('images/video.png')
        self.image = self.resource_path('images/image.png')


class DownloadingIndicatorBox():
    def __init__(self, parent):
        pass
class Colors():
    def __init__(self) -> None:           
        self.primary_color = '#1b1c1e'
        self.secondary_color = "#232428"
        self.text_color = '#edeef0'
        self.utils_color ="#48D1CC"

        
class ConfigFilesHandler:
    def __init__(self) -> None:
        # Define the path to the config file
        self.path_to_config_file = Path.home() / ".venaApp" / "config.txt"

        self.defaut_download_path = Path.home() / "Downloads" / "VenaApp"

    def create_config_file(self):
        self.settings_config = [
            "### Settings configuration for Vena ### \n",
            "\n",
            "*Note* Do not write or edit this file because your Vena Downloader will be faulty! Very faulty!\n",
            "\n",
            f"default_download_path <x:e> {self.defaut_download_path} \n",
            "max_concurrent_downloads <x:e> 5 \n",
            "auto_resume_download <x:e> false \n",
            "override_file <x:e> false\n",
            "show_progress_window <x:e> true \n",
            "show_download_complete_window <x:e> true \n",
            "\n",
            "extensions_link <x:e> https://vena.imaginekenya.site/addons\n",
            "VERSION <x:e> Vena 2.0 \n"
        ]

        try:
           
            if not self.path_to_config_file.parent.exists():
                self.path_to_config_file.parent.mkdir(parents=True, exist_ok=True)

            # Check if the config file already exists
            if not self.path_to_config_file.exists():
                # Write the settings to the config file if it doesn't exist
                with self.path_to_config_file.open('w') as f:
                    f.writelines(self.settings_config)
            

        except Exception as e:
            # Configure logging
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)
            # Log the exception
            logger.error(f"An error occurred: {e}")

class OtherMethods():
    def __init__(self) -> None:
        
        self.video_extensions = {
            '.mp4', '.mkv', '.flv', '.avi', '.mov', '.wmv', '.webm', 
            '.mpg', '.mpeg', '.3gp', '.m4v', '.ts', '.ogv', '.vob'
        }

        self.audio_extensions = {
            '.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.wma', 
            '.aiff', '.alac', '.opus', '.amr', '.mid', '.midi'
        }

        self.document_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
            '.txt', '.odt', '.ods', '.odp', '.html', '.htm', 
            '.rtf', '.csv', '.xml', '.xhtml', '.epub', '.md'
        }

        self.program_extensions = {
            '.exe', '.msi', '.bat', '.sh', '.py', '.jar', '.bin', 
            '.cmd', '.csh', '.pl', '.vb', '.wsf', '.vbs'
        }

        self.compressed_extensions = {
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', 
            '.xz', '.iso', '.dmg', '.tgz', '.z', '.lzma'
        }

        self.image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', 
            '.svg', '.webp', '.ico', '.heic', '.heif', '.psd'
        }

    def get_base_url(self, url):
        parsed_url = urlparse(url)
        base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '/', '', '', ''))
        return base_url
    
    def returnSpeed(self, speed):
        # Convert speed to human-readable format

        if speed > 1:
           speed = round(speed, 2)
           return f'{speed} mb/s'
        elif speed > 0:
            speed = int(speed * 1000)
            return f'{speed} kbs/s'
        else: 
            speed = int(speed * 1000)
            return f'{speed} bytes/s'
        
    def get_m3u8_in_link(self, link):
        pursed_url = urlparse(link)

        file_path = pursed_url.path

        return file_path.lower().endswith('.m3u8')
    
    def return_filesize_in_correct_units(self, filesize):
       
        try:
            filesize = int(filesize)
            if filesize >= (1024*1024*1024):  # For GB
                return f'{round(filesize / (1024**3), 2)} GB'
            elif filesize >= (1024*1024):  # For MB
                return f'{round(filesize / (1024**2), 2)} MB'
            elif filesize >= 1024:  # For KB
                return f'{round(filesize / 1024, 2)} KB'
            else:  # For bytes
                return f'{filesize} bytes'
        except Exception as e:
            return '---'
    
    def return_file_type(self, filename):
        xe_images = Images()

        name , extension = os.path.splitext(filename)
        extension = extension.lower()# converting all extensions to lower case
        if extension in self.video_extensions:
            return xe_images.video
        elif extension in self.document_extensions:
            return xe_images.document
        elif extension in self.program_extensions:
            return xe_images.program
        elif extension in self.audio_extensions:
            return xe_images.music
        elif extension in self.compressed_extensions:
            return xe_images.zip
        elif extension in self.image_extensions:
            return xe_images.image
        else: return xe_images.document

    def return_files_by_extension(self, filename):
        xe_images = Images()

        name , extension = os.path.splitext(filename)
        extension = extension.lower()# converting all extensions to lower case
        if extension in self.video_extensions:
            return "video"
        elif extension in self.document_extensions:
            return 'document'
        elif extension in self.program_extensions:
            return 'program'
        elif extension in self.audio_extensions:
            return "music"
        elif extension in self.compressed_extensions:
            return "compressed"
        elif extension in self.image_extensions:
            return "image"
        else: return 'document'


    def resource_path(self,relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
    

    content_type_to_extension = {
            # Text types
            'text/html': '.html',
            'text/plain': '.txt',
            'text/css': '.css',
            'text/csv': '.csv',
            'text/javascript': '.js',

            # Image types
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/webp': '.webp',
            'image/tiff': '.tiff',
            'image/svg+xml': '.svg',
            'image/x-icon': '.ico',

            # Audio types
            'audio/mpeg': '.mp3',
            'audio/wav': '.wav',
            'audio/ogg': '.ogg',
            'audio/midi': '.midi',
            'audio/x-aiff': '.aiff',

            # Video types
            'video/mp4': '.mp4',
            'video/x-msvideo': '.avi',
            'video/x-ms-wmv': '.wmv',
            'video/quicktime': '.mov',
            'video/webm': '.webm',
            'video/x-flv': '.flv',
            'video/mpeg': '.mpeg',

            'application/vnd.apple.mpegurl': '.m3u8',    # HLS master playlist
            'application/x-mpegURL': '.m3u8',            # HLS media playlist
            'video/mp2t': '.ts',                         # MPEG-2 Transport Stream
            'video/mp4': '.mp4',                         # MP4 segments
            'audio/aac': '.aac',                         # AAC audio segments
            'video/webm': '.webm',                       # WebM segments
            'video/ogg': '.ogv',                         # Ogg Video segments
            'audio/webm': '.weba',                       # WebM audio segments
            'audio/ogg': '.oga',                         # Ogg Audio segments

            # Application types
            'application/json': '.json',
            'application/pdf': '.pdf',
            'application/zip': '.zip',
            'application/x-tar': '.tar',
            'application/x-gzip': '.gz',
            'application/x-7z-compressed': '.7z',
            'application/x-rar-compressed': '.rar',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.ms-powerpoint': '.ppt',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            'application/x-www-form-urlencoded': '.urlencoded',
            'application/octet-stream': '',  # Generic binary file
            'application/xml': '.xml',
            'application/xhtml+xml': '.xhtml',
            'application/x-shockwave-flash': '.swf',
            'application/java-archive': '.jar',
            'application/x-msdownload': '.exe',
            'application/x-bittorrent': '.torrent',

            # Multipart types
            'multipart/form-data': '',
            'multipart/byteranges': '',
            
            # Other types
            'application/rtf': '.rtf',
            'application/postscript': '.ps',
            'application/x-iso9660-image': '.iso',
            'application/x-dosexec': '.exe',
            'application/vnd.android.package-archive': '.apk',
            'application/x-apple-diskimage': '.dmg',
            'application/x-csh': '.csh',
            'application/x-perl': '.pl',
            'application/x-python-code': '.pyc',
            'application/x-httpd-php': '.php',
            'application/x-sh': '.sh',
            'application/pgp-signature': '.sig',
            'application/vnd.oasis.opendocument.text': '.odt',
            'application/vnd.oasis.opendocument.spreadsheet': '.ods',
            'application/x-font-ttf': '.ttf',
            'application/x-font-woff': '.woff',
            'application/x-font-woff2': '.woff2',


            
        }
    def get_qss(self):
        return """
            *{
                padding: 0;
                margin: 0;
            }           
            #hero{
                background-color: #e2e7eb;
                margin: 0;
                padding : 0;
            }
        
            #topbar, #bottombar{
                height : 40px;
                background-color: transparent;
               
            }
           
            
            #content-container{
                background-color: white;
                border-radius: 10px;
                border: 1px solid #ccc;
                padding: 0;
                margin: 0px 5px 5px 0;
                
            }
            #About-btn, #Home-btn, #Settings-btn{
                background-color: #e2e7eb;
                border-radius: 10px;
                margin: 0;
                width: 40px;
                height: 40px;
                margin-bottom: 10px;
               
            } 
            #Home-btn{
                background-color: white;
            } 
           
            #About-btn:hover{
                background-color: white;
                icon: url('images/about-filled.png');
            }
            #Settings-btn:hover{
                background-color: white;
                icon: url('images/settings-filled.png');
            }#Home-btn:hover{
                background-color: white;
                icon: url('images/home-filled.png');
            }
            #active-btn, #downloaded-btn{
                background-color: #e2e7eb;
                width: 110px;
                height: 30px;
                border-radius: 5px;
                margin: 5px 5px 0  0;
            }
            #active-btn{
                background-color: #48D1CC;
            }
            #open_linkbox_btn{
                width: 40px;
                height: 30px;
                background-color: #e2e7eb;
                margin: 5px 0 0 10px;
                border-radius: 5px;  
            }
            #open_linkbox_btn:hover{
                icon: url('images/link-filled.png')
            }
            #scroll-area{
                border: none;
                background-color: transparent;
            }
            #Open-btn, #Delete-btn, #Pause-btn, #Resume-btn, #Restart-btn{
                background-color: #e2e7eb;
                border-radius: 10px;
                margin: 0;
                width: 30px;
                height: 30px;
                margin: 0 0 5px 0;
                
            } 
            #Delete-btn:hover{
                icon: url('images/trash-bin-filled.png');
            }
            #Open-btn:hover{
                icon: url('images/open-filled.png');
            }#Pause-btn:hover{
                icon: url('images/pause-filled.png');
            }#Restart-btn:hover{
                icon: url('images/refresh-filled.png');
            }#Resume-btn:hover{
                icon: url('images/play-button-filled.png');
            }
            
            
        """
            

            

                
            



