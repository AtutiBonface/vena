import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QMenu, QWidget, QVBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dropdown Menu Example")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Create the dropdown button
        self.dropdown_button = QPushButton("Filter chats by")
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QMenu {
                width: 200px;
                padding: 5px;
                border-radius: 5px;
            }
            QMenu::item {
                padding: 5px 5px 5px 5px;
                border-radius: 3px;
                width: 180px;
            }
            QMenu::item:selected {
                background-color: #e6e6e6;
            }
            QMenu::icon {
                position: absolute;
                height: 15px;
                width; 15PX;
                left: 5px;
                top: 5px;
            }
        """)
        layout.addWidget(self.dropdown_button)

        # Create the dropdown menu
        self.menu = QMenu(self)
        
        # Add menu items with icons
        self.menu.addAction(QIcon("images/add-link.png"), "Add Links")
        self.menu.addAction(QIcon("images/clean.png"), "Clear Finished")
        self.menu.addAction(QIcon("images/remove.png"), "Delete Selected")
       

        # Set the menu for the dropdown button
        self.dropdown_button.setMenu(self.menu)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())