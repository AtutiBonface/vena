from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window setup
        self.setWindowTitle("Window State Check")
        self.resize(300, 200)

        # Label to display the window state
        self.status_label = QLabel("Window Status: Normal", self)

        # Button to check window state
        self.check_button = QPushButton("Check Window State", self)
        self.check_button.clicked.connect(self.check_window_state)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.check_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def check_window_state(self):
        if self.isMinimized():
            self.status_label.setText("Window Status: Minimized")
        elif self.isActiveWindow():
            self.status_label.setText("Window Status: Active")
        else:
            self.status_label.setText("Window Status: Inactive")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
