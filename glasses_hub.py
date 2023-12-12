"""Module with glasses hub class and methods"""
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel
from qasync import QEventLoop

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
    
    def define_ui(self):
        """Function defining the UI of the Glasses Hub"""
