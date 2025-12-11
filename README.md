# RBNet Handheld UI

## Overview

This project is a **PySide6-based User Interface** for the RBNet Rice Blast Field Survey tool. It is designed to run on embedded systems like the **NVIDIA Jetson Nano** or **Jetson Orin Nano** equipped with a USB camera and a touchscreen.

The application serves as a field data collection tool, allowing users to capture images of rice leaves, input field metadata, and simulate disease severity analysis (simulating the RBNet deep learning model).

## Key Features

*   **Touch-Friendly Interface:** Optimized for 1024x600 touchscreens with large buttons and high-contrast visuals for outdoor visibility.
*   **Real-Time Preview:** Live camera feed using OpenCV.
*   **Field Data Collection:** Easy entry of metadata such as Plot ID, Cultivar, and Growth Stage.
*   **Simulated Analysis:** "Stubbed" RBNet inference module that generates realistic mock data for Disease Severity (DS) and severity classification.
*   **Result Visualization:** Displays leaf-level results and overall severity (Mild, Moderate, Severe).
*   **History & Export:** View past records and simulated export functionality.
*   **Offline First:** Designed to work without an internet connection.

## Prerequisites

*   **Hardware:**
    *   NVIDIA Jetson Nano / Orin Nano (or any Linux/Windows PC for testing)
    *   USB Webcam
    *   Touchscreen (1024x600 recommended)
*   **Software:**
    *   Python 3.10+
    *   PySide6
    *   OpenCV
    *   NumPy

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd rbnet_ui_v2
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install PySide6 opencv-python numpy
    ```
    *(Note: On Jetson devices, you might need to install OpenCV via system packages or build from source if pre-built wheels are not compatible.)*

## Usage

To start the application:

```bash
python main.py
```

The application launches in **Full Screen** mode by default.

## Project Structure

*   **`main.py`**: Application entry point. Sets up the main window and global styles.
*   **`ui/`**: Contains all user interface logic.
    *   `main_window.py`: The main container managing navigation.
    *   `pages/`: Individual screens (Camera, Result, History, Export, Settings).
*   **`services/`**: Backend logic.
    *   `camera_manager.py`: Handles webcam access and frame capture.
    *   `rbnet_stub.py`: Simulates the RBNet analysis engine (generates fake data for demonstration).
    *   `data_manager.py`: Manages saving and loading of survey records.
*   **`models/`**: Data classes (`SampleRecord`, `LeafResult`).
*   **`translations/`**: Translation files for localization (currently supporting Chinese).

## Future Roadmap

This demo is intended as a foundation. Future steps for full implementation include:
1.  Replacing `services/rbnet_stub.py` with the actual TensorRT/ONNX runtime for `RBNet`.
2.  Implementing actual image saving and database persistence in `services/data_manager.py`.
3.  Connecting the `ExportPage` to real USB mount points or cloud APIs.

## License


