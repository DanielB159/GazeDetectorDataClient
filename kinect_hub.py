"""Module with kinect hub class and methods"""
#pylint: disable=no-member
import pykinect_azure as pykinect
# import numpy as np
import cv2
import threading
import time
import sys
import os
import asyncio
import numpy as np
from pykinect_azure.k4arecord import _k4arecord
from pykinect_azure.k4a import _k4a
from pykinect_azure.k4arecord import Playback
from custom_made_libs.record_configuration import RecordConfiguration, default_configuration_record
from pykinect_azure.k4a import Device, Capture, Image, Configuration, ImuSample
from pykinect_azure.k4a._k4a import k4a_image_get_system_timestamp_nsec, k4a_image_get_device_timestamp_usec, k4a_image_get_timestamp_usec
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel, QLineEdit
from qasync import QEventLoop

class KinectHub:
    """Class representing the Kinect Hub"""

    _instance = None
    _is_initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KinectHub, cls).__new__(cls)
        return cls._instance

    def __init__(self, kinect_hub_widget: QWidget):
        if not self._is_initialized:
            self.is_recording: bool = False
            self.is_live_view: bool = False
            self.FILEPATH = self.configure_recordings_file()
            self._is_initialized : bool = True
            self.device : Device = None
            self.device_handle : int = None
            self.current_image : Image = None
            self.kinect_hub_widget : QWidget = kinect_hub_widget
            # define the device configuration
            self.device_config : Configuration = self.get_low_res_configuration()
            self.device_config_rec : RecordConfiguration = self.get_low_res_configuration_rec()
            # define the device UI
            self.define_ui()
            self.kinect_hub_widget.show()

    def define_ui(self) -> None:
        """Function defining the UI of the Kinect Hub"""
        self.kinect_hub_widget.setWindowTitle("Kinect Hub")
        self.kinect_hub_widget.setGeometry(500, 500, 500, 500)
        self.kinect_hub_widget.closeEvent = self.closeEvent
        kinect_hub_title = QLabel(self.kinect_hub_widget)
        kinect_hub_title.setText("Kinect Hub")
        # enlarge the label
        kinect_hub_title.move(200, 0)
        live_view_btn : QPushButton = QPushButton(self.kinect_hub_widget)
        live_view_btn.setText("Live View")
        live_view_btn.move(200, 100)
        live_view_btn.clicked.connect(self.live_view)
        start_rec_btn : QPushButton = QPushButton(self.kinect_hub_widget)
        start_rec_btn.setText("Start recording")
        start_rec_btn.move(200, 150)
        start_rec_btn.clicked.connect(self.start_recording)
        playback_btn: QPushButton = QPushButton(self.kinect_hub_widget)
        playback_btn.setText("Playback")
        playback_btn.move(200, 200)
        playback_btn.clicked.connect(self.start_playback)
        input_playback_filepath: QLineEdit = QLineEdit(self.kinect_hub_widget)
        input_playback_filepath.move(200, 250)


    def closeEvent(self, event) -> None:
        """Function to handle the close event"""
        self._instance = None
        self._is_initialized = False
        del self
    
    def start_playback(self) -> None:
        input_line: QLineEdit = self.kinect_hub_widget.findChild(QLineEdit)
        # check if the input line containts a valid path to an .mkf file
        if not os.path.exists(input_line.text()):
            print("not a valid path")
            return
        # start the playback in a seperate thread
        playback_thread: threading.Thread = threading.Thread(target=self.start_playback_thread, args=(input_line.text(),))
        playback_thread.start()



    def start_playback_thread(self, path) -> None:
        """Function to start playback the kinect camera"""
        pykinect.initialize_libraries()
        playback: Playback = pykinect.start_playback(path)
        # playback_config = playback.get_record_configuration()
        # print(playback_config)
        print("the playback length is " + str(playback.get_recording_length()) + " microseconds")
        cv2.namedWindow('Playback', cv2.WINDOW_NORMAL)
        i = 0
        while True:
            # Get camera capture
            ret, capture = playback.update()
            i += 33739.69512
            print(i)
            if not ret:
                break

            # Get color image
            image_obj: Image = capture.get_color_image_object()
            ret_color, color_image = image_obj.to_numpy()
            

            # get the imu data from the capture
            # imu: ImuSample = playback.get_next_imu_sample()
            # print(imu.acc_timestamp_usec)


            # # Get the colored depth
            # ret_depth, depth_color_image = capture.get_colored_depth_image()

            if not ret_color:
                continue

            # Plot the image
            image : np.ndarray = cv2.putText(color_image, "PlayBack", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.imshow('Playback', image)
            # Press q key to stop
            if cv2.waitKey(30) == ord('q'):
                break
        cv2.destroyWindow("Playback")


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

    def start_recording(self) -> None:
        """Function to start recording the kinect camera"""
        if self.is_live_view:
            print("not able to start recording when in live view")
            return
        self.FILEPATH = self.configure_recordings_file()
        self.configure_camera_rec()
        if self.device is None:
            return
        self.is_recording = True
        live_view_thread : threading.Thread = threading.Thread(target=self.start_recording_thread)
        live_view_thread.start()

    def configure_recordings_file(self) -> str:
        # if the path /recordings does not exist, create it
        i: int = 0
        if not os.path.exists("recordings"):
            os.makedirs("recordings")
        filename_taken: bool = True
        while filename_taken:
            # check find a filename that is not taken 
            if not os.path.exists("recordings/recording" + str(i) + ".mkv"):
                filename_taken = False
            else:
                i += 1
        return "recordings/recording" + str(i) + ".mkv"
            
    def start_recording_thread(self) -> None:
        """Function to start recording the kinect camera"""
        cv2.namedWindow("Recording", cv2.WINDOW_NORMAL)
        while True:
            capture: Capture = self.device.update()
            ret: bool
            raw_color_image: Image
            # Get the color image from the capture
            # self.current_image = capture.get_color_image_object()
            ret, raw_color_image = capture.get_color_image()
            # ret, raw_color_image = capture.get_color_image()

            # if the capture did not succeed, then continue
            if not ret:
                continue
            image : np.ndarray = cv2.putText(raw_color_image, "Recording", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.imshow("Recording", image)

            # Press q to exit
            if cv2.waitKey(1) == ord('q'):
                break
        cv2.destroyWindow("Recording")
        self.stop_kinect()
        self.is_recording = False
    




    def live_view(self) -> None:
        """Function to open the live view in the kinect camera in a seperate thread"""
        if self.is_recording:
            print("not able to start live view when recording")
            return
        self.configure_camera()
        if self.device is None:
            return
        # Start the live view in a seperate thread
        self.is_live_view = True
        live_view_thread: threading.Thread = threading.Thread(target=self.live_view_thread, args=(self.device,))
        live_view_thread.start()
        # Wait for the thread to finish
        # Stop the kinect
        # self.stop_kinect()
        

    def live_view_thread(self, device: Device) -> None:
        """Function to start the live view"""
        cv2.namedWindow("Live View", cv2.WINDOW_NORMAL)
        # sys.stdout = open("output.txt", "w")
        while True:
            # Get a capture from the device
            capture: Capture = device.update()
            imu: ImuSample = device.get_imu_sample()
            ret: bool
            raw_color_image: Image
            # Get the color image from the capture
            # self.current_image = capture.get_color_image_object()
            # self.current_image.handle()
            # print(k4a_image_get_system_timestamp_nsec(self.current_image._handle))
            # print(k4a_image_get_device_timestamp_usec(self.current_image._handle))
            # print(k4a_image_get_timestamp_usec(self.current_image._handle))
            img_obj = capture.get_color_image_object()
            # ret, raw_color_image = capture.get_color_image()
            ret, raw_color_image = img_obj.to_numpy()
            # if the capture did not succeed, then continue
            if not ret:
                continue
            # set the output of prints to be to a file called output.txt
            # print("time:")
            # print(k4a_image_get_device_timestamp_usec(img_obj.handle()))
            # print("imu time acc")
            # print(imu.acc_timestamp_usec)
            # print("imu time gyro")
            # print(imu.gyro_timestamp_usec)
            image : np.ndarray = cv2.putText(raw_color_image, "Live View", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.imshow("Live View", image)

            # Press q to exit
            if cv2.waitKey(1) == ord('q'):
                cv2.destroyWindow("Live View")
                break
        self.stop_kinect()
        self.is_live_view = False
        # print 100 spaces
        # for i in range(100):
        #     print(" ")
        # set the output of prints to be to the console
        # sys.stdout = sys.__stdout__


    def configure_camera(self) -> None:
        """Function to configure the camera"""
        pykinect.initialize_libraries()
        try:
            if self.device is None:
                self.device = pykinect.start_device(config=self.device_config)
            else:
                self.device.start(self.device_config)
        except SystemExit as exception:
            print(exception)
            print("device not connected or is not able to show live view")
            return None
    
    def configure_camera_rec(self) -> None:
        """Function to configure the camera"""
        pykinect.initialize_libraries()
        try:
            if self.device is None:
                self.device = pykinect.start_device(config=self.device_config, record=True, record_filepath=self.FILEPATH)
            else:
                self.device.start(self.device_config, True, record_filepath=self.FILEPATH)
        except SystemExit as exception:
            print(exception)
            print("device not connected or is not able to record")
            return None
        
    # def start_kinect(self) -> None:
    #     """Function to configure the device"""
    #     self.configure_camera()

    # def start_kinect_record(self) -> None:
    #     """Function to configure the device"""
    #     self.configure_camera_rec()
    
    def stop_kinect(self) -> None:
        """Function to stop the kinect"""
        if self.device is not None:
            self.device.stop_cameras()
            self.device.stop_imu()
            self.device.record = None
            self.device.recording = False

    

    def get_medium_res_confguration(self) -> Configuration:
        config: Configuration = pykinect.default_configuration
        config.camera_fps = pykinect.K4A_FRAMES_PER_SECOND_30
        config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_720P
        config.color_format = pykinect.K4A_IMAGE_FORMAT_COLOR_NV12
        return config

    def get_low_res_configuration(self) -> Configuration:
        config: Configuration = pykinect.default_configuration
        config.camera_fps = pykinect.K4A_FRAMES_PER_SECOND_30
        config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_720P
        config.color_format = pykinect.K4A_IMAGE_FORMAT_COLOR_MJPG
        return config
    
    def get_medium_res_confguration_rec(self) -> Configuration:
        config: Configuration = pykinect.default_configuration
        config.camera_fps = pykinect.K4A_FRAMES_PER_SECOND_30
        config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_720P
        config.color_format = pykinect.K4A_IMAGE_FORMAT_COLOR_NV12
        return config

    def get_low_res_configuration_rec(self) -> Configuration:
        config: Configuration = pykinect.default_configuration
        config.camera_fps = pykinect.K4A_FRAMES_PER_SECOND_30
        config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_720P
        config.color_format = pykinect.K4A_IMAGE_FORMAT_COLOR_MJPG
        return config