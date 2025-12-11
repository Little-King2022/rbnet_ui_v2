from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QPalette
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QPushButton,
    QScrollArea,
    QSizePolicy
)
import os

class ImageViewerDialog(QDialog):
    """
    A full-screen dialog to view an image with scrolling and zooming support.
    """
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Image Viewer"))
        self.setModal(True)
        self.resize(800, 600)
        self.image_path = image_path
        self.scale_factor = 1.0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.Dark)
        self.scroll_area.setWidgetResizable(True)
        
        self.image_label = QLabel()
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(True)
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)

        controls_layout = QHBoxLayout()
        self.zoom_in_btn = QPushButton(self.tr("Zoom In"))
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn = QPushButton(self.tr("Zoom Out"))
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.fit_btn = QPushButton(self.tr("Fit to Window"))
        self.fit_btn.clicked.connect(self.fit_to_window)
        self.close_btn = QPushButton(self.tr("Close"))
        self.close_btn.clicked.connect(self.close)

        controls_layout.addWidget(self.zoom_in_btn)
        controls_layout.addWidget(self.zoom_out_btn)
        controls_layout.addWidget(self.fit_btn)
        controls_layout.addWidget(self.close_btn)
        layout.addLayout(controls_layout)

        self.load_image()

    def load_image(self):
        if self.image_path and os.path.exists(self.image_path):
            self.pixmap = QPixmap(self.image_path)
            self.fit_to_window()
        else:
            self.image_label.setText(self.tr("Image not found"))
            self.pixmap = None

    def zoom_in(self):
        self.scale_image(1.25)

    def zoom_out(self):
        self.scale_image(0.8)

    def scale_image(self, factor):
        if not self.pixmap: return
        self.scale_factor *= factor
        self.scroll_area.setWidgetResizable(False)
        
        new_size = self.scale_factor * self.pixmap.size()
        self.image_label.resize(new_size)
        self.image_label.setPixmap(self.pixmap)

    def fit_to_window(self):
        if not self.pixmap: return
        self.scale_factor = 1.0
        self.scroll_area.setWidgetResizable(True)
        self.image_label.setPixmap(self.pixmap)


class RecordDetailsDialog(QDialog):
    """
    Dialog to show details of a SampleRecord.
    """
    def __init__(self, record, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Record Details"))
        self.resize(900, 600)
        self.record = record
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # --- Left: Image ---
        left_layout = QVBoxLayout()
        self.image_label = QLabel(self.tr("Loading Image..."))
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid #ccc; background-color: #eee;")
        self.image_label.setCursor(Qt.PointingHandCursor)
        
        self.enlarge_btn = QPushButton(self.tr("View Image"))
        self.enlarge_btn.clicked.connect(self.open_image_viewer)

        left_layout.addWidget(self.image_label)
        left_layout.addWidget(self.enlarge_btn)
        left_layout.addStretch()

        if self.record.raw_image_path and os.path.exists(self.record.raw_image_path):
            pixmap = QPixmap(self.record.raw_image_path)
            self.image_label.setPixmap(pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.image_label.setText(self.tr("No Image Available"))
            self.enlarge_btn.setEnabled(False)

        # --- Right: Details ---
        right_layout = QVBoxLayout()
        
        info_group = QGroupBox(self.tr("Basic Info"))
        info_layout = QVBoxLayout(info_group)
        
        # Note: formatting strings is tricky for translation. 
        # Ideally: self.tr("<b>Time:</b> %1<br>...").arg(...)
        # For simplicity, I'll translate labels.
        info_label = QLabel(
            f"<b>{self.tr('Sample ID')}:</b> {self.record.sample_id}<br>"
            f"<b>{self.tr('Time')}:</b> {self.record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br>"
            f"<b>{self.tr('Plot ID')}:</b> {self.record.plot_id}<br>"
            f"<b>{self.tr('Cultivar')}:</b> {self.record.cultivar}<br>"
            f"<b>{self.tr('Stage')}:</b> {self.record.growth_stage}<br>"
            f"<b>{self.tr('Mean DS')}:</b> {self.record.mean_ds}%<br>"
            f"<b>{self.tr('Severity')}:</b> {self.record.severity_class}<br>"
            f"<b>{self.tr('Notes')}:</b> {self.record.notes}"
        )
        info_layout.addWidget(info_label)
        
        table_group = QGroupBox(self.tr("Leaf Data"))
        table_layout = QVBoxLayout(table_group)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([self.tr("Leaf ID"), self.tr("DS (%)"), self.tr("Severity")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.table.setRowCount(len(self.record.leaf_results))
        for row, leaf in enumerate(self.record.leaf_results):
            self.table.setItem(row, 0, QTableWidgetItem(str(leaf.leaf_id)))
            self.table.setItem(row, 1, QTableWidgetItem(str(leaf.ds_value)))
            self.table.setItem(row, 2, QTableWidgetItem(leaf.severity_class))
            
        table_layout.addWidget(self.table)

        right_layout.addWidget(info_group)
        right_layout.addWidget(table_group)
        
        close_btn = QPushButton(self.tr("Close"))
        close_btn.clicked.connect(self.accept)
        right_layout.addWidget(close_btn)

        layout.addLayout(left_layout, 1)
        layout.addLayout(right_layout, 1)

    def open_image_viewer(self):
        if self.record.raw_image_path:
            viewer = ImageViewerDialog(self.record.raw_image_path, self)
            viewer.showFullScreen()
            viewer.exec()