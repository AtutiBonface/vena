from pathlib import Path 
class AppSettings():
    def __init__(self):
        self.default_download_path = Path.home() / "Downloads" / "Blackjuice"