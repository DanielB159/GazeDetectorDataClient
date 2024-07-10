"""Module with kinect hub class and methods"""

# pylint: disable=no-member
import pykinect_azure as pykinect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
# import numpy as np
import cv2
import threading
import time
import os
from datetime import datetime
import concurrent.futures
import numpy as np
from pykinect_azure.k4a import Device, Capture, Image, Configuration
from pykinect_azure.k4a._k4a import (
    k4a_image_get_device_timestamp_usec,
)
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy
from qasync import QEventLoop

from imports import rec_manager

class KinectHub:
    """Class representing the Kinect Hub"""

    _instance = None
    _is_initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KinectHub, cls).__new__(cls)
        return cls._instance

    def __init__(self, kinect_hub_widget: QWidget, record_manager : rec_manager, close_function):
        if not self._is_initialized:
            self.record_manager : rec_manager = record_manager
            if not record_manager:
                raise Exception("no recording manager provided")
            self.close_function = close_function
            self.is_recording: bool = False
            self.is_live_view: bool = False
            self._is_initialized: bool = True
            self.device: Device = None
            self.DEVICE_INDEX: int = 0
            self.RECORD: bool = False
            self.start_timestamp: datetime = None
            self.device_handle: int = None
            self.current_image: Image = None
            self.kinect_hub_widget: QWidget = kinect_hub_widget
            # define the device configuration
            self.device_config: Configuration = self.get_low_res_configuration()
            # define the device UI
            self.define_ui()
            self.kinect_hub_widget.show()

    
    def __del__(self):
        self._instance = None
        self._is_initialized = False
        print("Kinect hub instance destroyed.")

    def start_recording(self, recording_folder_name) -> None:
        """Function to start recording the kinect camera"""
        if self.is_live_view:
            print("not able to start recording when in live view")
            return
        self.FILEPATH = self.configure_recordings_file(recording_folder_name)
        self.configure_camera()
        if self.device is None:
            return
        self.is_recording = True
        self.record_manager.kinect_is_recording = True
        start_recording_thread : threading.Thread = threading.Thread(target=self.start_recording_thread)
        start_recording_thread.start()

    def stop_recording(self) -> None:
        self.is_recording = False
        self.record_manager.kinect_is_recording = False

    def configure_recordings_file(self, file_name: str) -> str:
        # if the path /recordings does not exist, create it
        i: int = 0
        if not os.path.exists("recordings"):
            os.makedirs("recordings")
        os.makedirs("recordings/" + file_name + "/Kinect")
        return "recordings/" + file_name + "/Kinect/"

    def save_image(self, image: np.ndarray, timestamp: str) -> None:
        filename = f"{self.FILEPATH}{timestamp}/{timestamp}.png"
        cv2.imwrite(filename, image)

    def save_depth_image(
        self, depth_image: np.ndarray, timestamp: str, single_channel: bool
    ) -> None:
        if single_channel:
            filename = f"{self.FILEPATH}{timestamp}/{timestamp}_depth_greyscale.png"
        else:
            filename = f"{self.FILEPATH}{timestamp}/{timestamp}_depth.png"
        cv2.imwrite(filename, depth_image)

    def save_depth_csv(self, depth_image: np.ndarray, timestamp: str) -> None:
        filename = f"{self.FILEPATH}{timestamp}/{timestamp}_depth.csv"
        np.savetxt(filename, depth_image, delimiter=",",fmt='%d')

    def start_recording_thread(self) -> None:
        """Function to start recording the kinect camera"""
        cv2.namedWindow("Recording", cv2.WINDOW_NORMAL)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            while True:
                capture: Capture = self.device.update()
                # imu: ImuSample = ImuSample(self.device.get_imu_sample())
                ret: bool
                raw_color_image: Image
                # Get the color image from the capture
                img_obj = capture.get_color_image_object()
                ret, raw_color_image = img_obj.to_numpy()
                # if the capture did not succeed, then continue
                if not ret:
                    continue
                # time_imu = imu.get_gyro_time()
                # get the timestamp from the image
                time_offset_image = k4a_image_get_device_timestamp_usec(img_obj.handle())
                # save the image to a file
                executor.submit(self.write_all_imagees, raw_color_image, None, None, str(time_offset_image))
                

                # if the capture did not succeed, then continue
                if not ret:
                    continue
                image: np.ndarray = cv2.putText(
                    raw_color_image,
                    "Recording",
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 0, 0),
                    2,
                    cv2.LINE_AA,
                )
                cv2.imshow("Recording", image)

                # Press q to exit
                if cv2.waitKey(1) == ord("q") or not self.is_recording:
                    break
            # save a text file that has only the timestamp of the start of the recording
            with open(self.FILEPATH + "start_timestamp.txt", "w") as file:
                file.write(str(self.start_timestamp))
            cv2.destroyWindow("Recording")
            self.stop_kinect()
            self.is_recording = False
            self.record_manager.kinect_is_recording = False

    def start_recording_depth(self, recording_folder_name) -> None:
        """Function to start recording the kinect camera with depth"""
        if self.is_live_view:
            print("not able to start recording when in live view")
            return
        self.FILEPATH = self.configure_recordings_file(recording_folder_name)
        self.configure_camera()
        if self.device is None:
            return
        self.is_recording = True
        self.record_manager.kinect_is_recording = True
        start_recording_thread: threading.Thread = threading.Thread(
            target=self.start_recording_depth_thread
        )
        start_recording_thread.start()

    def write_all_imagees(self, colored_image, depth_image, greyscale_image, timestamp) -> None:
        """Function to write all the images to the file"""
        os.mkdir(self.FILEPATH + timestamp)
        if colored_image is not None: self.save_image(colored_image, timestamp) 
        if depth_image is not None: self.save_depth_image(depth_image, timestamp, False) 
        if greyscale_image is not None: self.save_depth_image(greyscale_image, timestamp, True) 
        if colored_image is not None and greyscale_image is not None: self.save_depth_csv(greyscale_image, timestamp)

        


    def start_recording_depth_thread(self) -> None:
        """Function to start recording the kinect camera with depth"""
        cv2.namedWindow("Recording Depth", cv2.WINDOW_NORMAL)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            while True:
                capture: Capture = self.device.update()
                # Get the color image from the capture
                img_obj = capture.get_color_image_object()
                ret, raw_color_image = img_obj.to_numpy()
                # Get the colored depth and the grey scale detpth images
                ret_depth, transformed_depth_image = (
                    capture.get_transformed_colored_depth_image()
                )
                ret_depth_greyscale, transformed_depth_image_greyscale = (
                    capture.get_transformed_depth_image()
                )
                # if the capture did not succeed, then continue
                if not ret or not ret_depth or not ret_depth_greyscale:
                    continue
                # get the timestamp from the image
                time_offset_image = k4a_image_get_device_timestamp_usec(img_obj.handle())
                # start a thread to save all of the images to a file
                # self.write_all_images(raw_color_image, transformed_depth_image, transformed_depth_image_greyscale, str(time_offset_image))
                executor.submit(self.write_all_imagees, raw_color_image, transformed_depth_image, transformed_depth_image_greyscale, str(time_offset_image))
                # self.write_all_imagees(raw_color_image, transformed_depth_image, transformed_depth_image_greyscale, time_offset_image)

                combined_image = cv2.addWeighted(
                    raw_color_image[:, :, :3], 0.5, transformed_depth_image, 0.5, 0
                )
                cv2.imshow("Recording Depth", combined_image)

                # Press q to exit
                if cv2.waitKey(1) == ord("q") or not self.is_recording:
                    break
            # save a text file that has only the timestamp of the start of the recording
            with open(self.FILEPATH + "start_timestamp.txt", "w") as file:
                file.write(str(self.start_timestamp))
            # executor.shutdown(wait=True)
            # self.convert_greyscale_to_csv()
            cv2.destroyWindow("Recording Depth")
            self.stop_kinect()
            self.is_recording = False
            self.record_manager.kinect_is_recording = False
            
    def convert_greyscale_to_csv(self) -> None:
        """Function to convert all of the images taken in greyscale to csv files"""
        for folder in os.listdir(self.FILEPATH):
            if not os.path.isfile(f"{self.FILEPATH}{folder}"):
                for file in os.listdir(self.FILEPATH + folder):
                    if file.endswith("_depth_greyscale.png"):
                        greyscale_image = cv2.imread(f"{self.FILEPATH}{folder}/{file}", cv2.IMREAD_GRAYSCALE)
                        index = file.find("_depth_greyscale.png")
                        self.save_depth_csv(greyscale_image, file[:index])


    def live_view_depth(self) -> None:
        """Function to open the live view in depth mode in the kinect camera in a seperate thread"""
        if self.is_recording:
            print("not able to start live view when recording")
            return
        self.configure_camera(True)
        if self.device is None:
            return
        # Start the live view in a seperate thread
        self.is_live_view = True
        live_view_thread: threading.Thread = threading.Thread(
            target=self.live_view_depth_thread, args=(self.device,)
        )
        live_view_thread.start()
        # Stop the kinect
        # self.stop_kinect()

    def live_view_depth_thread(self, device: Device) -> None:
        """Function to start the live view"""
        cv2.namedWindow("Live View Depth", cv2.WINDOW_NORMAL)
        # sys.stdout = open("output.txt", "w")
        # Initialize the Open3d visualizer

        while True:
            # Get a capture from the device
            capture: Capture = device.update()
            ret: bool
            depth_image: Image
            color_image: Image
            # Get the color image from the capture
            # ret, depth_image = capture.get_ir_image()

            # Get the color depth image from the capture
            ret_depth, transformed_depth_image = (
                capture.get_transformed_colored_depth_image()
            )

            # Get the colorred image
            ret_color, color_image = capture.get_color_image()
            if not ret_depth or not ret_color:
                continue

            combined_image = cv2.addWeighted(
                color_image[:, :, :3], 0.5, transformed_depth_image, 0.5, 0
            )

            cv2.imshow("Live View Depth", combined_image)
            # Press q to exit
            if cv2.waitKey(1) == ord("q"):
                cv2.destroyWindow("Live View Depth")                
                break
        self.stop_kinect()
        self.is_live_view = False



    def live_view(self) -> None:
        """Function to open the live view in the kinect camera in a seperate thread"""
        if self.is_recording:
            print("not able to start live view when recording")
            return
        self.configure_camera(True)
        if self.device is None:
            return
        # Start the live view in a seperate thread
        self.is_live_view = True
        live_view_thread: threading.Thread = threading.Thread(
            target=self.live_view_thread, args=(self.device,)
        )
        live_view_thread.start()
        # Stop the kinect
        # self.stop_kinect()

    def live_view_thread(self, device: Device) -> None:
        """Function to start the live view"""
        cv2.namedWindow("Live View", cv2.WINDOW_NORMAL)
        # sys.stdout = open("output.txt", "w")
        while True:
            # Get a capture from the device
            capture: Capture = device.update()
            ret: bool
            raw_color_image: Image
            img_obj = capture.get_color_image_object()
            ret, raw_color_image = img_obj.to_numpy()
            # if the capture did not succeed, then continue
            if not ret:
                continue
            image: np.ndarray = cv2.putText(
                raw_color_image,
                "Live View",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow("Live View", image)

            # Press q to exit
            if cv2.waitKey(1) == ord("q"):
                cv2.destroyWindow("Live View")
                break
        self.stop_kinect()
        self.is_live_view = False

    def configure_camera(self, is_live_view=False) -> None:
        """Function to configure the camera"""
        pykinect.initialize_libraries()
        try:
            if self.device is None:
                # Create device object
                self.device = Device(self.DEVICE_INDEX)

                # Start device
                if is_live_view:
                    self.device.start(self.device_config)
                else:
                    self.device.start(self.device_config, self.RECORD, self.FILEPATH)
            else:
                self.device.start(self.device_config)
            self.start_timestamp = datetime.now()
        except SystemExit as exception:
            print(exception)
            print("device not connected or is not able to show live view")
            return None

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
        config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_2X2BINNED
        return config

    def get_low_res_configuration(self) -> Configuration:
        config: Configuration = pykinect.default_configuration
        config.camera_fps = pykinect.K4A_FRAMES_PER_SECOND_30
        # config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_OFF
        config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_720P
        config.color_format = pykinect.K4A_IMAGE_FORMAT_COLOR_MJPG
        config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_2X2BINNED
        return config

    def define_ui(self) -> None:
        """Function defining the UI of the Kinect Hub"""
        A_X = 50
        A_Y = 50
        A_W = 250
        A_H = 250
        self.kinect_hub_widget.setWindowTitle("Kinect Hub")
        self.kinect_hub_widget.setGeometry(A_X, A_Y, A_W, A_H)
        self.kinect_hub_widget.closeEvent = self.close_function

        # Set background color
        self.kinect_hub_widget.setAutoFillBackground(True)
        palette = self.kinect_hub_widget.palette()
        palette.setColor(QPalette.Window, QColor(220, 220, 220))
        self.kinect_hub_widget.setPalette(palette)

        kinect_hub_title = QLabel("Kinect Hub", self.kinect_hub_widget)
        kinect_hub_title.setAlignment(Qt.AlignCenter)

        live_view_btn = QPushButton("Live View", self.kinect_hub_widget)
        live_view_btn.setStyleSheet("background-color: lightblue;")
        live_view_btn.clicked.connect(self.live_view)
        
        live_view_depth_btn = QPushButton("Live View Depth", self.kinect_hub_widget)
        live_view_depth_btn.setStyleSheet("background-color: lightgreen;")
        live_view_depth_btn.clicked.connect(self.live_view_depth)
        
        start_rec_btn = QPushButton("Start recording", self.kinect_hub_widget)
        start_rec_btn.setStyleSheet("background-color: lightcoral;")
        start_rec_btn.clicked.connect(lambda: self.start_recording("recording_" + str(time.time())))
        
        start_rec_depth_btn = QPushButton("Start recording depth", self.kinect_hub_widget)
        start_rec_depth_btn.setStyleSheet("background-color: lightgoldenrodyellow;")
        start_rec_depth_btn.clicked.connect(lambda: self.start_recording_depth("recording_" + str(time.time())))

        vbox = QVBoxLayout()
        vbox.addWidget(kinect_hub_title)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(live_view_btn)
        hbox1.addWidget(live_view_depth_btn)
        vbox.addLayout(hbox1)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(start_rec_btn)
        hbox2.addWidget(start_rec_depth_btn)
        vbox.addLayout(hbox2)

        self.kinect_hub_widget.setLayout(vbox)

        # Make the widgets stretch properly when resizing
        live_view_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        live_view_depth_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        start_rec_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        start_rec_depth_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        kinect_hub_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)