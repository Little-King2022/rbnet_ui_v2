import os
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QRadioButton,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QApplication
)
from services.data_manager import DataManager

class ExportPage(QWidget):
    """
    Page for exporting collected data to various formats and targets.
    """
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Export Target ---
        self.target_group = QGroupBox()
        target_layout = QVBoxLayout(self.target_group)
        
        self.usb_radio = QRadioButton()
        self.local_radio = QRadioButton()
        self.sync_radio = QRadioButton()
        
        self.local_radio.setChecked(True)
        self.sync_radio.setEnabled(False) 
        
        target_layout.addWidget(self.usb_radio)
        target_layout.addWidget(self.local_radio)
        target_layout.addWidget(self.sync_radio)

        # --- Export Options ---
        self.options_group = QGroupBox()
        options_layout = QVBoxLayout(self.options_group)

        self.csv_check = QCheckBox()
        self.csv_check.setChecked(True)
        
        self.raw_image_check = QCheckBox()
        self.raw_image_check.setChecked(True)
        
        options_layout.addWidget(self.csv_check)
        options_layout.addWidget(self.raw_image_check)

        # --- Action Button ---
        self.export_button = QPushButton()
        self.export_button.setMinimumHeight(80)
        self.export_button.setStyleSheet("font-size: 20px; background-color: #28a745; color: white;")
        self.export_button.clicked.connect(self.start_export)

        layout.addWidget(self.target_group)
        layout.addWidget(self.options_group)
        layout.addStretch()
        layout.addWidget(self.export_button)
        
        self.retranslateUi()

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.target_group.setTitle(self.tr("Export Target"))
        self.usb_radio.setText(self.tr("Export to USB Drive"))
        self.local_radio.setText(self.tr("Export to Local Folder"))
        self.sync_radio.setText(self.tr("Wireless Sync"))
        
        self.options_group.setTitle(self.tr("Options"))
        self.csv_check.setText(self.tr("Export CSV with metadata"))
        self.raw_image_check.setText(self.tr("Export Raw Images"))
        
        self.export_button.setText(self.tr("Start Export"))

    def start_export(self):
        target_path = ""
        
        if self.local_radio.isChecked():
            target_path = QFileDialog.getExistingDirectory(self, self.tr("Select Export Directory"))
        elif self.usb_radio.isChecked():
            start_dir = "/media" if os.path.exists("/media") else os.path.expanduser("~")
            target_path = QFileDialog.getExistingDirectory(self, self.tr("Select USB Mount Point"), start_dir)
        
        if not target_path:
            return

        try:
            self.export_button.setEnabled(False)
            self.export_button.setText(self.tr("Exporting..."))
            QApplication.processEvents()

            self.data_manager.export_data(
                target_path,
                export_csv=self.csv_check.isChecked(),
                export_images=self.raw_image_check.isChecked()
            )

            QMessageBox.information(
                self,
                self.tr("Success"),
                self.tr("Data successfully exported to:\n") + target_path
            )
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), f"{self.tr('Export failed')}:\n{e}")
        finally:
            self.export_button.setEnabled(True)
            self.export_button.setText(self.tr("Start Export"))
