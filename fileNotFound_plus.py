from PyQt6.QtWidgets import QCheckBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
import subprocess, os, platform
from themes import ThemeColors



class FileNotFoundDialog(QDialog):
    def __init__(self, app, file_name):
        super().__init__()
        self.file_name = file_name
        self.app = app
        self.theme_manager = ThemeColors()
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        self.setWindowTitle("File Not Found")
        self.setWindowIcon(QIcon(self.app.other_methods.resource_path('images/tray.ico')))
        self.setFixedSize(400, 180)
        
        # Center dialog on screen
        screen = self.screen().geometry()
        self.move(screen.center() - self.frameGeometry().center())

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Icon and message layout
        icon_message_layout = QHBoxLayout()
        icon_message_layout.setSpacing(15)

        error_icon_label = QLabel()
        error_pixmap = QPixmap("images/failed.png")
        error_icon_label.setPixmap(error_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio))
        error_icon_label.setFixedSize(32, 32)
        icon_message_layout.addWidget(error_icon_label)

        message_layout = QVBoxLayout()
        message_layout.setSpacing(8)
        
        error_label = QLabel("File Not Found")
        error_label.setObjectName("title")
        details_label = QLabel(f"The file '{self.file_name}' could not be found or may have been moved.")
        details_label.setWordWrap(True)
        details_label.setObjectName("message")
        
        message_layout.addWidget(error_label)
        message_layout.addWidget(details_label)
        icon_message_layout.addLayout(message_layout)

        main_layout.addLayout(icon_message_layout)
        main_layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.setFixedSize(100, 35)
        ok_button.setObjectName("primary-button")
        ok_button.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def apply_theme(self):
        colors = self.theme_manager.get_theme(self.app.current_theme)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['content_area']};
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QLabel#title {{
                font-size: 16px;
                font-weight: bold;
                color: {colors['text']};
            }}
            QLabel#message {{
                color: {colors['text_secondary']};
            }}
            QPushButton#primary-button {{
                background-color: {colors['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton#primary-button:hover {{
                background-color: {colors['accent_hover']};
            }}
        """)


class DeletionConfirmationWindow(QDialog):
    def __init__(self, app, file_name, file_to_delete):
        super().__init__()
        self.file_name = file_name
        # Convert single file to list if it's not already a list
        self.files_to_delete = file_to_delete if isinstance(file_to_delete, list) else [file_to_delete]
        self.app = app
        self.theme_manager = ThemeColors()
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        self.setWindowTitle("Confirm Deletion")
        self.setWindowIcon(QIcon(self.app.other_methods.resource_path('images/tray.ico')))
        self.setFixedSize(400, 180)
        
        # Center dialog on screen
        screen = self.screen().geometry()
        self.move(screen.center() - self.frameGeometry().center())

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Warning icon and message
        warning_layout = QHBoxLayout()
        warning_layout.setSpacing(15)

        warning_icon = QLabel()
        warning_pixmap = QPixmap("images/warning.png")
        warning_icon.setPixmap(warning_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio))
        warning_icon.setFixedSize(32, 32)
        warning_layout.addWidget(warning_icon)

        message_layout = QVBoxLayout()
        message_layout.setSpacing(8)

        warning_label = QLabel(f"Delete '{self.file_name}'?")
        warning_label.setObjectName("title")
        warning_label.setWordWrap(True)
        message_layout.addWidget(warning_label)
        warning_layout.addLayout(message_layout)

        main_layout.addLayout(warning_layout)

        # Checkbox
        self.delete_storage_checkbox = QCheckBox("Also delete file from device storage")
        self.delete_storage_checkbox.setObjectName("delete-checkbox")
        main_layout.addWidget(self.delete_storage_checkbox)

        main_layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedSize(100, 35)
        cancel_button.setObjectName("secondary-button")
        cancel_button.clicked.connect(self.close)

        delete_button = QPushButton("Delete")
        delete_button.setFixedSize(100, 35)
        delete_button.setObjectName("delete-button")
        delete_button.clicked.connect(self.confirm_deletion)

        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(delete_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def apply_theme(self):
        colors = self.theme_manager.get_theme(self.app.current_theme)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['content_area']};
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QLabel#title {{
                font-size: 16px;
                font-weight: bold;
                color: {colors['text']};
            }}
            QPushButton#secondary-button {{
                background-color: {colors['button']};
                color: {colors['text']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton#secondary-button:hover {{
                background-color: {colors['hover']};
            }}
            QPushButton#delete-button {{
                background-color: #e65d66;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton#delete-button:hover {{
                background-color: #d34751;
            }}
            QCheckBox {{
                color: {colors['text']};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 2px solid {colors['border']};
                background: {colors['content_container']};
            }}
            QCheckBox::indicator:checked {{
                background: {colors['accent']};
                border-color: {colors['accent']};
                image: url(images/check-white.png);
            }}
            QCheckBox::indicator:hover {{
                border-color: {colors['accent']};
            }}
        """)

    def confirm_deletion(self):
        delete_from_storage = self.delete_storage_checkbox.isChecked()
        
        for file_path in self.files_to_delete:
            filename = os.path.basename(file_path)
            if delete_from_storage:
                try:
                    self.app.delete_details_or_make_changes(filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(e)
            else:
                try:
                    self.app.delete_details_or_make_changes(filename)
                except Exception as e:
                    pass
        self.close()