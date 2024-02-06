"""Module with glasses hub class and methods"""
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel
from qasync import QEventLoop
from imports import asyncio
from imports import g3pylib
from g3pylib import Glasses3
from imports import os
from imports import cv2
from g3pylib.recordings.recording import Recording
from recordings_hub import RecordingsHub
from recordings_hub import download_recording_thread

import threading
import logging
#from asgiref.sync import async_to_sync
from datetime import datetime

logging.basicConfig(level=logging.INFO)


def run_async_thread(func):
    rtsp_thread: threading.Thread = threading.Thread(
        target=lambda x: thread_function(x), args=(func,)
    )
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
            self.glasses_widget: QWidget = glasses_hub_widget
            self._is_initialized: bool = True
            self.battery_level: float = 0
            self.storage_free: int = 0
            self.storage_size: int = 1
            self.recording_folder_name : str = None
            self.define_ui()
            self.previous_recording = None  # TODO: ADD TYPING
            self.g3: Glasses3 = None
            #self.isConnected: bool = False // just check if self.g3 == None
            self.glasses_widget.show()
            asyncio.ensure_future(self.connect())  # attempt to auto-connect to glasses

#    @async_to_sync
    async def is_recording(self):
        return await self.g3.recorder.get_uuid() == None

    def is_able_to_record(self):
        if self.g3 == None: # check if is even connected
            return False
        try:
            # check if glasses are currently recording
            print("checking")
            is_recording = False    # TODO: make it actually check
            #is_recording = self.is_recording()
            #print(is_recording)
        except:
            return False
        return not is_recording

    def closeEvent(self, event):
        """Function to handle the close event"""
        logging.info("Glasseshub window closed.")
        self._instance = None
        self._is_initialized = False
        self.__del__()

    def __del__(self):
        logging.info("Glasseshub instance destroyed.")
        # in case a recording is in progress, close it
        run_async_thread(self._stop_recording)
        run_async_thread(self.disconnect)
        # how do i force this to remain open?

    async def connect(self):
        """Function to connect machine to glasses"""
        if not self.g3 == None:
            logging.info("Already Connected, reconnecting...")
        try:
            self.g3 = await g3pylib.connect_to_glasses.with_hostname(
                os.environ["G3_HOSTNAME"]
            )
        except:
            logging.info("Connection failed.")
            return
        self.connection_label.setText(f"Status: Connected to {self.g3.rtsp_url}")

    async def disconnect(self):
        if not self.g3 == None:
            logging.info("Not connected.")
        try:
            await self.g3.close()
            self.g3 = None
        except:
            logging.info("Closing connection failed.")
        self.connection_label.setText("Status: Not Connected")

    async def calibrate(self):
        if self.g3 == None:
            logging("Not connected.")
            return
        try:
            out = await self.g3.calibrate.run()
        except:
            logging.info("Unable to reach Glasses3.")
        if out:
            print("Calibration successful.")
        else:
            print("Calibration failed.")

    async def _start_recording(self):
        if self.g3 == None:
            logging("Glasses_Hub: Not Connected.")
            return
        try:
            if await self.g3.recorder.get_uuid() != None:
                logging.info(
                    "Warning: Recording ongoing, can't start new recording. Make sure to stop recording."
                )
                return
            async with self.g3.recordings.keep_updated_in_context():
                await self.g3.recorder.start()
                logging.info("Creating new recording")
        except:
            logging.info("Glasses_Hub: _start_recording() Error: Unable to reach Glasses3")
    
    def start_recording(self, recording_folder_name : str):
        # TODO: what if overrides??? make sure it doesnt if self.recording_folder_name is already set, and make it None otherwise?   
        self.recording_folder_name = recording_folder_name
        asyncio.ensure_future(self._start_recording())

    async def _stop_recording(self):
        if self.g3 == None:
            logging.info("Not connected.")
            return
        try:
            if await self.g3.recorder.get_uuid() == None:
                logging.info("Warning: Recording not ongoing, nothing to stop.")
                return
            async with self.g3.recordings.keep_updated_in_context():
                recording_uuid = await self.g3.recorder.get_uuid()
                await self.g3.recorder.stop()  # what if failed?
                logging.info("Recording stopped")
                # get recording now
                self.previous_recording = self.g3.recordings.get_recording(
                    recording_uuid
                )  # must it be updated?
                logging.info(await self.previous_recording.get_http_path())

                #assuming dir doesnt exist!
                os.makedirs("./recordings/" + self.recording_folder_name + "/Glasses3")
                download_recording_thread(self.previous_recording.uuid, self.g3._http_url, "./recordings/" + self.recording_folder_name + "/Glasses3")

                # at this point i might want to try and downlod it from the glasses. or perhaps just name it to use later
        except:
            logging.info("Glasses_Hub: _stop_recording() Error: Unable to reach Glasses3")

    def stop_recording(self):
        asyncio.ensure_future(self._stop_recording())

    async def _cancel_recording(self):
        if self.g3 == None:
            logging.info("Not connected.")
            return
        try:
            if await self.g3.recorder.get_uuid() == None:
                logging.info("Warning: Recording not ongoing, nothing to cancel.")
                return
            async with self.g3.recordings.keep_updated_in_context():
                await self.g3.recorder.cancel()  # what if failed?
                logging.info("Recording cancelled")
        except:
            logging.info("Glasses_Hub: _cancel_recording() Error: Unable to reach Glasses3")

    def cancel_recording(self):
        asyncio.ensure_future(self._cancel_recording())

    async def get_sd_and_battery_info(self):
        if self.g3 == None:
            logging.info("Not Connected.")
            return
        try:
            # define the requests
            req_battery = self.g3._connection.generate_get_request("//system/battery.level")
            req_storage_size = self.g3._connection.generate_get_request(
                "//system/storage.size"
            )
            req_storage_free = self.g3._connection.generate_get_request(
                "//system/storage.free"
            )

            # request the data
            res_battery = await self.g3._connection.require(req_battery)
            if not res_battery:
                logging.error("Error getting battery level")
                return
            self.battery_level = float(res_battery)
            self.battery_label.setText("Battery: {:.2f}%".format(self.battery_level * 100))
            # or
            # self.battery_label.setText(f"Battery: {self.battery_level * 100:.2f}%")
            res_storage_size = await self.g3._connection.require(req_storage_size)
            if not res_storage_size:
                logging.error("Error getting storage size")
                return
            self.storage_size = int(res_storage_size)
            res_storage_free = await self.g3._connection.require(req_storage_free)
            if not res_storage_free:
                logging.error("Error getting storage free")
                return
            self.storage_free = int(res_storage_free)
            self.sd_card_label.setText(
                "SD card free space left: {:.2f}%".format(
                    (self.storage_free / self.storage_size) * 100
                )
            )

            # logging.info(sd_info) 
        except:
            logging.info("Glasses_Hub: get_sd_and_battery_info() Error: Unable to reach Glasses3")

    async def lv_start(self):
        try:
            async with self.g3.stream_rtsp(scene_camera=True, gaze=True) as streams:
                async with streams.gaze.decode() as gaze_stream, streams.scene_camera.decode() as scene_stream:
                    cv2.namedWindow("Live_View", cv2.WINDOW_NORMAL)
                    prev_key = -1
                    i = 0  # frames
                    while prev_key != ord("q"):
                        i += 1  # frames
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

                        # logging.info(f"Frame timestamp: {frame_timestamp}")
                        # logging.info(f"Gaze timestamp: {gaze_timestamp}")
                        frame = frame.to_ndarray(format="bgr24")

                        # If given gaze data
                        if "gaze2d" in gaze:
                            gaze2d = gaze["gaze2d"]
                            # logging.info(f"Gaze2d: {gaze2d[0]:9.4f},{gaze2d[1]:9.4f}")

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

    async def storage_recordings(self):
        """Function to show all recordings on the glasses"""
        if self.g3 == None:
            logging.error("Not connected to glasses")
            return
        recordings = await self.g3.recordings._get_children()
        recordings_widget = QWidget()
        recordings_hub: RecordingsHub = RecordingsHub(recordings_widget, recordings, self.g3)
        

    def define_ui(self):
        """Function defining the UI of the Glasses Hub"""
        self.glasses_widget.setWindowTitle("Glasses Hub")
        self.glasses_widget.setGeometry(500, 500, 500, 500)
        self.glasses_widget.closeEvent = self.closeEvent

        self.connection_label: QLabel = QLabel(self.glasses_widget)
        self.connection_label.resize(1000, 20)
        self.connection_label.setText("Status: Not Connected")

        # connection buttons
        self.connect_button: QPushButton = QPushButton(self.glasses_widget)
        self.connect_button.setText("Connect")
        self.connect_button.move(50, 50)
        self.connect_button.clicked.connect(
            lambda: asyncio.ensure_future(self.connect())
        )

        self.disconnect_button: QPushButton = QPushButton(self.glasses_widget)
        self.disconnect_button.setText("Disconnect")
        self.disconnect_button.move(150, 50)
        self.disconnect_button.clicked.connect(
            lambda: asyncio.ensure_future(self.disconnect())
        )

        # calibration and live_view
        self.calibrate_button: QPushButton = QPushButton(self.glasses_widget)
        self.calibrate_button.setText("Calibrate")
        self.calibrate_button.move(150, 100)
        self.calibrate_button.clicked.connect(
            lambda: asyncio.ensure_future(self.calibrate())
        )

        self.lv_start_button: QPushButton = QPushButton(self.glasses_widget)
        self.lv_start_button.setText("Start Live View")
        self.lv_start_button.move(50, 100)
        self.lv_start_button.clicked.connect(lambda: run_async_thread(self.lv_start))

        # recording buttons
        self.record_start_button: QPushButton = QPushButton(self.glasses_widget)
        self.record_start_button.setText("Start Recording")
        self.record_start_button.move(50, 150)
        self.record_start_button.clicked.connect(
            lambda: self.start_recording("solo_recording: " + '_'.join(str(datetime.now()).split(':')))
        )

        self.record_stop_button: QPushButton = QPushButton(self.glasses_widget)
        self.record_stop_button.setText("Stop Recording")
        self.record_stop_button.move(150, 150)
        self.record_stop_button.clicked.connect(
            lambda: self.stop_recording()
        )

        self.record_cancel_button: QPushButton = QPushButton(self.glasses_widget)
        self.record_cancel_button.setText("Cancel Recording")
        self.record_cancel_button.move(100, 200)
        self.record_cancel_button.clicked.connect(
            lambda: self.cancel_recording()
        )

        # get SD card info an Battery info
        self.sd_info_button: QPushButton = QPushButton(self.glasses_widget)
        self.sd_info_button.setText("SD Info")
        self.sd_info_button.move(50, 250)
        self.sd_info_button.clicked.connect(
            lambda: asyncio.ensure_future(self.get_sd_and_battery_info())
        )

        # define label to show the baattery info
        self.battery_label: QLabel = QLabel(self.glasses_widget)
        self.battery_label.resize(1000, 20)
        self.battery_label.move(50, 300)
        self.battery_label.setText("Battery: " + str(self.battery_level) + "%")

        # define label to show the sd card info
        self.sd_card_label: QLabel = QLabel(self.glasses_widget)
        self.sd_card_label.resize(1000, 20)
        self.sd_card_label.move(50, 350)
        self.sd_card_label.setText(
            "SD card free space left: "
            + str(self.storage_free / self.storage_size)
            + "%"
        )

        # define button to show all recordings
        self.show_recordings_button: QPushButton = QPushButton(self.glasses_widget)
        self.show_recordings_button.setText("Storage recordings")
        self.show_recordings_button.move(50, 400)
        self.show_recordings_button.clicked.connect(
            lambda: asyncio.ensure_future(self.storage_recordings())
        )


# TODO: add safety! to if we didnt stop recording, ways to monitor sd space and battery
