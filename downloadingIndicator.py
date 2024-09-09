from PyQt6.QtWidgets import QWidget, QLabel,QVBoxLayout,QPushButton, QHBoxLayout, QApplication, QFrame
import sys
from PyQt6.QtCore import Qt, QRect, QTimer, QSize, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QIcon, QPixmap, QFont


class CircularProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0
        self.setFixedSize(100, 100)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)  # Update every 100ms

    def update_progress(self):
        self.progress = (self.progress + 1) % 101  # Update between 0 and 100
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen_width = 4
        rect = QRect(int(30), int(30), 
                    int(44 - pen_width), int(44 - pen_width))


        # Draw progress arc
        painter.setPen(QPen(QColor(72, 209, 204), pen_width, Qt.PenStyle.SolidLine))
          # No fill for the arc
        span_angle = int(-self.progress * 360 / 100 * 16)  # progress as angle, clockwise
        painter.drawArc(rect, 90 * 16, span_angle)  # Start from top (90 degrees)

        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)  # Adjust font size as necessary
        painter.setFont(font)

        # Calculate the center of the rectangle for text placement
        text = f"{int(self.progress)}%"  # Text to be displayed (progress in percentage)
        text_rect = painter.boundingRect(rect, Qt.AlignmentFlag.AlignCenter, text)
        
        painter.setPen(QPen(QColor(0, 0, 0)))  # Black color for the text
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)  # Draw the text in the center

        painter.end()  # Close the painter
       

class DownloadIndicator(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(280, 120)
        self.move_to_bottom_right()
        self.setContentsMargins(0, 0, 0, 0)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        title_bar = QFrame()
        title_bar_layout = QHBoxLayout()
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar.setLayout(title_bar_layout)
        network_button = QPushButton(QIcon('images/signal.png'), "")
        network_button.setIconSize(QSize(10, 10))
        close_button = QPushButton(QIcon('images/close.png'), "")
        expand_app_button = QPushButton(QIcon('images/up.png'), "")
        close_button.setIconSize(QSize(10, 10))
        expand_app_button.setIconSize(QSize(15, 15))
        title_bar.setObjectName("title-bar")
        expand_app_button.setObjectName("expand-btn")
        close_button.setObjectName("close-btn")
        close_button.clicked.connect(self.close_window)
        title_bar.setMaximumHeight(13)
        title_bar_layout.setSpacing(0)


        title_bar_layout.addWidget(network_button)
        title_bar_layout.addStretch()        
        title_bar_layout.addWidget(expand_app_button)
        title_bar_layout.addWidget(close_button)
        
        body_layout = QHBoxLayout()
        body = QFrame()
        body.setObjectName('body')
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body.setLayout(body_layout)
        self.no_connection_ho_btn = QPushButton(QIcon('images/no-connection.png'), " Internet Connection lost !")

        self.no_connection_ho_btn.setObjectName("connection-lost-btn")
        self.no_connection_ho_btn.setIconSize(QSize(30, 30))
        download_finished =  QPushButton(QIcon('images/complete.png'), " download complete!")
        download_finished.setIconSize(QSize(30, 30))
        download_failed =  QPushButton(QIcon('images/failed.png'), " download failed!")
        download_failed.setIconSize(QSize(25, 25))

        task_added =  QPushButton(QIcon('images/add.png'), " Task added!")
        task_added.setIconSize(QSize(25, 25))

        tasks_frame = QFrame()        
        tasks_layout = QVBoxLayout()
        tasks_number_l = QLabel("Tasks (10)")
        downloading_l = QLabel("Downloading (0)")
        downloading_l.setStyleSheet("color: green;")
        waiting_l = QLabel("Waiting (3)")
        download_failed_label = QLabel("Failed (0)")
        download_failed_label.setStyleSheet("color: brown; font-weight : bold;")
        tasks_layout.addWidget(tasks_number_l)
        tasks_layout.addWidget(downloading_l)
        tasks_layout.addWidget(waiting_l)
        #tasks_layout.addWidget(download_failed_label)
        tasks_frame.setLayout(tasks_layout)
        self.progress_bar = CircularProgress()
        body_layout.addWidget(tasks_frame, stretch=1)    
        body_layout.addWidget(self.progress_bar)

        #body_layout.addWidget(task_added)

        main_layout.addWidget(title_bar, stretch=0,alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(body, stretch=1)

        self.apply_font(tasks_number_l, 'Helvetica', 10)
        self.apply_font(download_failed_label, 'Helvetica', 10 )
        self.apply_font(downloading_l, 'Helvetica', 10 )
        self.apply_font(waiting_l, 'Helvetica', 10 )
        self.apply_font(download_failed, 'Helvetica', 10 , bold=True)
        self.apply_font(download_finished, 'Helvetica', 10 , bold=True)
        self.apply_font(task_added, 'Helvetica', 10 , bold=True)
        self.apply_font(self.no_connection_ho_btn, 'Helvetica', 10 , bold=True)
        

        self.setStyleSheet("""
            DownloadIndicator{
                background-color: #e2e7eb;
            }
            #title-bar{
                background-color: transparent;
            }
            QPushButton{
                background-color: transparent;
                border: none;
                padding: 4px;
            }
            #close-btn:hover{
                background-color: red;
            }
            #expand-btn:hover{
                background-color: white;
            }
            #body{
                background-color: white; 
                border-radius: 5px; 
                margin: 0 2px 2px 10px;
            }
            #connection-lost-btn{
                margin 0 10px 0 10px;
                border-radius: 5px;
                color: orange;
            }
            #connection-lost-btn:hover{
                background-color: #e2e7eb;
            }
        """)
    def close_window(self):
        self.close()
        
    def move_to_bottom_right(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        x = screen_geometry.width() - self.width() - 40  # 40 px from the right
        y = screen_geometry.height() - self.height() - 70  # 70 px from the bottom
        self.move(x, y)

    

    def mousePressEvent(self, event):
        """Override to capture the position of the window when the user clicks."""
        self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Override to move the window when the user drags the title bar."""
        delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPosition().toPoint()

    def apply_font(self, widget,family,size, underline=False, bold=False, italic=False):
        font = QFont(family,size)
        font.setBold(bold)
        font.setItalic(italic)
        font.setUnderline(underline)
        widget.setFont(font)

