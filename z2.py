import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Application")
        self.setGeometry(100, 100, 800, 600)
        
        # Create a button to open the secondary window
        self.open_secondary_button = QPushButton("Open Secondary Window")
        self.open_secondary_button.clicked.connect(self.open_secondary_window)

        # Set the layout and central widget
        layout = QVBoxLayout()
        layout.addWidget(self.open_secondary_button)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Initialize the secondary window
        self.secondary_window = SecondaryWindow(self)

    def open_secondary_window(self):
        self.secondary_window.show()

    def showEvent(self, event):
        super().showEvent(event)
        if self.secondary_window.isVisible():
            self.secondary_window.show()


class SecondaryWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Secondary Window")
        self.setGeometry(100, 100, 300, 200)

        # Create a button to restore the main window
        self.restore_button = QPushButton("Restore Main Window")
        self.restore_button.clicked.connect(self.restore_main_window)

        # Set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.restore_button)
        self.setLayout(layout)

    def restore_main_window(self):
        if self.main_window.isMinimized():
            self.main_window.showNormal()
        self.main_window.activateWindow()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
