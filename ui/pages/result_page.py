from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QMessageBox
)
import cv2
import numpy as np

from models.entities import SampleRecord
from services.data_manager import DataManager

class ResultPage(QWidget):
    """
    Displays the analysis results of a single sample.
    """
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window 
        self.current_record = None
        self.current_image = None
        self.data_manager = DataManager()
        self.init_ui()

    def set_main_window(self, main_window):
        self.main_window = main_window

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Left side: Summary and Image ---
        left_layout = QVBoxLayout()
        self.summary_label = QLabel("Average DS: --% (---)")
        self.summary_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.metadata_label = QLabel("Plot: -- | Cultivar: -- | Stage: --")
        self.metadata_label.setStyleSheet("font-size: 14px;")

        self.image_label = QLabel()
        self.image_label.setMinimumSize(480, 360)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #ddd;")
        
        left_layout.addWidget(self.summary_label)
        left_layout.addWidget(self.metadata_label)
        left_layout.addWidget(self.image_label)
        left_layout.addStretch()

        # --- Right side: Leaf results table and actions ---
        right_layout = QVBoxLayout()
        
        self.table_group = QGroupBox()
        table_layout = QVBoxLayout(self.table_group)
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        table_layout.addWidget(self.results_table)

        self.actions_group = QGroupBox()
        actions_layout = QHBoxLayout(self.actions_group)

        self.save_button = QPushButton()
        self.save_button.setMinimumHeight(60)
        self.save_button.clicked.connect(self.save_record)
        
        self.discard_button = QPushButton()
        self.discard_button.setMinimumHeight(60)
        self.discard_button.clicked.connect(self.discard_record)

        actions_layout.addWidget(self.save_button)
        actions_layout.addWidget(self.discard_button)

        right_layout.addWidget(self.table_group)
        right_layout.addWidget(self.actions_group)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)
        
        self.retranslateUi()

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.image_label.setText(self.tr("Original Image"))
        self.table_group.setTitle(self.tr("Leaf-level Results"))
        self.results_table.setHorizontalHeaderLabels([self.tr("Leaf ID"), self.tr("DS (%)"), self.tr("Severity")])
        self.actions_group.setTitle(self.tr("Actions"))
        self.save_button.setText(self.tr("Save Record"))
        self.discard_button.setText(self.tr("Discard"))
        
        # Note: Summary and Metadata labels are dynamic content, updated in set_result.
        # But if language changes while displaying result, we should re-update text.
        if self.current_record:
            self.update_info_labels()

    def set_result(self, record: SampleRecord, image: np.ndarray = None):
        if not self.main_window:
            if isinstance(self.parent(), QWidget) and hasattr(self.parent().parent(), 'go_to_camera_page'):
                 self.main_window = self.parent().parent()

        self.current_record = record
        self.current_image = image
        
        self.update_info_labels()
        
        if image is not None:
            h, w, ch = image.shape
            bytes_per_line = ch * w
            qt_image = QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
                self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            self.image_label.setText(self.tr("No Image Available"))

        self.results_table.setRowCount(len(record.leaf_results))
        for row, leaf in enumerate(record.leaf_results):
            self.results_table.setItem(row, 0, QTableWidgetItem(str(leaf.leaf_id)))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(leaf.ds_value)))
            self.results_table.setItem(row, 2, QTableWidgetItem(leaf.severity_class)) # Severity class is usually English key (mild/moderate). Should we translate it?
            # Yes, ideally. 
            # self.tr(leaf.severity_class) might work if "mild" is in TS file.

    def update_info_labels(self):
        if not self.current_record: return
        # Translate dynamic labels
        rec = self.current_record
        avg_ds_text = self.tr("Average DS")
        plot_text = self.tr("Plot")
        cult_text = self.tr("Cultivar")
        stage_text = self.tr("Stage")
        
        self.summary_label.setText(f"{avg_ds_text}: {rec.mean_ds}% ({rec.severity_class.capitalize()})")
        self.metadata_label.setText(
            f"{plot_text}: {rec.plot_id} | {cult_text}: {rec.cultivar} | {stage_text}: {rec.growth_stage}"
        )

    def save_record(self):
        if self.current_record:
            try:
                self.data_manager.save_record(self.current_record, self.current_image)
                
                if self.main_window and hasattr(self.main_window, 'history_page'):
                    self.main_window.history_page.add_record(self.current_record)

                QMessageBox.information(self, self.tr("Saved"), self.tr("Record saved successfully."))
                self.go_back_to_camera()
            except Exception as e:
                QMessageBox.critical(self, self.tr("Error"), f"{self.tr('Failed to save record')}: {str(e)}")
        else:
            QMessageBox.warning(self, self.tr("No Record"), self.tr("No record to save."))
    
    def discard_record(self):
        reply = QMessageBox.question(
            self, self.tr("Confirm Discard"), self.tr("Are you sure you want to discard this result?"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.current_record = None
            self.current_image = None
            self.go_back_to_camera()

    def go_back_to_camera(self):
        if self.main_window:
            self.main_window.go_to_camera_page()
        else:
            print("Error: Main window reference not available in ResultPage.")