import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen

class RoundedFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("RoundedFrame")
        self.setStyleSheet("""
            #RoundedFrame {
                background-color: red;
                border: 2px solid #c3c3c3;
            }
        """)

class CustomDropdown(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        self.frame = RoundedFrame()
        layout.addWidget(self.frame)
        layout.setContentsMargins(0, 0, 0, 0)

        frame_layout = QVBoxLayout(self.frame)
        for i in range(5):
            button = QPushButton(f"Option {i+1}")
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    text-align: left;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #e6e6e6;
                }
            """)
            frame_layout.addWidget(button)

        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def showEvent(self, event):
        super().showEvent(event)
        target_height = self.sizeHint().height()
        start_rect = QRect(self.geometry())
        start_rect.setHeight(0)
        end_rect = QRect(self.geometry())
        end_rect.setHeight(target_height)

        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Dropdown Example")
        self.setGeometry(100, 100, 300, 200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.button = QPushButton("Show Dropdown")
        self.button.clicked.connect(self.showDropdown)
        layout.addWidget(self.button)

        self.dropdown = CustomDropdown(self)

    def showDropdown(self):
        button_pos = self.button.mapToGlobal(self.button.rect().bottomLeft())
        self.dropdown.move(button_pos)
        self.dropdown.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())