"""Module with all functionality to run the main hub"""
from glasses_hub import GlassesHub
from kinect_hub import KinectHub
import sys
import asyncio
from datetime import datetime

# from imports import tk
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QLabel
from qasync import QEventLoop

import recording_manager

record_manager = recording_manager.RecordingManager()

glasses_hub: GlassesHub = None
kinect_hub: KinectHub = None

def start_glasses_hub(main_widget: QWidget) -> None:
    """Function opening the Glasses Hub"""
    global glasses_hub
    glasses_widget = QWidget()
    glasses_hub = GlassesHub(glasses_widget, record_manager)
    record_manager.glasses_hub = glasses_hub
    print(glasses_hub)

def start_kinect_hub(main_widget: QWidget) -> None:
    """Function opening the Kinect Hub"""
    global kinect_hub
    kinect_hub_widget = QWidget()
    kinect_hub = KinectHub(kinect_hub_widget)
    record_manager.kinect_hub = kinect_hub

def start_recording() -> None:
    if glasses_hub == None or kinect_hub == None:
        print("Error: A hub is not currently running.")
        # note: if one was opened then closed it still exists, deal with it in safety
        return
    if not record_manager.is_glasses_available() or not record_manager.is_kinect_available():
        print("Error: recording currently unavailable.")
        return
    
    recording_folder_name = '_'.join(str(datetime.now()).split(':'))
    kinect_hub.start_recording(recording_folder_name)
    glasses_hub.start_recording(recording_folder_name)

    record_manager.glasses_is_recording = True
    record_manager.kinect_is_recording = True
    
def end_recording() -> None:
    # no need to check, will stop and update if possible
    kinect_hub.stop_recording() # make sure is self updating!
    glasses_hub.stop_recording()
    return

def cancel_recording() -> None:
    # no need to check, will stop and update if possible
    kinect_hub.stop_recording()    #no way to cancel for now
    glasses_hub.cancel_recording()
    return

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

    start_recording_button = QPushButton(main_widget)
    start_recording_button.setText("Start Recording")
    start_recording_button.move(200, 200)
    start_recording_button.clicked.connect(lambda: start_recording())

    end_recording_button = QPushButton(main_widget)
    end_recording_button.setText("End Recording")
    end_recording_button.move(200, 250)
    end_recording_button.clicked.connect(lambda: end_recording())

    cancel_recording_button = QPushButton(main_widget)
    cancel_recording_button.setText("Cancel Recording")
    cancel_recording_button.move(200, 300)
    cancel_recording_button.clicked.connect(lambda: cancel_recording())



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

