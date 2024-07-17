"""Module with all functionality to run the main hub"""
from glasses_hub import GlassesHub
from kinect_hub import KinectHub
import sys
import asyncio
from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
# from imports import tk
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QLabel, QVBoxLayout, QSizePolicy

from qasync import QEventLoop

from imports import rec_manager
record_manager = rec_manager()

glasses_hub: GlassesHub = None
kinect_hub: KinectHub = None

def close_glasses_hub(event) -> None:
    """Function kills glasses_hub"""
    global glasses_hub
    glasses_hub.__del__()
    glasses_hub = None
    
def close_kinect_hub(event) -> None:
    """Function kills kinect_hub"""
    global kinect_hub
    kinect_hub.__del__()
    kinect_hub = None

def start_glasses_hub(main_widget: QWidget) -> None:
    """Function opening the Glasses Hub"""
    global glasses_hub
    glasses_widget = QWidget()
    glasses_hub = GlassesHub(glasses_widget, record_manager, close_glasses_hub)
    record_manager.glasses_hub = glasses_hub
    print(glasses_hub)

def start_kinect_hub(main_widget: QWidget) -> None:
    """Function opening the Kinect Hub"""
    global kinect_hub
    kinect_hub_widget = QWidget()
    kinect_hub = KinectHub(kinect_hub_widget, record_manager, close_kinect_hub)
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
    kinect_hub.start_recording_depth(recording_folder_name)
    # kinect_hub.start_recording(recording_folder_name)
    glasses_hub.start_recording(recording_folder_name)

    record_manager.glasses_is_recording = True
    record_manager.kinect_is_recording = True
    
def end_recording() -> None:
    # no need to check, will stop and update if possible
    if glasses_hub is not None:
        if record_manager.glasses_is_connected and record_manager.glasses_is_recording:
            glasses_hub.stop_recording()
    if kinect_hub is not None:
        if record_manager.kinect_is_recording:
            kinect_hub.stop_recording()
    # if (end_kinect): kinect_hub.stop_recording() # make sure is self updating!
    # if (end_glasses): glasses_hub.stop_recording()
    return

def cancel_recording() -> None:
    # no need to check, will stop and update if possible
    if glasses_hub is not None:
        if record_manager.glasses_is_connected and record_manager.glasses_is_recording:
            glasses_hub.cancel_recording()
    if kinect_hub is not None:
        if record_manager.kinect_is_recording:
            kinect_hub.stop_recording()
    return

def define_main_ui(main_widget: QWidget) -> None:
    """Function defining all of the UI elements of the main hub"""

    main_widget.setWindowTitle("Main Hub")
    main_widget.setGeometry(500, 500, 400, 400)  # Smaller screen size

    # Set background color
    main_widget.setAutoFillBackground(True)
    palette = main_widget.palette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    main_widget.setPalette(palette)

    # Create the title
    title = QLabel("Main Hub", main_widget)
    title.setAlignment(Qt.AlignCenter)

    # Create buttons
    glasses_hub_btn = QPushButton("Glasses Hub", main_widget)
    glasses_hub_btn.setStyleSheet("background-color: lightblue;")

    kinect_hub_btn = QPushButton("Kinect Hub", main_widget)
    kinect_hub_btn.setStyleSheet("background-color: lightgreen;")

    start_recording_button = QPushButton("Start Recording", main_widget)
    start_recording_button.setStyleSheet("background-color: orange; font-weight: bold;")

    end_recording_button = QPushButton("End Recording", main_widget)
    end_recording_button.setStyleSheet("background-color: red; font-weight: bold; color: white;")

    cancel_recording_button = QPushButton("Cancel Recording", main_widget)
    cancel_recording_button.setStyleSheet("background-color: lightcoral;")

    # Connect buttons to functions
    glasses_hub_btn.clicked.connect(lambda: start_glasses_hub(main_widget))
    kinect_hub_btn.clicked.connect(lambda: start_kinect_hub(main_widget))
    start_recording_button.clicked.connect(lambda: start_recording())
    end_recording_button.clicked.connect(lambda: end_recording())
    cancel_recording_button.clicked.connect(lambda: cancel_recording())

    # Create layouts
    vbox = QVBoxLayout()
    vbox.addWidget(title)
    vbox.addWidget(glasses_hub_btn)
    vbox.addWidget(kinect_hub_btn)
    vbox.addWidget(start_recording_button)
    vbox.addWidget(end_recording_button)
    vbox.addWidget(cancel_recording_button)

    # Set layout to main_widget
    main_widget.setLayout(vbox)

    # Make widgets stretch properly when resizing
    title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    glasses_hub_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    kinect_hub_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    start_recording_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    end_recording_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    cancel_recording_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


    # main_widget.setWindowTitle("Main Hub")
    # main_widget.setGeometry(500, 500, 500, 500)

    # # Create the title
    # title = QLabel(main_widget)
    # title.setText("Main Hub")
    # title.move(200, 0)

    
    # # Create the button for the glasses hub
    # glasses_hub_btn = QPushButton(main_widget)
    # glasses_hub_btn.setText("Glasses Hub")
    # glasses_hub_btn.move(200, 100)
    # glasses_hub_btn.clicked.connect(lambda: start_glasses_hub(main_widget))

    # # Create the button for the kinect hub
    # kinect_hub_btn = QPushButton(main_widget)
    # kinect_hub_btn.setText("Kinect Hub")
    # kinect_hub_btn.move(200, 150)
    # kinect_hub_btn.clicked.connect(lambda: start_kinect_hub(main_widget))

    # start_recording_button = QPushButton(main_widget)
    # start_recording_button.setText("Start Recording")
    # start_recording_button.move(200, 200)
    # start_recording_button.clicked.connect(lambda: start_recording())

    # end_recording_button = QPushButton(main_widget)
    # end_recording_button.setText("End Recording")
    # end_recording_button.move(200, 250)
    # end_recording_button.clicked.connect(lambda: end_recording(end_kinect=True, end_glasses=True))

    # cancel_recording_button = QPushButton(main_widget)
    # cancel_recording_button.setText("Cancel Recording")
    # cancel_recording_button.move(200, 300)
    # cancel_recording_button.clicked.connect(lambda: cancel_recording())



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