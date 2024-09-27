import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QListWidget, QListWidgetItem, QPushButton, QLabel, QLineEdit, QFileDialog)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

class FileItem(QWidget):
    def __init__(self, filename=None, size=None, url=None, cookies=None):
        super().__init__()
        self.filename = filename
        self.size = size
        self.url = url
        self.cookies = cookies
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        top_row = QHBoxLayout()
        self.filename_label = QLabel(self.filename)
        self.url_label = QLabel(self.url)
        top_row.addWidget(self.filename_label)
        top_row.addWidget(self.url_label)
        
        bottom_row = QHBoxLayout()
        self.size_label = QLabel(f"Size: {self.size}")
        bottom_row.addWidget(self.size_label)
        
        layout.addLayout(top_row)
        layout.addLayout(bottom_row)
        
        self.setLayout(layout)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border-radius: 5px;
                padding: 5px;
                margin: 2px;
            }
            QLabel {
                color: #333;
            }
        """)

class DownloadManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Download Manager")
        self.setGeometry(100, 100, 600, 400)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # File list
        self.file_list = QListWidget()
        main_layout.addWidget(self.file_list)

        # Add file section
        add_file_layout = QHBoxLayout()
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("Filename")
       
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("URL")
        add_button = QPushButton("Add File")
        add_button.clicked.connect(self.add_file)

        add_file_layout.addWidget(self.filename_input)        
        add_file_layout.addWidget(self.url_input)
        add_file_layout.addWidget(add_button)
        main_layout.addLayout(add_file_layout)

        # Action buttons
        button_layout = QHBoxLayout()
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_selected)
        download_button = QPushButton("Download Selected")
        download_button.clicked.connect(self.download_selected)

        button_layout.addWidget(remove_button)
        button_layout.addWidget(download_button)
        main_layout.addLayout(button_layout)

    def add_file(self):
        filename = self.filename_input.text()
       
        url = self.url_input.text()
        if filename  and url:
            item_widget = FileItem(filename=filename, url=url)
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            self.file_list.addItem(list_item)
            self.file_list.setItemWidget(list_item, item_widget)
            self.clear_inputs()

    def remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def download_selected(self):
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            widget = self.file_list.itemWidget(item)
            print(f"Downloading: {widget.filename} from {widget.url}")
        # Here you would implement the actual download logic

    def clear_inputs(self):
        self.filename_input.clear()
        self.url_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloadManager()
    window.show()
    sys.exit(app.exec())