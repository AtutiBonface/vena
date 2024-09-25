from PyQt6.QtWidgets import QCheckBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
import subprocess, os, platform



class FileNotFoundDialog(QDialog):
    def __init__(self, app, file_name):
        super().__init__()
        self.file_name = file_name
        self.app = app
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
        ok_button.clicked.connect(self.close)
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


class DeletionConfirmationWindow(QDialog):
    def __init__(self,app, file_name, file_to_delete):
        super().__init__()
        self.file_name = file_name
        self.file_to_delete = file_to_delete
        self.app = app
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Confirm Deletion")
        self.setWindowIcon(QIcon("delete_icon.png"))  # Replace with your icon path
        self.setFixedSize(400, 200)

        main_layout = QVBoxLayout()

        # Warning message
        warning_label = QLabel(f"Are you sure you want to delete '{self.file_name}'?")
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning_label.setStyleSheet("font-weight: bold; color: #E74C3C;")
        main_layout.addWidget(warning_label)

        # Checkbox for deletion option
        self.delete_storage_checkbox = QCheckBox("Also delete file from Device storage")
        self.delete_storage_checkbox.setStyleSheet("margin: 10px 0;")
        main_layout.addWidget(self.delete_storage_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.confirm_deletion)
        delete_button.setStyleSheet("background-color: #E74C3C; color: white;")

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(delete_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.setStyleSheet("""
            DeletionConfirmationWindow{
                background-color: #e2e7eb;
            }
            QPushButton{
                height: 40px;
                max-width : 120px;
                border: none;
                border-radius: 5px;
                background-color: #48D1CC;
            }

        """)

    def confirm_deletion(self):
        delete_from_storage = self.delete_storage_checkbox.isChecked()
        if delete_from_storage:
            try:
                self.app.delete_details_or_make_changes(self.file_name)
            except Exception as e: 
                pass
            if os.path.exists(self.file_to_delete):
                try:
                    os.remove(self.file_to_delete)
                except Exception as e:
                    print(e)

        else:
            try:
                self.app.delete_details_or_make_changes(self.file_name)
            except Exception as e: 
                pass
        self.close()