
import cv2
import numpy as np
from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QImage
from pathlib import Path


class CameraManager(QObject):
    """
    Manages camera operations in a separate thread to prevent UI freezing.
    It captures frames, converts them to QImage, and emits them.
    """
    # Signal to send a new frame to the UI
    new_frame = Signal(QImage)
    # Signal to indicate camera status
    status_changed = Signal(str)
    # Signal to provide a captured frame for analysis
    frame_captured = Signal(np.ndarray)

    def __init__(self, device_id=0, frame_rate=30, fallback_image_path: str | None = None):
        super().__init__()
        self.device_id = device_id
        self.frame_rate = frame_rate
        self.capture = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.read_frame)
        self._is_running = False
        self._is_paused = False
        self._read_failures = 0
        self._fallback_image_path = (
            Path(fallback_image_path)
            if fallback_image_path
            else (Path(__file__).resolve().parent.parent / "data" / "test_image" / "IMG_20250324_103853.jpg")
        )
        self._fallback_qimage: QImage | None = None
        self._fallback_rgb_frame: np.ndarray | None = None

    def _load_fallback_qimage(self) -> QImage:
        if self._fallback_qimage is None:
            if self._fallback_image_path.exists():
                self._fallback_qimage = QImage(str(self._fallback_image_path))
            else:
                self._fallback_qimage = QImage()
        return self._fallback_qimage

    def _load_fallback_rgb_frame(self) -> np.ndarray | None:
        if self._fallback_rgb_frame is None:
            if not self._fallback_image_path.exists():
                return None
            bgr = cv2.imread(str(self._fallback_image_path))
            if bgr is None:
                return None
            self._fallback_rgb_frame = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        return self._fallback_rgb_frame

    def _emit_fallback_preview(self, status: str | None = None) -> None:
        fallback = self._load_fallback_qimage()
        if not fallback.isNull():
            self.new_frame.emit(fallback.copy())
        if status:
            self.status_changed.emit(status)

    @Slot()
    def start_preview(self):
        if not self._is_running:
            self.capture = cv2.VideoCapture(self.device_id)
            if not self.capture.isOpened():
                self.status_changed.emit("Status: Preview")
                self.capture = None
                self._emit_fallback_preview()
                return
            
            self._is_running = True
            self._is_paused = False
            self._read_failures = 0
            self.timer.start(1000 // self.frame_rate)
            self.status_changed.emit("预览中")
        elif self._is_paused:
            self.resume_preview()

    @Slot()
    def stop_preview(self):
        if self._is_running:
            self.timer.stop()
            self._is_running = False
            self._is_paused = False
            self._read_failures = 0
            if self.capture:
                self.capture.release()
                self.capture = None
            self.status_changed.emit("摄像头已停止")

    @Slot()
    def pause_preview(self):
        if self._is_running and not self._is_paused:
            self.timer.stop()
            self._is_paused = True
            self.status_changed.emit("预览已暂停")
            
    @Slot()
    def resume_preview(self):
        if not self._is_running:
            self.start_preview()
            return
        if self._is_running and self._is_paused:
            self.timer.start(1000 // self.frame_rate)
            self._is_paused = False
            self.status_changed.emit("预览中")

    @Slot()
    def capture_frame_for_analysis(self):
        """Captures a single high-quality frame for the analysis process."""
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                # Convert to RGB to ensure consistent color across the application
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.pause_preview() # Pause preview after capture
                self.status_changed.emit("已捕获帧，准备分析...")
                self.frame_captured.emit(rgb_frame)
            else:
                self.status_changed.emit("无法捕获帧")
        else:
            rgb_frame = self._load_fallback_rgb_frame()
            if rgb_frame is None:
                self.status_changed.emit("摄像头未连接，且示例图片不可用")
                return
            self.status_changed.emit("摄像头未连接，使用示例图片分析...")
            self.frame_captured.emit(rgb_frame.copy())

    def read_frame(self):
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                self._read_failures = 0
                # Convert from BGR (OpenCV default) to RGB
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.new_frame.emit(qt_image.copy()) # Emit a copy
            else:
                self._read_failures += 1
                if self._read_failures >= 10:
                    # Likely disconnected or in a bad state; fall back to sample preview.
                    self.stop_preview()
                    self._emit_fallback_preview("摄像头读取失败（显示示例图片）")
        elif not self._is_running:
            # Show a stable placeholder when the camera isn't running.
            self._emit_fallback_preview()

    def __del__(self):
        self.stop_preview()

# --- Worker thread for moving CameraManager off the main GUI thread ---
def get_camera_manager_thread(
    device_id=0, frame_rate=30, fallback_image_path: str | None = None
) -> (QThread, CameraManager):
    """
    Factory function to create and set up a CameraManager in its own thread.
    This is the recommended way to use it to avoid blocking the GUI.
    """
    thread = QThread()
    camera_manager = CameraManager(device_id, frame_rate, fallback_image_path=fallback_image_path)
    camera_manager.moveToThread(thread)

    # When the thread starts, automatically start the camera preview
    thread.started.connect(camera_manager.start_preview)
    # When the thread is finishing, stop the camera
    thread.finished.connect(camera_manager.stop_preview)

    return thread, camera_manager

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QPushButton
    import sys

    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Camera Test")
            self.image_label = QLabel("Initializing camera...")
            self.image_label.setFixedSize(640, 480)
            
            self.status_label = QLabel("Status: Unknown")

            self.pause_button = QPushButton("Pause/Resume")
            self.capture_button = QPushButton("Capture for Analysis")

            layout = QVBoxLayout()
            layout.addWidget(self.image_label)
            layout.addWidget(self.status_label)
            layout.addWidget(self.pause_button)
            layout.addWidget(self.capture_button)
            
            container = QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)

            # Setup camera in a separate thread
            self.camera_thread, self.camera_manager = get_camera_manager_thread()

            # Connect signals
            self.camera_manager.new_frame.connect(self.update_image)
            self.camera_manager.status_changed.connect(self.update_status)
            self.camera_manager.frame_captured.connect(self.on_frame_captured)

            self.pause_button.clicked.connect(self.toggle_pause)
            self.capture_button.clicked.connect(self.camera_manager.capture_frame_for_analysis)
            
            self.is_paused = False
            
            # Start the thread
            self.camera_thread.start()

        def toggle_pause(self):
            if self.is_paused:
                self.camera_manager.resume_preview()
            else:
                self.camera_manager.pause_preview()
            self.is_paused = not self.is_paused

        @Slot(QImage)
        def update_image(self, q_image):
            from PySide6.QtGui import QPixmap
            self.image_label.setPixmap(QPixmap.fromImage(q_image).scaled(
                self.image_label.width(), self.image_label.height()
            ))

        @Slot(str)
        def update_status(self, status):
            self.status_label.setText(f"Status: {status}")

        @Slot(np.ndarray)
        def on_frame_captured(self, frame):
            print(f"Frame captured for analysis! Shape: {frame.shape}")
            # Here you would trigger the analysis
            # For the test, we'll just show a message
            self.update_status("Frame captured, ready for analysis.")


        def closeEvent(self, event):
            self.camera_thread.quit()
            self.camera_thread.wait()
            event.accept()

    app = QApplication(sys.argv)
    win = TestWindow()
    win.show()
    sys.exit(app.exec())
