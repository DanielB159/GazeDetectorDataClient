"""Module with all functionality to run the main hub"""
from glasses_hub import GlassesHub
from kinect_hub import KinectHub
import sys
import asyncio

# from imports import tk
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QLabel
from qasync import QEventLoop


def start_glasses_hub(main_widget: QWidget) -> None:
    """Function opening the Glasses Hub"""
    glasses_widget = QWidget()
    glasses_hub: GlassesHub = GlassesHub(glasses_widget)


def start_kinect_hub(main_widget: QWidget) -> None:
    """Function opening the Kinect Hub"""
    kinect_hub_widget = QWidget()
    kinect_hub: KinectHub = KinectHub(kinect_hub_widget)


def define_main_ui(main_widget: QWidget) -> None:
    """Function defining all of the UI elements of the main hub"""

    main_widget.setWindowTitle("Main Hub")
    main_widget.setGeometry(500, 500, 500, 500)

    # Create the title
    title = QLabel(main_widget)
    title.setText("Main Hub")
    title.move(200, 0)

    
    

    # Create the button for the glasses hub
    glasses_hub_btn = QPushButton(main_widget)
    glasses_hub_btn.setText("Glasses Hub")
    glasses_hub_btn.move(200, 100)
    glasses_hub_btn.clicked.connect(lambda: start_glasses_hub(main_widget))

    # Create the button for the kinect hub
    kinect_hub_btn = QPushButton(main_widget)
    kinect_hub_btn.setText("Kinect Hub")
    kinect_hub_btn.move(200, 150)
    kinect_hub_btn.clicked.connect(lambda: start_kinect_hub(main_widget))

def start_main_hub() -> None:
    """Function opening the main hub"""

    # Create the main window
    # Define the main window
    app = QApplication(sys.argv)
    main_widget = QWidget()
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Define the UI
    define_main_ui(main_widget)

    # Show the main window
    main_widget.show()
    loop.run_forever()

