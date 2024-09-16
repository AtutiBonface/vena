import sys
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class DeletionConfirmationWindow(QDialog):
    def __init__(self, file_name):
        super().__init__()
        self.file_name = file_name
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
        # Perform deletion logic here
        print(f"Deleting '{self.file_name}' from database")
        if delete_from_storage:
            print(f"Also deleting '{self.file_name}' from storage")
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DeletionConfirmationWindow("Free 4K Stock Videos & Full HD Video Clips to Download.mp4")
    window.show()
    sys.exit(app.exec())