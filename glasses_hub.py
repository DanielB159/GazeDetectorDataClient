"""Module with glasses hub class and methods"""
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel
from qasync import QEventLoop
from imports import asyncio
from imports import g3pylib
from imports import os

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
        self.connection_label.setText(f"Connected to {self.g3.rtsp_url}")
    
    async def disconnect(self):
        self.g3.close()
        self.connection_label.setText("Not Connected")
    
    def define_ui(self):
        """Function defining the UI of the Glasses Hub"""
        self.connection_label : QLabel = QLabel(self.glasses_widget)
        self.connection_label.setText("Not Connected")
        self.connection_label.move(200, 0)

        self.connect_button : QPushButton = QPushButton(self.glasses_widget)
        self.connect_button.setText("Connect")
        self.connect_button.move(200, 100)
        self.connect_button.clicked.connect(lambda: asyncio.ensure_future(self.connect()))

        
        self.connect_button : QPushButton = QPushButton(self.glasses_widget)
        self.connect_button.setText("Disconnect")
        self.connect_button.move(200, 200)
        self.connect_button.clicked.connect(lambda: asyncio.ensure_future(self.disconnect()))
