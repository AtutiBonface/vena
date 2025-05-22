from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

class ThemeColors:
    def __init__(self):
        self.light = {
            'window': '#ffffff',  # White window
            'content_area': '#e2e7eb',  # Main container background
            'content_container': '#ffffff',  # Inner containers
            'sidebar': 'transparent',
            'text': '#24292e',
            'text_secondary': '#656d76',
            'border': '#e1e4e8',
            'separator': '#f0f2f4',  # Add lighter border color for separators
            'content_border': '#ccc',  # Add specific border color for content container
            'hover': '#e1e4e8',
            'button': '#f1f2f3',
            'button_text': '#24292e',
            'accent': '#48D1CC',
            'accent_hover': '#3eb5b0',  # Slightly darker version of accent
            'status': {
                'completed': '#4ac069',  # Lighter green
                'downloading': '#70d6d1', # Lighter turquoise
                'paused': '#dba53f',     # Lighter orange
                'failed': '#e65d66'      # Lighter red
            }
        }
        
        self.dark = {
            'window': '#1a1a1a',  # Dark window
            'content_area': '#2d2d2d',  # Darker container
            'content_container': '#363636',  # Inner containers
            'sidebar': 'transparent',
            'text': '#e1e1e1',
            'text_secondary': '#9da5b4',
            'border': '#404040',
            'content_border': '#404040',  # Darker border for dark theme
            'hover': '#2d2d2d',
            'button': '#333333',
            'button_text': '#e1e1e1',
            'accent': '#48D1CC',
            'accent_hover': '#5ce6e0',  # Slightly lighter version of accent
            'status': {
                'completed': '#3da158',  # Lighter green for dark theme
                'downloading': '#5eccc7', # Lighter turquoise for dark theme
                'paused': '#c99537',     # Lighter orange for dark theme
                'failed': '#d34751'      # Lighter red for dark theme
            }
        }

    def get_theme(self, theme='system'):
        if theme == 'system':
            # Get system theme from Qt's palette
            app = QApplication.instance()
            if app:
                palette = app.style().standardPalette()
                # Check if system theme appears dark
                bg_color = palette.color(QPalette.ColorRole.Window)
                is_dark = self.is_dark_color(bg_color)
                return self.dark if is_dark else self.light
            return self.light
        return self.dark if theme == 'dark' else self.light

    def is_dark_color(self, color):
        """Check if a color appears dark based on its luminance"""
        # Calculate relative luminance
        luminance = (0.299 * color.red() + 
                    0.587 * color.green() + 
                    0.114 * color.blue()) / 255
        return luminance < 0.5

    def get_stylesheet(self, theme='system'):
        colors = self.get_theme(theme)
        return f"""
            /* Base Window Styles */
            QMainWindow {{
                background-color: {colors['window']};
                color: {colors['text']};
            }}
            
            /* Shared Page Container Style */
            .page-container {{
                background-color: {colors['content_area']};
                border-radius: 10px;
                padding: 0;
                margin: 0px 5px 5px 0;
            }}
            
            #content-container {{
                background-color: {colors['content_area']};
                border-radius: 10px;
                border: 1px solid {colors['content_border']};
                padding: 0;
                margin: 0px 5px 5px 0;
            }}
            
            /* Sidebar Styling */
            #sidebar {{
                background-color: {colors['sidebar']};
                border: none;
                padding: 4px;
            }}
            
            #sidebar QPushButton {{
                border-radius: 10px;
                margin: 2px;
                width: 40px;
                height: 40px;
                background-color: transparent;
                padding: 0;
            }}
            
            #sidebar QPushButton:hover {{
                background-color: {colors['hover']};
            }}
            
            #sidebar QPushButton[active="true"] {{
                background-color: {colors['accent']};
            }}
            
            #sidebar QPushButton[active="true"]:hover {{
                background-color: {colors['accent_hover']};
            }}
            
            #sidebar {{
                background-color: {colors['sidebar']};
                border: none;
                padding: 8px;
            }}
            #topbar {{
                background-color: transparent;
                border-bottom: 1px solid {colors['border']};
                padding: 8px;
            }}
            #file-info-box {{
                background-color: {colors['content_container']};
                border-radius: 6px;
                margin: 5px;
            }}
            QLabel {{
                color: {colors['text']};
            }}
            .secondary-text {{
                color: {colors['text_secondary']};
            }}
            QPushButton {{
                background-color: {colors['button']};
                color: {colors['text']};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {colors['hover']};
            }}
            #add-link-btn {{
                background-color: {colors['accent']};
                color: white;
            }}
            #add-link-btn:hover {{
                background-color: {colors['accent_hover']};
                opacity: 0.9;
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollArea #scroll-widget {{
                background-color: transparent;
            }}
            FileItemWidget {{
                background-color: transparent;
                border-radius: 4px;
                margin: 0;
                padding: 2px;
                border-bottom: 1px solid {colors.get('separator', colors['border'])};  /* Lighter separator for light theme */
            }}
            
            FileItemWidget:last-child {{
                border-bottom: none;  /* Remove border from last item */
            }}
            
            FileItemWidget:hover {{
                background-color: {colors['button']};
            }}
            
            /* Add padding to the main layout of FileItemWidget */
            FileItemWidget > QHBoxLayout {{
                padding: 8px 12px;
            }}
            
            FileItemWidget:checked {{
                background-color: {colors['button']};
            }}
            
            FileItemWidget #file-checkbox {{
                margin: 0;
                spacing: 0;
            }}
            
            FileItemWidget #icon-label {{
                background-color: {colors['button']};
                border-radius: 6px;
            }}
            FileItemWidget #filename-label {{
                color: {colors['text']};
                font-size: 13px;
                font-weight: 500;
                padding: 2px 0;
            }}
            
            FileItemWidget #info-label {{
                color: {colors['text_secondary']};
                font-size: 12px;
                padding: 2px 0;
            }}
            
            /* Status label styles */
            FileItemWidget #status-label[download-status="completed"] {{
                background-color: {colors['status']['completed']};
                color: white;
                border-radius: 10px;
                padding: 2px 8px;
            }}
            
            FileItemWidget #status-label[download-status="downloading"] {{
                background-color: {colors['status']['downloading']};
                color: white;
                border-radius: 10px;
                padding: 2px 8px;
            }}
            
            FileItemWidget #status-label[download-status="paused"] {{
                background-color: {colors['status']['paused']};
                color: white;
                border-radius: 10px;
                padding: 2px 8px;
            }}
            
            FileItemWidget #status-label[download-status="failed"] {{
                background-color: {colors['status']['failed']};
                color: white;
                border-radius: 10px;
                padding: 2px 8px;
            }}
            
            FileItemWidget #status-label {{
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 12px;
                /* Default status background */
                background-color: {colors['status']['downloading']};
                color: white;
            }}

            FileItemWidget #speed-label {{
                color: {colors['text']};
                font-size: 12px;
                padding: 2px 0;
            }}
            
            FileItemWidget #date-label {{
                color: {colors['text_secondary']};
                font-size: 12px;
                padding: 2px 0;
            }}
            
            FileItemWidget #retry-btn {{
                background: transparent;
                color: {colors['accent']};
                border: none;
                font-size: 12px;
                padding: 2px 8px;
            }}
            FileItemWidget #retry-btn:hover {{
                color: {colors['accent_hover']};
                text-decoration: underline;
            }}
            #info-label, #date-label {{
                color: {colors['text_secondary']};
            }}
            
            /* TopBar Button Styles */
            #topbar QPushButton {{
                background-color: {colors['button']};
                color: {colors['button_text']};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                margin-right: 8px;
            }}
            
            #topbar QPushButton:hover {{
                background-color: {colors['hover']};
            }}

            #topbar QIcon {{
                margin-right: 6px;
            }}
            
            #topbar #add-link-btn {{
                background-color: {colors['accent']};
                color: white;
            }}
            
            #topbar #add-link-btn:hover {{
                background-color: {colors['accent_hover']};
            }}
            
            /* About Page Styles */
            #scroll-content {{
                background-color: {colors['content_area']};
                border-radius: 10px;
            }}
            
            #scroll-area {{
                background-color: {colors['content_area']};
            }}
            
            #scroll-content QLabel {{
                color: {colors['text']};
            }}
            
            #scroll-content QLabel#title {{
                color: {colors['text']};
                font-weight: bold;
            }}
            
            #scroll-content QLabel.secondary-text {{
                color: {colors['text_secondary']};
            }}
            
            #scroll-content QPushButton {{
                background-color: {colors['button']};
                color: {colors['button_text']};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            
            #scroll-content QPushButton:hover {{
                background-color: {colors['hover']};
            }}
            
            /* Settings Page Styles */
            #settings-page {{
                background-color: {colors['content_area']};
                border: none;
                margin: 0;
            }}
            
            #settings-page .page-container {{
                background-color: {colors['content_container']};
                border-radius: 10px;
                padding: 16px;
            }}
            
            #settings-topbar {{
                background-color: transparent;
                border-bottom: 1px solid {colors['border']};
                padding: 8px;
                margin-bottom: 16px;
            }}
            
            #settings-topbar QPushButton {{
                background-color: {colors['button']};
                color: {colors['text']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                min-width: 120px;
                height: 40px;
            }}

            #settings-topbar QPushButton {{
                height: 35px;
                min-width: 120px;
                padding: 0 16px;
                font-size: 13px;
            }}
            
            #settings-topbar QPushButton:hover {{
                background-color: {colors['hover']};
            }}
            
            #settings-topbar QPushButton[active="true"] {{
                background-color: {colors['accent']};
                color: white;
            }}

            #reset-btn {{
                background-color: {colors['button']};
                color: {colors['text']};
                border-radius: 6px;
                padding: 8px 16px;
                max-width: 100px;
                height: 40px;
                min-width: 100px;
            }}

            #reset-btn {{
                height: 35px;
                min-width: 100px;
            }}

            #reset-btn:hover {{
                background-color: {colors['accent']};
                color: white;
            }}
            
            /* Settings Topbar Navigation */
            #settings-topbar {{
                background-color: transparent;
                border-bottom: 1px solid {colors['border']};
                padding: 8px;
                margin-bottom: 16px;
            }}
            
            #settings-nav-btn {{
                background-color: {colors['button']};
                color: {colors['text']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                height: 35px;
                min-width: 120px;
            }}
            
            #settings-nav-btn:hover {{
                background-color: {colors['hover']};
            }}
            
            #settings-nav-btn[active="true"] {{
                background-color: {colors['accent']};
                color: white;
            }}
            
            #topbar-separator {{
                color: {colors['border']};
            }}
            
            /* Settings form controls */
            .settings-page QLabel {{
                color: {colors['text']};
                padding: 8px 0;
            }}
            
            .settings-page QLineEdit,
            .settings-page QComboBox,
            .settings-page QSpinBox {{
                background: {colors['content_container']};
                border: 1px solid {colors['border']};
                color: {colors['text']};
                padding: 8px;
                border-radius: 6px;
                height: 40px;
                min-width: 120px;
            }}

            .settings-page QLineEdit,
            .settings-page QComboBox,
            .settings-page QSpinBox {{
                height: 35px;
                min-width: 120px;
                padding: 0 10px;
            }}

            .settings-page QComboBox::drop-down {{
                border: none;
                width: 35px;
            }}

            .settings-page QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}

            .settings-page QComboBox QAbstractItemView {{
                padding: 8px 4px;
                border: 1px solid {colors['border']};
                background: {colors['content_container']};
                selection-background-color: {colors['accent']};
            }}

            .settings-page QComboBox QAbstractItemView::item {{
                min-height: 30px;
                padding: 0 8px;
            }}

            .settings-page QComboBox QAbstractItemView::item:selected {{
                background-color: {colors['accent']};
                color: white;
            }}

            .settings-page QCheckBox {{
                color: {colors['text']};
                padding: 8px 0;
            }}

            .settings-page QPushButton {{
                height: 40px;
                min-width: 100px;
                background-color: {colors['button']};
                color: {colors['text']};
            }}

            .settings-page QPushButton:hover {{
                background-color: {colors['accent']};
                color: white;
            }}

            .settings-page QComboBox::drop-down {{
                border: none;
                padding-right: 15px;
            }}

            .settings-page QSpinBox::up-button,
            .settings-page QSpinBox::down-button {{
                width: 25px;
            }}

            /* Settings form controls */
            .settings-page QLabel#settings-label {{
                color: {colors['text']};
                padding: 8px 0;
            }}
            
            .settings-page QLineEdit#settings-input {{
                background: {colors['content_container']};
                border: 1px solid {colors['border']};
                color: {colors['text']};
                padding: 8px;
                border-radius: 6px;
                height: 35px;
                min-width: 120px;
            }}
            
            .settings-page QCheckBox#settings-checkbox {{
                color: {colors['text']};
                spacing: 8px;
                margin: 8px 0;
            }}
            
            .settings-page QPushButton#settings-button {{
                background-color: {colors['button']};
                color: {colors['button_text']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                height: 35px;
            }}
            
            .settings-page QPushButton#settings-button:hover {{
                background-color: {colors['accent']};
                color: white;
            }}

            /* Settings Section Styles */
            #settings-section {{
                background-color: {colors['content_container']};
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 8px;
            }}
            
            #settings-section QLabel#settings-label {{
                min-width: 160px;
            }}
            
            #settings-section QComboBox,
            #settings-section QSpinBox,
            #settings-section QLineEdit {{               
                min-width: 200px;
            }}

            /* Download Indicator Styles */
            DownloadIndicator {{
                background-color: {colors['content_container']};
            }}
            
            DownloadIndicator #content {{
                background-color: {colors['content_container']};
            }}
            
            DownloadIndicator #expand-btn {{
                background-color: transparent;
                border: none;
                padding: 4px;
                border-radius: 4px;
                color: {colors['text_secondary']};
                font-size: 11px;
            }}
            
            DownloadIndicator #expand-btn:hover {{
                background-color: {colors['hover']};
                color: {colors['text']};
            }}
            
            DownloadIndicator #active-value, 
            DownloadIndicator #waiting-value, 
            DownloadIndicator #completed-value, 
            DownloadIndicator #failed-value {{
                font-size: 16px;
                font-weight: bold;
            }}
            
            DownloadIndicator #active-label, 
            DownloadIndicator #waiting-label, 
            DownloadIndicator #completed-label, 
            DownloadIndicator #failed-label {{
                color: {colors['text_secondary']};
                font-size: 11px;
            }}
            
            DownloadIndicator #status-label {{
                color: {colors['text_secondary']};
                font-size: 11px;
                padding: 2px;
            }}
            
            DownloadIndicator #active-value {{ color: {colors['status']['downloading']}; }}
            DownloadIndicator #waiting-value {{ color: {colors['status']['paused']}; }}
            DownloadIndicator #completed-value {{ color: {colors['status']['completed']}; }}
            DownloadIndicator #failed-value {{ color: {colors['status']['failed']}; }}

            /* AddLink Dialog Styles */
            AddLink {{
                background-color: {colors['content_area']};
            }}

            AddLink #input-label {{
                background-color: transparent;
                height: 30px;
                margin: 0;
                padding: 0;
            }}

            AddLink #label {{
                background-color: transparent;
                height: 30px;
                min-width: 50px;
                padding: 0;
                font-weight: bold;
                color: {colors['text']};
            }}

            AddLink #entry {{
                height: 30px;
                border: none;
                border-radius: 3px;
                background-color: {colors['content_container']};
                color: {colors['text']};
            }}

            AddLink #change-path-btn {{
                height: 30px;
                border: none;
                border-radius: 3px;
                background-color: {colors['accent']};
                width: 30px;
                color: white;
            }}

            AddLink #submit-btn {{
                min-height: 40px;
                height: 40px;
                border: none;
                border-radius: 3px;
                background-color: {colors['accent']};
                padding: 0 20px;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }}

            AddLink #warning-label {{
                height: 30px;
                margin: 0;
                padding: 0;
                color: {colors['text']};
            }}

            AddLink QLineEdit {{
                color: {colors['text']};
            }}

            /* AddLink Step 2 Styles */
            AddLink #summary-label {{
                font-size: 16px;
                font-weight: bold;
                color: {colors['text']};
                padding: 5px 0;
            }}
            
            AddLink #details-frame {{
                background-color: {colors['content_container']};
                border-radius: 6px;
                padding: 15px;
            }}
            
            AddLink #info-label {{
                color: {colors['text']};
                padding: 5px 0;
            }}
            
            AddLink #back-btn {{
                background-color: {colors['button']};
                color: {colors['text']};
            }}
            
            AddLink #download-btn {{
                background-color: {colors['accent']};
                color: white;
            }}
            
            AddLink #back-btn:hover {{
                background-color: {colors['hover']};
            }}
            
            AddLink #download-btn:hover {{
                background-color: {colors['accent_hover']};
            }}

            /* Network Status Styles */
            #sidebar #network-status {{
                background-color: transparent;
                border-radius: 10px;
                margin: 2px;
                width: 40px;
                height: 40px;
            }}

            #sidebar #network-status:hover {{
                background-color: {colors['hover']};
            }}
        """
