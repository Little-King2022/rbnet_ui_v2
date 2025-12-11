
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from services.i18n_manager import I18nManager

def main():
    """
    The main entry point for the RBNet UI application.
    """
    app = QApplication(sys.argv)

    # Initialize I18n
    i18n = I18nManager()
    i18n.install(app)

    # Global stylesheet for high contrast and large touch targets
    app.setStyleSheet("""
        QWidget {
            background-color: #F0F0F0;
            color: #111;
            font-size: 14pt; /* Reduced from 16pt */
        }
        QMainWindow, QToolBar {
            background-color: #E1E1E1;
        }
        QLabel {
            background-color: transparent;
        }
        QPushButton, QToolButton {
            background-color: #D1D1D1;
            border: 1px solid #B1B1B1;
            padding: 6px; /* Reduced from 8px */
            /*min-height: 20px;  Touch target size 
            min-width: 60px;*/
        }
        QPushButton:hover, QToolButton:hover {
            background-color: #C1C1C1;
        }
        QPushButton:pressed, QToolButton:pressed {
            background-color: #B1B1B1;
        }
        QGroupBox {
            font-size: 13pt;
            font-weight: bold;
            border: 1px solid #B1B1B1;
            border-radius: 5px;
            margin-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            background-color: #F0F0F0;
        }
        QComboBox, QLineEdit {
            padding: 6px; /* Reduced from 8px */
            border: 1px solid #B1B1B1;
            font-size: 12pt; /* Reduced from 14pt */
            min-height: 20px;
        }
        QTableWidget {
            font-size: 12pt; /* Reduced from 14pt */
        }
    """)

    window = MainWindow()
    # To run in full screen mode on the device:
    window.showFullScreen() 
    # window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
