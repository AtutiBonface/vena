from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel

class FileInfoBox(QFrame):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setObjectName('file-info-box')
        self.setStyleSheet("""
            QLabel {
                padding: 10px 0;
                margin: 0;
            }
            #link {
                color: #6a3de8;
            }
        """)

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.addStretch()
        self.image_label = QLabel()
        
        self.main_layout.addWidget(self.image_label)
        info_layout = QVBoxLayout()        
        
        # File name
        self.file_name_label = QLabel("")
        info_layout.addWidget(self.file_name_label)        
        # Status
        self.status_label = QLabel("")
        info_layout.addWidget(self.status_label)        
        # Total size
        self.size_label = QLabel("")
        info_layout.addWidget(self.size_label)        
        # Added at
        self.added_at_label = QLabel("")
        info_layout.addWidget(self.added_at_label)        
        # File path
        self.path_label = QLabel("")
        info_layout.addWidget(self.path_label)
        
        # File link
        self.link_label = QLabel('')
        self.link_label.setObjectName('link')
        self.link_label.setWordWrap(True) 
        info_layout.addWidget(self.link_label)
        
        self.link_label.setOpenExternalLinks(True)
        self.main_layout.addLayout(info_layout)
        self.main_layout.addStretch()

        # Set main layout
        self.setLayout(self.main_layout)
        self.setMinimumWidth(200)
        self.setMaximumWidth(300)
