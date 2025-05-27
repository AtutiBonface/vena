import sys
import os
from cx_Freeze import setup, Executable

# Additional files to include (like your images folder)
include_files = [
    ('images/', 'images')  # Copies the 'images' folder to the build directory
]

# Dependencies are automatically detected, but some modules need help
build_exe_options = {
    'packages': [],
    'excludes': [],
    'include_files': include_files,
    'optimize': 2,  # Set to 1 or 2 if you want optimization
}

# Base is set to "Win32GUI" to prevent a console from popping up in Windows
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'  # Use 'Console' if you want a console window

# Icon file for the executable
icon_path = os.path.join('images', 'tray.ico')

executables = [
    Executable(
        'main.py',  # The main script
        base=base,  # Base set depending on the platform (Windows GUI)
        target_name='VenaApp.exe',  # Name of the final executable
        icon=icon_path  # Icon for the application
    )
]

setup(
    name='VenaApp',
    version='1.0',
    description='VenaApp Download Manager',
    options={
        'build_exe': build_exe_options,  # Passing the build options
    },
    executables=executables
)
