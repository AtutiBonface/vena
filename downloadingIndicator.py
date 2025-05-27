from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton,
                            QHBoxLayout, QApplication, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QSize, QPoint
from PyQt6.QtGui import QIcon
from venaUtils import OtherMethods
from themes import ThemeColors

class DownloadIndicator(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.other_methods = OtherMethods()
        self.theme_manager = ThemeColors()
        self.current_theme = self.app.current_theme if hasattr(self.app, 'current_theme') else 'system'
        self.setup_ui()
        self.setup_stats()
        self.apply_theme()

    def setup_ui(self):
        # Use default window flags with system buttons
        
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.CustomizeWindowHint  |
            Qt.WindowType.WindowCloseButtonHint            
                            
        )
        self.setWindowTitle("Downloads Status")
        self.setWindowIcon(QIcon(self.other_methods.resource_path('images/tray.ico')))
        self.setFixedSize(300, 160)
        self.move_to_bottom_right()

        # Main layout with adjusted margins
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 4, 12, 8)  # Reduced top margin
        main_layout.setSpacing(8)
        self.setLayout(main_layout)

        # Content frame
        content = QFrame()
        content.setObjectName('content')
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Stats grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(6)

        # Create stat widgets
        self.active_count = self.create_stat_widget("Active", "0")
        self.waiting_count = self.create_stat_widget("Waiting", "0")
        self.completed_count = self.create_stat_widget("Completed", "0")
        self.failed_count = self.create_stat_widget("Failed", "0")

        # Add stats to grid
        stats_grid.addLayout(self.active_count, 0, 0)
        stats_grid.addLayout(self.waiting_count, 0, 1)
        stats_grid.addLayout(self.completed_count, 1, 0)
        stats_grid.addLayout(self.failed_count, 1, 1)

        content_layout.addLayout(stats_grid)

        # Status message
        self.status_label = QLabel()
        self.status_label.setObjectName('status-label')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)

        main_layout.addWidget(content)

        # Add show more button at bottom
        expand_btn = QPushButton("Show More")
        expand_btn.setObjectName('expand-btn')
        expand_btn.setIcon(QIcon(self.other_methods.resource_path('images/up.png')))
        expand_btn.clicked.connect(self.open_app)
        main_layout.addWidget(expand_btn)

        # Setup message timer
        self.message_timer = QTimer(self)
        self.message_timer.timeout.connect(self.clear_message)

    def create_stat_widget(self, label, value):
        layout = QVBoxLayout()
        layout.setSpacing(2)
        
        value_label = QLabel(value)
        value_label.setObjectName(f'{label.lower()}-value')
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        name_label = QLabel(label)
        name_label.setObjectName(f'{label.lower()}-label')
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(value_label)
        layout.addWidget(name_label)
        
        # Store references to labels
        setattr(self, f'{label.lower()}_value', value_label)
        setattr(self, f'{label.lower()}_name', name_label)
        
        return layout

    def setup_stats(self):
        self.stats = {
            'active': 0,
            'waiting': 0,
            'completed': 0,
            'failed': 0
        }

    def update_stats(self, stat_type, value):
        self.stats[stat_type] = value
        # Update the value label directly using stored reference
        getattr(self, f'{stat_type}_value').setText(str(value))

    def show_message(self, message, icon, duration=3000):
        self.status_label.setText(message)
        self.message_timer.start(duration)

    def clear_message(self):
        self.status_label.clear()
        self.message_timer.stop()

    def file_added(self):
        self.update_stats('waiting', self.stats['waiting'] + 1)
        self.show_message("Task added", "")

    def download_completed(self):
        self.update_stats('completed', self.stats['completed'] + 1)
        if self.stats['active'] > 0:
            self.update_stats('active', self.stats['active'] - 1)
        self.show_message("Download complete!", "")

    def download_failed(self):
        self.update_stats('failed', self.stats['failed'] + 1)
        if self.stats['active'] > 0:
            self.update_stats('active', self.stats['active'] - 1)
        self.show_message("Download failed!", "")

    def open_app(self):
        """Handle expanding the minimized main window"""
        if self.app.isMinimized():
            self.app.showNormal()
        self.app.activateWindow()
        self.close()

    def apply_theme(self):
        """Update the theme using the current theme from parent app"""
        if hasattr(self.app, 'current_theme'):
            self.current_theme = self.app.current_theme
        stylesheet = self.theme_manager.get_stylesheet(self.current_theme)
        self.setStyleSheet(stylesheet)

    def showEvent(self, event):
        """Reapply theme when window is shown"""
        self.apply_theme()
        super().showEvent(event)

    def update_theme(self, theme):
        """Update indicator theme when main app theme changes"""
        self.current_theme = theme
        self.apply_theme()

    def move_to_bottom_right(self):
        """Position the indicator window in the bottom right of the screen"""
        screen_geometry = QApplication.primaryScreen().geometry()
        x = screen_geometry.width() - self.width() - 40  # 40 px from right
        y = screen_geometry.height() - self.height() - 70  # 70 px from bottom
        self.move(x, y)

    def mousePressEvent(self, event):
        """Capture initial mouse position for window dragging"""
        self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Handle window dragging"""
        delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPosition().toPoint()

