import sys
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

class FileNotFoundDialog(QDialog):
    def __init__(self, file_name):
        super().__init__()
        self.file_name = file_name
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("File Not Found")
        self.setWindowIcon(QIcon("images/failed.png"))  # Replace with your icon path
        self.setFixedSize(400, 200)

        main_layout = QVBoxLayout()

        # Icon and message layout
        icon_message_layout = QHBoxLayout()

        # Error icon
        error_icon_label = QLabel()
        error_pixmap = QPixmap("images/failed.png")  # Replace with your icon path
        error_icon_label.setPixmap(error_pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio))
        error_icon_label.setMaximumSize(30, 30)
        icon_message_layout.addWidget(error_icon_label)

        # Error message
        message_layout = QVBoxLayout()
        error_label = QLabel("File Not Found")
        error_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #E74C3C;")
        details_label = QLabel(f"The file '{self.file_name}' could not be found or may have been moved.")
        details_label.setWordWrap(True)
        message_layout.addWidget(error_label)
        message_layout.addWidget(details_label)
        icon_message_layout.addLayout(message_layout)

        main_layout.addLayout(icon_message_layout)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton(QIcon('images/like.png')," OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)

        main_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.setStyleSheet("""
            FileNotFoundDialog{
                background-color: #e2e7eb;
            }
            QPushButton{
                background-color: #48D1CC;
                width: 100px;
                height: 30px;
                border-radius: 5px;
                margin: 5px 5px 0  0;
            }

        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = FileNotFoundDialog("Free 4K Stock Videos & Full HD Video Clips to Download.mp4")
    dialog.exec()