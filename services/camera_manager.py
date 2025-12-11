
import cv2
import numpy as np
from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QImage


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

    def __init__(self, device_id=0, frame_rate=30):
        super().__init__()
        self.device_id = device_id
        self.frame_rate = frame_rate
        self.capture = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.read_frame)
        self._is_running = False
        self._is_paused = False

    @Slot()
    def start_preview(self):
        if not self._is_running:
            self.capture = cv2.VideoCapture(self.device_id)
            if not self.capture.isOpened():
                self.status_changed.emit("摄像头连接失败")
                self.capture = None
                return
            
            self._is_running = True
            self._is_paused = False
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

    def read_frame(self):
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                # Convert from BGR (OpenCV default) to RGB
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.new_frame.emit(qt_image.copy()) # Emit a copy

    def __del__(self):
        self.stop_preview()

# --- Worker thread for moving CameraManager off the main GUI thread ---
def get_camera_manager_thread(device_id=0, frame_rate=30) -> (QThread, CameraManager):
    """
    Factory function to create and set up a CameraManager in its own thread.
    This is the recommended way to use it to avoid blocking the GUI.
    """
    thread = QThread()
    camera_manager = CameraManager(device_id, frame_rate)
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
