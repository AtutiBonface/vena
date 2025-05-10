import sys
from PyQt6.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QLineEdit
)
from PyQt6.QtGui import QPixmap


class FileInfoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Set window title
        self.setWindowTitle("File Info")

        # Main vertical layout
        main_layout = QVBoxLayout()

        # Add image preview
        image_label = QLabel()
        pixmap = QPixmap("free-photo-of-stack-of-delicious-homemade-cookies-on-plate.jpeg")  # Adjust image path
        pixmap = pixmap.scaledToWidth(100)
        image_label.setPixmap(pixmap)
        main_layout.addWidget(image_label)

        # File info layout
        info_layout = QVBoxLayout()
        
        # File name
        file_name_label = QLabel("File Name: free-photo-of-stack-of-delicious-homemade-cookies-on-plate.jpeg")
        info_layout.addWidget(file_name_label)
        
        # Status
        status_label = QLabel("Status: Completed")
        info_layout.addWidget(status_label)
        
        # Total size
        size_label = QLabel("Total size: 19.6 KB")
        info_layout.addWidget(size_label)
        
        # Added at
        added_at_label = QLabel("Added at: 1:53 AM")
        info_layout.addWidget(added_at_label)
        
        # File path
        path_label = QLabel("Path: C:\\Users\\bonface\\Downloads")
        info_layout.addWidget(path_label)

        # Add info layout to the main layout
        main_layout.addLayout(info_layout)

        # File link
        link_label = QLabel('<a href="https://images.pexels.com/...=tinysrgb&w=600&lazy=load">File Link</a>')
        link_label.setOpenExternalLinks(True)
        main_layout.addWidget(link_label)

        # Set main layout
        self.setLayout(main_layout)
        self.setMinimumWidth(300)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileInfoApp()
    window.show()
    sys.exit(app.exec())
