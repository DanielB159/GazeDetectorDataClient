"""Module with glasses hub class and methods"""
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel
from qasync import QEventLoop
from imports import asyncio
from imports import g3pylib
from imports import os
from imports import cv2

import threading
import logging
logging.basicConfig(level=logging.INFO)

def run_async_thread(func):
    rtsp_thread : threading.Thread = threading.Thread(target=lambda x: thread_function(x), args=(func,))
    rtsp_thread.start()

def thread_function(func):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(func())
    loop.close()

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
            self.define_ui()
            self.previous_recording = None
            self.g3 = None
            self.glasses_widget.show()
            asyncio.ensure_future(self.connect())  # attempt to auto-connect to glasses

    def closeEvent(self, event):
        """Function to handle the close event"""
        logging.info("Glasseshub window closed.")
        self._instance = None
        self._is_initialized = False
        self.__del__()

    def __del__(self):
        logging.info("Glasseshub instance destroyed.")
        # in case a recording is in progress, close it
        asyncio.ensure_future(self.stop_recording())
        asyncio.ensure_future(self.disconnect())

    async def connect(self):
        """Function to connect machine to glasses"""
        self.g3 = await g3pylib.connect_to_glasses.with_hostname(os.environ["G3_HOSTNAME"])
        self.connection_label.setText(f"Status: Connected to {self.g3.rtsp_url}")
    
    async def disconnect(self):
        await self.g3.close()
        self.connection_label.setText("Status: Not Connected")
    
    async def calibrate(self):
        out = await self.g3.calibrate.run()
        if (out):
            print("Calibration successful.")
        else:
            print("Calibration failed.")

    async def start_recording(self):
        if await self.g3.recorder.get_uuid() != None:
            logging.info("Warning: Recording ongoing, can't start new recording. Make sure to stop recording.")
            return
        async with self.g3.recordings.keep_updated_in_context():
            await self.g3.recorder.start()
            logging.info("Creating new recording")
            # now is the time to set folder and names (not uuid)
            # self.recording_uuid = await self.g3.recorder.get_uuid()
            # self.g3.recorder.set_visible_name(str)

    async def stop_recording(self):
        if await self.g3.recorder.get_uuid() == None:
            logging.info("Warning: Recording not ongoing, nothing to stop.")
            return
        async with self.g3.recordings.keep_updated_in_context():
            recording_uuid = await self.g3.recorder.get_uuid()
            await self.g3.recorder.stop()    # what if failed?
            logging.info("Recording stopped")
            # get recording now
            self.previous_recording = self.g3.recordings.get_recording(recording_uuid)  # must it be updated?
            logging.info(await self.previous_recording.get_http_path())
            # at this point i might want to try and downlod it from the glasses. or perhaps just name it to use later

    async def cancel_recording(self):
        if await self.g3.recorder.get_uuid() == None:
            logging.info("Warning: Recording not ongoing, nothing to cancel.")
            return
        async with self.g3.recordings.keep_updated_in_context():
            await self.g3.recorder.cancel()    # what if failed?
            logging.info("Recording cancelled")

    async def lv_start(self):
        try:
            async with self.g3.stream_rtsp(scene_camera=True, gaze=True) as streams:
                async with streams.gaze.decode() as gaze_stream, streams.scene_camera.decode() as scene_stream:
                    cv2.namedWindow("Live_View", cv2.WINDOW_NORMAL)
                    prev_key = -1
                    i = 0 # frames
                    while prev_key != ord('q'):
                        i += 1 # frames
                        frame, frame_timestamp = await scene_stream.get()
                        gaze, gaze_timestamp = await gaze_stream.get()
                        while gaze_timestamp is None or frame_timestamp is None:
                            if frame_timestamp is None:
                                frame, frame_timestamp = await scene_stream.get()
                            if gaze_timestamp is None:
                                gaze, gaze_timestamp = await gaze_stream.get()
                        while gaze_timestamp < frame_timestamp:
                            gaze, gaze_timestamp = await gaze_stream.get()
                            while gaze_timestamp is None:
                                gaze, gaze_timestamp = await gaze_stream.get()

                        #logging.info(f"Frame timestamp: {frame_timestamp}")
                        #logging.info(f"Gaze timestamp: {gaze_timestamp}")
                        frame = frame.to_ndarray(format="bgr24")

                        # If given gaze data
                        if "gaze2d" in gaze:
                            gaze2d = gaze["gaze2d"]
                            #logging.info(f"Gaze2d: {gaze2d[0]:9.4f},{gaze2d[1]:9.4f}")

                            # Convert rational (x,y) to pixel location (x,y)
                            h, w = frame.shape[:2]
                            fix = (int(gaze2d[0] * w), int(gaze2d[1] * h))

                            # Draw gaze
                            frame = cv2.circle(frame, fix, 10, (0, 0, 255), 3)

                        elif i % 50 == 0:
                            logging.info(
                                "No gaze data received. Have you tried putting on the glasses?"
                            )

                        cv2.imshow("Live_View", frame)  # type: ignore
                        prev_key = cv2.waitKey(1)  # type: ignore
                    
                    cv2.destroyWindow("Live_View")
        except Exception as e:
            logging.error(str(e))
        

    def define_ui(self):
        """Function defining the UI of the Glasses Hub"""
        self.glasses_widget.setWindowTitle("Glasses Hub")
        self.glasses_widget.setGeometry(500, 500, 500, 500)
        self.glasses_widget.closeEvent = self.closeEvent

        self.connection_label : QLabel = QLabel(self.glasses_widget)
        self.connection_label.resize(1000, 20)
        self.connection_label.setText("Status: Not Connected")

        # connection buttons
        self.connect_button : QPushButton = QPushButton(self.glasses_widget)
        self.connect_button.setText("Connect")
        self.connect_button.move(50, 50)
        self.connect_button.clicked.connect(lambda: asyncio.ensure_future(self.connect()))
        
        self.disconnect_button : QPushButton = QPushButton(self.glasses_widget)
        self.disconnect_button.setText("Disconnect")
        self.disconnect_button.move(150, 50)
        self.disconnect_button.clicked.connect(lambda: asyncio.ensure_future(self.disconnect()))

        # calibration and live_view
        self.calibrate_button : QPushButton = QPushButton(self.glasses_widget)
        self.calibrate_button.setText("Calibrate")
        self.calibrate_button.move(150, 100)
        self.calibrate_button.clicked.connect(lambda: asyncio.ensure_future(self.calibrate()))

        self.lv_start_button : QPushButton = QPushButton(self.glasses_widget)
        self.lv_start_button.setText("Start Live View")
        self.lv_start_button.move(50, 100)
        self.lv_start_button.clicked.connect(lambda: run_async_thread(self.lv_start))

        # recording buttons
        self.record_start_button : QPushButton = QPushButton(self.glasses_widget)
        self.record_start_button.setText("Start Recording")
        self.record_start_button.move(50, 150)
        self.record_start_button.clicked.connect(lambda: asyncio.ensure_future(self.start_recording()))
        
        self.record_stop_button : QPushButton = QPushButton(self.glasses_widget)
        self.record_stop_button.setText("Stop Recording")
        self.record_stop_button.move(150, 150)
        self.record_stop_button.clicked.connect(lambda: asyncio.ensure_future(self.stop_recording()))

        self.record_cancel_button : QPushButton = QPushButton(self.glasses_widget)
        self.record_cancel_button.setText("Cancel Recording")
        self.record_cancel_button.move(100, 200)
        self.record_cancel_button.clicked.connect(lambda: asyncio.ensure_future(self.cancel_recording()))
# TODO: add safety! to if we didnt stop recording, ways to monitor sd space and battery