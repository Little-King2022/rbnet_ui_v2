
import os
import shutil
import socket
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QMessageBox
)

class DiagnosticsPage(QWidget):
    """
    Page for displaying system diagnostics and device status.
    """
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Timer to refresh stats
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_stats)
        self.timer.start(5000) # Every 5 seconds
        self.refresh_stats()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- System Status ---
        self.system_group = QGroupBox()
        system_layout = QFormLayout(self.system_group)

        self.disk_usage_label = QLabel("Loading...")
        self.memory_usage_label = QLabel("Loading...")
        self.load_avg_label = QLabel("Loading...")
        
        self.label_disk = QLabel()
        self.label_mem = QLabel()
        self.label_load = QLabel()
        
        system_layout.addRow(self.label_disk, self.disk_usage_label)
        system_layout.addRow(self.label_mem, self.memory_usage_label)
        system_layout.addRow(self.label_load, self.load_avg_label)
        
        # --- Model Status ---
        self.model_group = QGroupBox()
        model_layout = QFormLayout(self.model_group)
        
        engine_file_label = QLabel("/home/jetson/RBNet/Stage2/work_dirs/deeplabv3plus_all/best.pth")
        self.inference_time_label = QLabel(" 2.7s")

        self.label_engine = QLabel()
        self.label_infer = QLabel()
        
        model_layout.addRow(self.label_engine, engine_file_label)
        model_layout.addRow(self.label_infer, self.inference_time_label)

        # --- Network Status ---
        self.network_group = QGroupBox()
        network_layout = QVBoxLayout(self.network_group)

        self.check_connection_button = QPushButton()
        self.check_connection_button.clicked.connect(self.check_connection)
        
        network_layout.addWidget(self.check_connection_button)

        layout.addWidget(self.system_group)
        layout.addWidget(self.model_group)
        layout.addWidget(self.network_group)
        layout.addStretch()
        
        self.retranslateUi()

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.system_group.setTitle(self.tr("System Status"))
        self.label_disk.setText(self.tr("Disk Usage:"))
        self.label_mem.setText(self.tr("Memory Usage:"))
        self.label_load.setText(self.tr("Load Avg:"))
        
        self.model_group.setTitle(self.tr("Model Load Status"))
        self.label_engine.setText("Model Weight File:")
        self.label_infer.setText(self.tr("Avg Inference Time:"))
        
        self.network_group.setTitle(self.tr("Network Connectivity"))
        self.check_connection_button.setText(self.tr("Check Server Connection"))

    def refresh_stats(self):
        """Refreshes system statistics."""
        # Disk Usage
        try:
            total, used, free = shutil.disk_usage("/")
            percent = (used / total) * 100
            self.disk_usage_label.setText(f"{used // (2**30)} GB / {total // (2**30)} GB ({percent:.1f}%)")
        except:
            self.disk_usage_label.setText("Error reading disk")

        # Memory Usage
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            mem_info = {}
            for line in lines:
                parts = line.split(':')
                if len(parts) == 2:
                    mem_info[parts[0].strip()] = int(parts[1].strip().split()[0])
            
            if 'MemTotal' in mem_info and 'MemAvailable' in mem_info:
                total_mem = mem_info['MemTotal']
                avail_mem = mem_info['MemAvailable']
                used_mem = total_mem - avail_mem
                percent_mem = (used_mem / total_mem) * 100
                self.memory_usage_label.setText(f"{used_mem // 1024} MB / {total_mem // 1024} MB ({percent_mem:.1f}%)")
        except:
            self.memory_usage_label.setText("Error reading memory")

        # Load Avg
        try:
            load = os.getloadavg()
            self.load_avg_label.setText(f"{load[0]:.2f}, {load[1]:.2f}, {load[2]:.2f}")
        except:
            self.load_avg_label.setText("Error reading load")

    def check_connection(self):
        """Checks connection to a public DNS server."""
        self.check_connection_button.setText(self.tr("Checking..."))
        self.check_connection_button.setEnabled(False)
        self.check_connection_button.repaint()
        
        try:
            # Connect to Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            QMessageBox.information(self, self.tr("Network Status"), self.tr("Connected to Internet."))
        except OSError:
            QMessageBox.warning(self, self.tr("Network Status"), self.tr("Connection Failed (No Internet)."))
        finally:
            self.check_connection_button.setText(self.tr("Check Server Connection"))
            self.check_connection_button.setEnabled(True)
