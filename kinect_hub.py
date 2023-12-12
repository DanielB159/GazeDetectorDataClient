"""Module with kinect hub class and methods"""
#pylint: disable=no-member
import pykinect_azure as pykinect
# import numpy as np
import cv2
from pykinect_azure.k4a import Device, Capture, Image
from pykinect_azure.k4a._k4a import k4a_image_get_system_timestamp_nsec, k4a_image_get_device_timestamp_usec, k4a_image_get_timestamp_usec
from imports import tk
import threading


class KinectHub:
    """Class representing the Kinect Hub"""

    _instance = None
    _is_initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KinectHub, cls).__new__(cls)
        return cls._instance

    def __init__(self, root: tk.Tk):
        if not self._is_initialized:
            self._is_initialized : bool = True
            self.device : Device = None
            self.current_image : Image = None
            self.root : tk.Tk = root
            self.top_level : tk.Toplevel = tk.Toplevel(self.root)
            self.top_level.resizable(False, False)
            self.top_level.title("Kinect Hub")
            self.top_level.geometry("500x500")
            self.top_level.protocol("WM_DELETE_WINDOW", self.__del__)
            self.define_ui()

    def define_ui(self):
        """Function defining the UI of the Kinect Hub"""
        title = tk.Label(self.top_level, text="Kinect Hub", fg="red", font=("Helvetica", 16))
        title.grid(row=0, column=10, columnspan=2, sticky="ew")
        live_view_btn = tk.Button(self.top_level, text="Live View", command=self.live_view)
        live_view_btn.grid(row=2, column=2, columnspan=1, sticky="ew")


    def __del__(self):
        self.top_level.destroy()
        self._instance = None
        self._is_initialized = False


    def capture_image(self):
        """Function to capture an image from the kinect camera"""
        self.configure_kinect()
        if self.device is None:
            return
    
    def capture_image_thread(self, device: Device, current_image: Image):
        """Function to capture an image from the kinect camera"""
        # Get a capture from the device
        capture: Capture = device.update()
        ret: bool
        raw_color_image: Image
        # Get the color image from the capture
        ret, raw_color_image = capture.get_color_image()

        # if the capture did not succeed, then continue



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
            print()
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
        # Modify camera configuration
        device_config = pykinect.default_configuration
        device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
        # device_config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_2X2BINNED
        try:
            self.device: Device = pykinect.start_device(config=device_config)
        except SystemExit as exception:
            print(exception)
            return None
        
    def configure_kinect(self):
        """Function to configure the device"""
        if self.device is None:
            self.configure_camera_sdk_device()
            