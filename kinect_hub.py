"""Module with kinect hub class and methods"""
#pylint: disable=no-member
import pykinect_azure as pykinect
# import numpy as np
import cv2
import threading
import time
from pykinect_azure.k4arecord import Record, RecordConfiguration, Playback
from pykinect_azure.k4a import Device, Capture, Image
from pykinect_azure.k4a._k4a import k4a_image_get_system_timestamp_nsec, k4a_image_get_device_timestamp_usec, k4a_image_get_timestamp_usec
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel
from qasync import QEventLoop



class KinectHub:
    """Class representing the Kinect Hub"""

    _instance = None
    _is_initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KinectHub, cls).__new__(cls)
        return cls._instance

    def __init__(self, main_hub_widget: QWidget):
        if not self._is_initialized:
            self._is_initialized : bool = True
            self.device : Device = None
            self.current_image : Image = None
            self.main_hub_widget : QWidget = main_hub_widget
            # define the device configuration
            self.device_config = pykinect.default_configuration
            self.device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
            # define the device UI
            self.define_ui()
            self.main_hub_widget.show()

    def define_ui(self):
        """Function defining the UI of the Kinect Hub"""
        self.main_hub_widget.setWindowTitle("Kinect Hub")
        self.main_hub_widget.setGeometry(500, 500, 500, 500)
        self.main_hub_widget.closeEvent = self.closeEvent
        kinect_hub_title = QLabel(self.main_hub_widget)
        kinect_hub_title.setText("Kinect Hub")
        kinect_hub_title.move(200, 0)
        live_view_btn : QPushButton = QPushButton(self.main_hub_widget)
        live_view_btn.setText("Live View")
        live_view_btn.move(200, 100)
        live_view_btn.clicked.connect(self.live_view)
        start_rec_btn : QPushButton = QPushButton(self.main_hub_widget)
        start_rec_btn.setText("Start recording")
        start_rec_btn.move(200, 150)
        start_rec_btn.clicked.connect(self.start_recording)

    def closeEvent(self, event):
        """Function to handle the close event"""
        self._instance = None
        self._is_initialized = False
        del self
    
    # def capture_image(self):
    #     """Function to capture an image from the kinect camera"""
    #     self.configure_kinect()
    #     if self.device is None:
    #         return
    
    # def capture_image_thread(self):
    #     """Function to capture an image from the kinect camera"""
    #     # Get a capture from the device
    #     capture: Capture = self.device.update()
    #     ret: bool
    #     raw_color_image: Image
    #     # Get the color image from the capture
    #     ret, raw_color_image = capture.get_color_image()

    #     # if the capture did not succeed, then continue

    def start_recording(self):
        """Function to start recording the kinect camera"""
        self.configure_kinect()
        if self.device is None:
            return
        threading.Thread(target=self.start_recording_thread).start()
    
    def start_recording_thread(self):
        """Function to start recording the kinect camera"""
        recording: Record = Record(self.device.handle(), self.device_config.handle(), "test.mkv") 
        # Record.create_recording(self.device, self.device_config, "test.mkv")
        # sleep for 5 secnods
        time.sleep(5)
        # Stop the recording
        recording.close()
    




    def live_view(self):
        """Function to open the live view in the kinect camera in a seperate thread"""
        self.configure_kinect()
        if self.device is None:
            return
        # Start the live view in a seperate thread
        threading.Thread(target=self.live_view_thread).start()

    def live_view_thread(self):
        """Function to start the live view"""
        cv2.namedWindow("Live View", cv2.WINDOW_NORMAL)
        while True:
            # Get a capture from the device
            capture: Capture = self.device.update()
            ret: bool
            raw_color_image: Image
            # Get the color image from the capture
            self.current_image = capture.get_color_image_object()
            # self.current_image.handle()
            print(k4a_image_get_system_timestamp_nsec(self.current_image._handle))
            print(k4a_image_get_device_timestamp_usec(self.current_image._handle))
            print(k4a_image_get_timestamp_usec(self.current_image._handle))
            ret, raw_color_image = self.current_image.to_numpy()
            # ret, raw_color_image = capture.get_color_image()

            # if the capture did not succeed, then continue
            if not ret:
                continue
            image = cv2.putText(raw_color_image, "Live View", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.imshow("Live View", image)

            # Press q to exit
            if cv2.waitKey(1) == ord('q'):
                break
   
    def configure_camera_sdk_device(self) -> Device:
        """Function to configure the camera"""
        pykinect.initialize_libraries()
        try:
            self.device: Device = pykinect.start_device(config=self.device_config)
        except SystemExit as exception:
            print(exception)
            return None
        
    def configure_kinect(self):
        """Function to configure the device"""
        if self.device is None:
            self.configure_camera_sdk_device()
            