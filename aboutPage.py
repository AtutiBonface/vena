from PyQt6.QtWidgets import (QFrame, QWidget, QVBoxLayout, 
                             QLabel, QPushButton, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
def switch_filelist_page(self, index):
        for name , details in self.xengine_downloads.items():
            if index == 0 and 'finished' not in details['status'].lower():
                self.active_file_widgets[name].show()

            else:
               self.active_file_widgets[name].hide()
               if index == 1 and  'finished' in details['status'].lower():
                   self.active_file_widgets[name].show()
        self.topbar.update_button_styles(index)
class AboutWindow(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            AboutWindow{
                background-color: white;
                border-radius: 10px;
                border: 1px solid #ccc;
                padding: 5px;
                margin: 0px 5px 5px 0;  
                          
            }
            QPushButton {
                border: none;
                padding: 0 16px;
                text-align: center;
                text-decoration: none;
                font-size: 13px;
                margin: 4px 2px;
                border-radius: 5px;
                background-color: #48D1CC;
                height: 40px;
            }
           
            QLineEdit, QComboBox, QSpinBox {
                padding: 6px;
                font-size: 14px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            #scroll-area{
                background-color: transparent;
                border: none;
                margin: 5px;
                border-radius: 10px;
            }
            #scroll-content{
                border-radius: 10px;
                background-color: transparent; 
            }
            #title{
              
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0,0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setObjectName('scroll-area')
        scroll_content.setObjectName('scroll-content')
        scroll_layout = QVBoxLayout(scroll_content)

        # App Logo (placeholder)
        logo_label = QLabel()

        logo_pixmap = QPixmap('images/main.ico')  # Create a placeholder pixmap
        logo_pixmap = logo_pixmap.scaled(30, 30)  # Make it transparent
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(logo_label)

        # App Overview
        overview_label = QLabel("VenaApp: Fast, Simple, Efficient Download Manager")
        overview_label.setObjectName('title')
        overview_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        overview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(overview_label)

        description = QLabel(
            "VenaApp is your all-in-one solution for efficient and hassle-free downloads. "
            "With our powerful browser extension integration, we've revolutionized the way "
            "you manage and organize your digital content. Say goodbye to slow downloads "
            "and hello to a streamlined, lightning-fast downloads with a clean, user-friendly interface"
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignJustify)
        scroll_layout.addWidget(description)

        # Features
        features_label = QLabel("Key Features:")
        features_label.setObjectName('title')
        features_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        scroll_layout.addWidget(features_label)

        features = [
            "High-speed downloads with multi-threading support",
            "Seamless browser integration for one-click downloads",
            "Intelligent pause and resume functionality",
            "Support for a wide range of file formats",
        ]

        for feature in features:
            feature_label = QLabel(f"• {feature}")
            feature_label.setWordWrap(True)
            scroll_layout.addWidget(feature_label)

        # Version Information
        version_label = QLabel("Version Information")
        version_label.setObjectName('title')
        version_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        scroll_layout.addWidget(version_label)

        version_info = QLabel("VenaApp: v2.1.0\nBrowser Extension: v2.0.0")
        scroll_layout.addWidget(version_info)

        # Team/Developer Credits
        team_label = QLabel("The Team Behind VenaApp")
        team_label.setObjectName('title')
        team_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        scroll_layout.addWidget(team_label)

        team_info = QLabel(
            "VenaApp is brought to you by a passionate AtutiBonface Softwares "
            "dedicated to enhancing your digital experience. Our diverse group "
            "brings together expertise in software engineering, UX design,"
            "cybersecurity and more  to deliver a top-notch product."
        )
        team_info.setWordWrap(True)
        scroll_layout.addWidget(team_info)

        # Support and Contact
        support_label = QLabel("Support and Contact")
        support_label.setObjectName('title')
        support_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        scroll_layout.addWidget(support_label)

        support_info = QLabel(
            "Need help or have suggestions? We're here for you!\n"
            "Email: support@venaapp.com\n"
            "Phone: +254 718202340\n"
            "Visit our website for FAQs and documentation: www.venaapp.com/support"
        )
        support_info.setWordWrap(True)
        scroll_layout.addWidget(support_info)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)
