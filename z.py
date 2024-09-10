from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QStackedWidget, QLabel


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Create the stacked widget
        self.stacked_widget = QStackedWidget()

        # Create two different pages
        self.page1 = self.create_page1()
        self.page2 = self.create_page2()

        # Add pages to the stacked widget
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)

        # Set the initial page
        self.stacked_widget.setCurrentIndex(0)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)

        self.setLayout(main_layout)

    def create_page1(self):
        """Create the first page with a button to switch to the second page."""
        page = QWidget()
        layout = QVBoxLayout()

        label = QLabel("This is Page 1")
        button = QPushButton("Go to Page 2")
        button.clicked.connect(self.go_to_page2)

        layout.addWidget(label)
        layout.addWidget(button)
        page.setLayout(layout)

        return page

    def create_page2(self):
        """Create the second page with a button to switch back to the first page."""
        page = QWidget()
        layout = QVBoxLayout()

        label = QLabel("This is Page 2")
        button = QPushButton("Go to Page 1")
        button.clicked.connect(self.go_to_page1)

        layout.addWidget(label)
        layout.addWidget(button)
        page.setLayout(layout)

        return page

    def go_to_page1(self):
        """Switch to page 1."""
        self.stacked_widget.setCurrentIndex(0)

    def go_to_page2(self):
        """Switch to page 2."""
        self.stacked_widget.setCurrentIndex(1)


# Main application
if __name__ == '__main__':
    app = QApplication([])

    window = MainWindow()
    window.setWindowTitle("PyQt Page Navigation")
    window.resize(300, 200)
    window.show()

    app.exec()
