import sys
from PySide6.QtCore import Qt, QSize, QTimer, Slot, QEvent
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QLabel,
    QPushButton,
    QToolBar,
    QToolButton,
    QSizePolicy
)
from PySide6.QtGui import QAction, QIcon
from datetime import datetime

# Placeholder page widgets for now
# In the next steps, we will replace these with the actual page implementations
from ui.pages.camera_page import CameraPage
from ui.pages.history_page import HistoryPage
from ui.pages.export_page import ExportPage
from ui.pages.settings_page import SettingsPage
from ui.pages.diagnostics_page import DiagnosticsPage
from ui.pages.result_page import ResultPage


class MainWindow(QMainWindow):
    """
    The main application window containing the status bar, navigation,
    and the stacked widget for managing different pages.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RBNet Field Survey")
        self.setFixedSize(1024, 600)
        
        self.init_ui()
        self.init_status_bar()
        self.init_nav_bar()
        self.retranslateUi()
        
    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.setWindowTitle(self.tr("RBNet Field Survey"))
        self.software_name_label.setText(self.tr("RBNet Field Survey Tool - V1.0  "))
        
        # Nav buttons
        self.nav_buttons["survey"].setText(self.tr("Survey"))
        self.nav_buttons["history"].setText(self.tr("History"))
        self.nav_buttons["export"].setText(self.tr("Export"))
        self.nav_buttons["settings"].setText(self.tr("Settings"))
        self.nav_buttons["diagnostics"].setText(self.tr("Diagnostics"))
        self.nav_buttons["exit"].setText(self.tr("Exit"))

    def init_ui(self):
        """Initializes the main UI components, including the stacked widget."""
        # The QStackedWidget will hold all the different pages of the application
        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)

        # Create and add pages
        self.camera_page = CameraPage(self) # Pass main window reference
        self.result_page = ResultPage(self) # Pass main window reference
        self.history_page = HistoryPage()
        self.export_page = ExportPage()
        self.settings_page = SettingsPage()
        self.diagnostics_page = DiagnosticsPage()

        self.pages.addWidget(self.camera_page)
        self.pages.addWidget(self.result_page)
        self.pages.addWidget(self.history_page)
        self.pages.addWidget(self.export_page)
        self.pages.addWidget(self.settings_page)
        self.pages.addWidget(self.diagnostics_page)
        
        # Connect signals from pages to main window slots
        self.camera_page.status_forwarder.connect(self.update_camera_status)
        self.settings_page.settings_changed.connect(self.camera_page.refresh_options)
        
    def init_status_bar(self):
        """Creates the top status bar using the built-in QStatusBar."""
        status_bar = self.statusBar()
        
        # Add normal widgets to the left side
        self.camera_status_label = QLabel("Camera: Initializing...")
        status_bar.addWidget(self.camera_status_label)

        # Add permanent widgets to the right side
        self.software_name_label = QLabel()
        self.time_label = QLabel("00:00")
        self.date_label = QLabel(datetime.now().strftime("%Y-%m-%d"))

        status_bar.addPermanentWidget(self.date_label)
        status_bar.addPermanentWidget(self.time_label)
        status_bar.addPermanentWidget(self.software_name_label)

        # Timer to update the clock
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(995) # Update every second
        self.update_time()

    def init_nav_bar(self):
        """Creates the bottom navigation toolbar."""
        self.nav_bar = QToolBar("Navigation")
        self.nav_bar.setMovable(False)
        self.nav_bar.setIconSize(QSize(32, 32)) # Smaller icon
        self.nav_bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.BottomToolBarArea, self.nav_bar)
        
        self.nav_buttons = {}

        actions = [
            ("Survey", self.go_to_camera_page, "survey"),
            ("History", self.go_to_history_page, "history"),
            ("Export", self.go_to_export_page, "export"),
            ("Settings", self.go_to_settings_page, "settings"),
            ("Diagnostics", self.go_to_diagnostics_page, "diagnostics"),
            ("Exit", self.close, "exit"),
        ]
        
        # Add a spacer to push buttons to be evenly distributed
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.nav_bar.addWidget(spacer)

        for text, slot, key in actions:
            button = QToolButton()
            # Text will be set in retranslateUi
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setFixedSize(1024/6-3, 70) # Adjusted size for 6 buttons
            button.clicked.connect(slot)
            
            if key == "exit":
                button.setStyleSheet("background-color: #CC4450; color: white;font-weight: bold;")
            self.nav_bar.addWidget(button)
            self.nav_buttons[key] = button

        # Add Exit button
        # exit_button = QToolButton()
        # exit_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        # exit_button.setFixedSize(150, 70)
        # exit_button.clicked.connect(self.close)
        # self.nav_bar.addWidget(exit_button)
        # self.nav_buttons["exit"] = exit_button

        spacer2 = QWidget()
        spacer2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.nav_bar.addWidget(spacer2)

    @Slot(str)
    def update_camera_status(self, status):
        """Updates the camera status label in the status bar."""
        # Note: status comes from CameraPage, which might be translated or not.
        # Ideally status strings should be keys or translated at source.
        self.camera_status_label.setText(f"{self.tr('Camera')}: {status}")

    def update_time(self):
        self.time_label.setText(datetime.now().strftime("%H:%M:%S "))

    # --- Page Navigation Slots ---
    def go_to_page(self, page_widget):
        self.pages.setCurrentWidget(page_widget)
        
    def go_to_camera_page(self):
        self.go_to_page(self.camera_page)
        self.camera_page.start_camera() # Resume camera when returning

    def go_to_history_page(self):
        self.go_to_page(self.history_page)
        self.camera_page.stop_camera() # Stop camera to save power

    def go_to_export_page(self):
        self.go_to_page(self.export_page)
        self.camera_page.stop_camera()

    def go_to_settings_page(self):
        self.go_to_page(self.settings_page)
        self.camera_page.stop_camera()
        
    def go_to_diagnostics_page(self):
        self.go_to_page(self.diagnostics_page)
        self.camera_page.stop_camera()

    def go_to_result_page(self, sample_record, image=None):
        """Switches to the result page and displays the record."""
        self.result_page.set_result(sample_record, image)
        self.pages.setCurrentWidget(self.result_page)
        self.camera_page.stop_camera()

    def closeEvent(self, event):
        """Overrides the close event to ensure threads are shut down."""
        print("Closing application and shutting down camera thread...")
        self.camera_page.shutdown_camera_thread()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())