"""Module with kinect hub class and methods"""
#pylint: disable=no-member
import pykinect_azure as pykinect
# import numpy as np
import cv2
from pykinect_azure.k4a import Device, Capture, Image
from PIL import ImageTk, Image as PILImage
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
            self._is_initialized = True
            self.root = root
            self.top_level = tk.Toplevel(root)
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

    def live_view(self):
        """Function to open the live view in the kinect camera in a seperate thread"""
        device: Device = self.configure_camera()
        if device is None:
            return
        # Start the live view in a seperate thread
        threading.Thread(target=self.live_view_thread, args=(device,)).start()

    def live_view_thread(self, device: Device):
        '''Function to start the live view'''
        cv2.namedWindow("Live View", cv2.WINDOW_NORMAL)
        while True:
            # Get a capture from the device
            capture: Capture = device.update()
            ret: bool
            raw_color_image: Image
            # Get the color image from the capture
            ret, raw_color_image = capture.get_color_image()

            # if the capture did not succeed, then continue
            if not ret:
                continue
            
            image = cv2.putText(raw_color_image, "Live View", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.imshow("Live View", image)

            # Press q to exit
            if cv2.waitKey(1) == ord('q'):
                break

    


    def configure_camera(self) -> Device:
        """Function to configure the camera"""
        pykinect.initialize_libraries()
        # Modify camera configuration
        device_config = pykinect.default_configuration
        device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
        # device_config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_2X2BINNED
        try:
            device: Device = pykinect.start_device(config=device_config)
            return device
        except SystemExit as exception:
            print(exception)
            return None
            

