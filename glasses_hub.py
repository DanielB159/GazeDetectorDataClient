"""Module with glasses hub class and methods"""
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel
from qasync import QEventLoop
from imports import asyncio
from imports import g3pylib
from imports import os
from imports import cv2

class GlassesHub:
    """Class representing the Kinect Hub"""

    _instance = None
    _is_initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GlassesHub, cls).__new__(cls)
        return cls._instance

    def __init__(self, glasses_hub_widget: QWidget):
        if not self._is_initialized:
            self._is_initialized = True
            self.glasses_widget : QWidget = glasses_hub_widget
            self.glasses_widget.setWindowTitle("Glasses Hub")
            self.glasses_widget.setGeometry(500, 500, 500, 500)
            self.glasses_widget.closeEvent = self.closeEvent
            self.define_ui()
            self.glasses_widget.show()

    def closeEvent(self, event):
        """Function to handle the close event"""
        self._instance = None
        self._is_initialized = False
        del self

    async def connect(self):
        """Function to connect machine to glasses"""
        self.g3 = await g3pylib.connect_to_glasses.with_hostname(os.environ["G3_HOSTNAME"])
        self.connection_label.setText(f"Status: Connected to {self.g3.rtsp_url}")
    
    async def disconnect(self):
        await self.g3.close()
        self.connection_label.setText("Status: Not Connected")
    
    async def calibrate(self):
        out = await self.g3.calibrate.run()
        if (out):
            print("Calibration successful.")
        else:
            print("Calibration failed.")

    async def lv_start(self):
        async with self.g3.stream_rtsp(scene_camera=True) as streams:
            async with streams.scene_camera.decode() as decoded_stream:        
                cv2.namedWindow("Live View", cv2.WINDOW_NORMAL)
                for _ in range(300):
                    frame, _timestamp = await decoded_stream.get()
                    image = frame.to_ndarray(format="bgr24")
                    cv2.imshow("Live View", image)  # type: ignore
                    cv2.waitKey(1)  # type: ignore
    
    def define_ui(self):
        """Function defining the UI of the Glasses Hub"""
        self.connection_label : QLabel = QLabel(self.glasses_widget)
        self.connection_label.resize(1000, 20)
        self.connection_label.setText("Status: Not Connected")

        self.connect_button : QPushButton = QPushButton(self.glasses_widget)
        self.connect_button.setText("Connect")
        self.connect_button.move(0, 50)
        self.connect_button.clicked.connect(lambda: asyncio.ensure_future(self.connect()))
        
        self.disconnect_button : QPushButton = QPushButton(self.glasses_widget)
        self.disconnect_button.setText("Disconnect")
        self.disconnect_button.move(100, 50)
        self.disconnect_button.clicked.connect(lambda: asyncio.ensure_future(self.disconnect()))

        self.calibrate_button : QPushButton = QPushButton(self.glasses_widget)
        self.calibrate_button.setText("Calibrate")
        self.calibrate_button.move(0, 150)
        self.calibrate_button.clicked.connect(lambda: asyncio.ensure_future(self.calibrate()))

        self.lv_start_button : QPushButton = QPushButton(self.glasses_widget)
        self.lv_start_button.setText("Start Live View")
        self.lv_start_button.move(0, 250)
        self.lv_start_button.clicked.connect(lambda: asyncio.ensure_future(self.lv_start()))

        


