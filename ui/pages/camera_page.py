
from PySide6.QtCore import Qt, Slot, QThread, Signal, QSettings, QEvent
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QLineEdit
)
import numpy as np

from services.camera_manager import get_camera_manager_thread
from services.rbnet_stub import RbnetStub
from models.entities import SampleRecord

# --- Analysis Worker ---
class AnalysisWorker(QThread):
    """
    Worker thread to run the fake analysis without blocking the UI.
    """
    analysis_complete = Signal(SampleRecord, np.ndarray)

    def __init__(self, image, metadata, parent=None):
        super().__init__(parent)
        self.image = image
        self.metadata = metadata
        self.stub = RbnetStub()

    def run(self):
        """Performs the analysis and emits the result."""
        record = self.stub.analyze(
            self.image,
            plot_id=self.metadata.get("plot_id"),
            cultivar=self.metadata.get("cultivar"),
            growth_stage=self.metadata.get("growth_stage"),
            notes=self.metadata.get("notes"),
        )
        self.analysis_complete.emit(record, self.image)


class CameraPage(QWidget):
    """
    The main page for camera preview, metadata entry, and capturing images for analysis.
    """
    request_pause_preview = Signal()
    request_resume_preview = Signal()
    request_capture_frame = Signal()
    status_forwarder = Signal(str)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.settings = QSettings("RBNet", "FieldSurvey")
        self.analysis_worker = None
        
        self.init_ui()
        self.init_camera()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # --- Left Side: Camera Preview ---
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0,0,0,0)
        self.preview_label = QLabel(self.tr("Initializing Camera..."))
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #333; color: white;")
        
        preview_layout.addWidget(self.preview_label)
        
        # --- Right Side: Controls and Metadata ---
        controls_container = QWidget()
        controls_container.setMaximumWidth(360)
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setSpacing(20)

        # Metadata Group
        self.metadata_group = QGroupBox()
        form_layout = QFormLayout(self.metadata_group)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.plot_id_combo = QComboBox()
        self.plot_id_combo.setEditable(True)

        self.cultivar_combo = QComboBox()
        self.cultivar_combo.setEditable(True)
        
        self.growth_stage_combo = QComboBox()

        self.notes_input = QLineEdit()

        self.label_plot = QLabel()
        form_layout.addRow(self.label_plot, self.plot_id_combo)
        
        self.label_cultivar = QLabel()
        form_layout.addRow(self.label_cultivar, self.cultivar_combo)
        
        self.label_stage = QLabel()
        form_layout.addRow(self.label_stage, self.growth_stage_combo)
        
        self.label_notes = QLabel()
        form_layout.addRow(self.label_notes, self.notes_input)

        self.load_options()

        # Action Buttons Group
        self.actions_group = QGroupBox()
        actions_layout = QVBoxLayout(self.actions_group)
        
        self.analyze_button = QPushButton()
        self.analyze_button.setFixedHeight(50)
        self.analyze_button.setStyleSheet("font-size: 18px; background-color: #007bff; color: white;font-weight: bold;")
        self.analyze_button.clicked.connect(self.capture_and_analyze)

        self.pause_button = QPushButton()
        self.pause_button.setFixedHeight(50)
        self.pause_button.clicked.connect(self.toggle_pause)
        
        actions_layout.addWidget(self.analyze_button)
        actions_layout.addWidget(self.pause_button)
        
        controls_layout.addWidget(self.metadata_group)
        controls_layout.addWidget(self.actions_group)
        controls_layout.addStretch()

        layout.addWidget(preview_container, 3)
        layout.addWidget(controls_container, 2)
        
        self.retranslateUi()

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.metadata_group.setTitle(self.tr("Sample Info"))
        self.label_plot.setText(self.tr("Plot ID:"))
        self.label_cultivar.setText(self.tr("Cultivar:"))
        self.label_stage.setText(self.tr("Growth Stage:"))
        self.label_notes.setText(self.tr("Notes:"))
        
        self.actions_group.setTitle(self.tr("Actions"))
        self.analyze_button.setText(self.tr("Capture and Analyze"))
        self.pause_button.setText(self.tr("Pause/Resume Preview"))

    def load_options(self):
        # Plot IDs
        plots = self.settings.value("options/plots", [f"PLOT-{i:03}" for i in range(1, 11)])
        if not isinstance(plots, list): plots = [str(plots)] if plots else []
        self.plot_id_combo.clear()
        self.plot_id_combo.addItems([str(p) for p in plots])

        # Cultivars
        cultivars = self.settings.value("options/cultivars", ["Cultivar-A", "Cultivar-B", "IR64", "Minghui 63"])
        if not isinstance(cultivars, list): cultivars = [str(cultivars)] if cultivars else []
        self.cultivar_combo.clear()
        self.cultivar_combo.addItems([str(c) for c in cultivars])

        # Growth Stages
        stages = self.settings.value("options/stages", ["Tillering", "Stem Elongation", "Booting", "Heading/Flowering"])
        if not isinstance(stages, list): stages = [str(stages)] if stages else []
        self.growth_stage_combo.clear()
        self.growth_stage_combo.addItems([str(s) for s in stages])

    @Slot()
    def refresh_options(self):
        self.load_options()

    def init_camera(self):
        self.camera_thread, self.camera_manager = get_camera_manager_thread()
        
        self.camera_manager.new_frame.connect(self.update_preview)
        self.camera_manager.status_changed.connect(self.update_status)
        self.camera_manager.frame_captured.connect(self.on_frame_captured)

        self.request_pause_preview.connect(self.camera_manager.pause_preview)
        self.request_resume_preview.connect(self.camera_manager.resume_preview)
        self.request_capture_frame.connect(self.camera_manager.capture_frame_for_analysis)

        self.is_paused = False
        self.camera_thread.start()

    @Slot(QImage)
    def update_preview(self, image):
        pixmap = QPixmap.fromImage(image)
        self.preview_label.setPixmap(pixmap.scaled(
            self.preview_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    @Slot(str)
    def update_status(self, status):
        # Translate status if possible, or just emit
        self.status_forwarder.emit(status)
        if "暂停" in status or "paused" in status.lower():
            self.is_paused = True
        elif "预览中" in status or "previewing" in status.lower():
            self.is_paused = False

    def toggle_pause(self):
        if not self.is_paused:
            self.request_pause_preview.emit()
        else:
            self.request_resume_preview.emit()
    
    def capture_and_analyze(self):
        self.analyze_button.setEnabled(False)
        self.analyze_button.setText(self.tr("Capturing..."))
        self.request_capture_frame.emit()

    @Slot(np.ndarray)
    def on_frame_captured(self, frame):
        self.update_status("Frame captured. Starting analysis...")
        self.analyze_button.setText(self.tr("Analyzing..."))
        
        metadata = {
            "plot_id": self.plot_id_combo.currentText(),
            "cultivar": self.cultivar_combo.currentText(),
            "growth_stage": self.growth_stage_combo.currentText(),
            "notes": self.notes_input.text(),
        }

        self.analysis_worker = AnalysisWorker(frame, metadata)
        self.analysis_worker.analysis_complete.connect(self.on_analysis_complete)
        self.analysis_worker.finished.connect(self.on_worker_finished)
        self.analysis_worker.start()

    @Slot(SampleRecord, np.ndarray)
    def on_analysis_complete(self, record, image):
        self.update_status(f"Analysis complete. Mean DS: {record.mean_ds}%")
        self.main_window.go_to_result_page(record, image)

    def on_worker_finished(self):
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText(self.tr("Capture and Analyze"))
        self.analysis_worker = None

    def start_camera(self):
        if not self.camera_thread.isRunning():
            self.camera_thread.start()
        else:
            self.request_resume_preview.emit()

    def stop_camera(self):
        if self.camera_thread.isRunning():
            self.request_pause_preview.emit()
    
    def shutdown_camera_thread(self):
        if self.camera_thread.isRunning():
            self.camera_thread.quit()
            self.camera_thread.wait(2000)
            if self.camera_thread.isRunning():
                print("Warning: Camera thread did not shut down gracefully.")
