"""Module with glasses hub class and methods"""


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QSizePolicy
from imports import asyncio
from imports import g3pylib
from g3pylib import Glasses3
from imports import os
from imports import cv2
from recordings_hub import RecordingsHub
from recordings_hub import download_recording_thread

import threading
import logging

# from asgiref.sync import async_to_sync
from datetime import datetime

from imports import rec_manager
import re

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
    """Class representing the Glasses Hub."""

    _instance = None
    _is_initialized = False

    def __new__(cls, *args, **kwargs):
        """Function ensuring singleton status of the class."""
        if cls._instance is None:
            cls._instance = super(GlassesHub, cls).__new__(cls)
        return cls._instance

    def __init__(
        self, glasses_hub_widget: QWidget, record_manager: rec_manager, close_function
    ):
        """Constructor for Glasses Hub.

        Args:
            glasses_hub_widget (QWidget): PyQt5 widget for displaying this hub.
            record_manager (rec_manager): Instance managing which Hubs are available for recording.
            close_function (function(event) -> None): Function to be called when the window closes.

        Returns:
            GlassesHub: Instance of this class.
        """
        if not self._is_initialized:
            self.record_manager: rec_manager = record_manager
            if not record_manager:
                raise Exception("no recording manager provided")  # unnecessary check
            self.close_function = close_function
            self.host_ip = None if "G3_HOSTNAME" not in os.environ else os.environ["G3_HOSTNAME"]
            self.glasses_widget: QWidget = glasses_hub_widget
            self._is_initialized: bool = True
            self.battery_level: float = 0
            self.storage_free: int = 0
            self.storage_size: int = 1
            self.recording_folder_name: str = None
            self.glasses_offset = 3
            self.define_ui()
            self.previous_recording = None  # TODO: ADD TYPING
            self.g3: Glasses3 = None
            self.glasses_widget.show()
            asyncio.ensure_future(self.connect())  # attempt to auto-connect to glasses

    async def _update_recording_state(self):
        """Update recording_manager instance of glasses status."""
        # check glasses are connected
        # TODO: what if lost connection?
        if self.g3 == None:
            self.record_manager.glasses_is_connected = False
            self.record_manager.glasses_is_recording = False
            return
        self.record_manager.glasses_is_connected = True
        state = (
            await self.g3.recorder.get_uuid() != None
        )  # check if there is an ongoing recording
        self.record_manager.glasses_is_recording = state

    def update_recording_state(self):
        """Synchronously call _update_recording_state."""
        asyncio.ensure_future(self._update_recording_state())

    def __del__(self):
        """Close connection and recordings in progress on instance destruction."""
        # in case a recording is in progress, close it
        self._instance = None
        self._is_initialized = False
        asyncio.ensure_future(self._stop_recording())
        asyncio.ensure_future(self.disconnect())
        logging.info("Glasseshub instance destroyed.")
        # TODO: how do i force this to remain open? is it already so?

    async def connect(self):
        """Connect this machine to the glasses."""
        if not self.g3 == None:
            logging.info("Already Connected, reconnecting...")
        try:
            hostmame = self.host_ip
            if not hostmame:
                raise ValueError("host ip not defined")
            self.g3 = await g3pylib.connect_to_glasses.with_hostname(hostname=hostmame)
        except Exception as e:
            logging.info(f"Connection failed: {e}")
            return
        self.connection_label.setText(f"Status: Connected to {self.g3.rtsp_url}")
        self.update_recording_state()  # update recording manager status TODO: just await on async?

    async def disconnect(self):
        """Disconnect this machine from the glasses."""
        if not self.g3 == None:
            logging.info("Not connected.")
        try:
            await self._stop_recording()  # end recordings before disconnecting
            await self.g3.close()
            self.g3 = None
        except:
            logging.info("Closing connection failed.")
        self.connection_label.setText("Status: Not Connected")
        self.update_recording_state()  # update recording manager status

    async def calibrate(self):
        """Run glasses calibration sequence."""
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
        """Start a new recording if none are currently ongoing."""
        if self.g3 == None:
            logging("Glasses_Hub: Not Connected.")
            return
        try:
            if await self.g3.recorder.get_uuid() != None:
                logging.info("Warning: Recording ongoing, can't start a new recording.")
                return
            async with self.g3.recordings.keep_updated_in_context():
                await self.g3.recorder.start()
                logging.info("Creating new recording")
        except:
            logging.info(
                "Glasses_Hub: _start_recording() Error: Unable to reach Glasses3"
            )
        self.update_recording_state()  # update recording manager status

    def start_recording(self, recording_folder_name: str):
        """Synchronously call _start_recording.

        Args:
            recording_folder_name (str): Name of folder to save this recording to. (Must be unique!)
        """
        # TODO: what if overrides??? make sure it doesnt if self.recording_folder_name is already set, and make it None otherwise?
        self.recording_folder_name = recording_folder_name
        asyncio.ensure_future(self._start_recording())

    async def _stop_recording(self):
        """Stop current recording in progress, and download the recording onto self.recording_folder_name.
        Folder was set upon calling self.start_recording().
        """
        if self.g3 == None:
            logging.info("Not connected.")
            return
        try:
            if await self.g3.recorder.get_uuid() == None:
                logging.info("Warning: Recording not ongoing, nothing to stop.")
                return
            async with self.g3.recordings.keep_updated_in_context():
                recording_uuid = await self.g3.recorder.get_uuid()
                await self.g3.recorder.stop()  # TODO: what if failed?
                logging.info("Recording stopped")
                # get recording now
                self.previous_recording = self.g3.recordings.get_recording(
                    recording_uuid
                )
                logging.info(await self.previous_recording.get_http_path())

                os.makedirs("./recordings/" + self.recording_folder_name + "/Glasses3")
                download_recording_thread(
                    self.previous_recording.uuid,
                    self.g3._http_url,
                    "./recordings/" + self.recording_folder_name + "/Glasses3",
                    self.glasses_offset
                )

        except Exception as e:
            logging.info(e)
            logging.info(
                "Glasses_Hub: _stop_recording() Error: Unable to reach Glasses3"
            )
        self.update_recording_state()  # update recording manager status

    def stop_recording(self):
        """Synchronously call _stop_recording."""
        asyncio.ensure_future(self._stop_recording())

    async def _cancel_recording(self):
        """Cancel current recording in progress, without saving any of the data."""
        if self.g3 == None:
            logging.info("Not connected.")
            return
        try:
            if await self.g3.recorder.get_uuid() == None:
                logging.info("Warning: Recording not ongoing, nothing to cancel.")
                return
            async with self.g3.recordings.keep_updated_in_context():
                await self.g3.recorder.cancel()  # TODO: what if failed?
                logging.info("Recording cancelled")
        except:
            logging.info(
                "Glasses_Hub: _cancel_recording() Error: Unable to reach Glasses3"
            )
        self.update_recording_state()  # update recording manager status

    def cancel_recording(self):
        """Synchronously call _cancel_recording."""
        asyncio.ensure_future(self._cancel_recording())

    async def get_sd_and_battery_info(self):
        """Request battery and sd status from the glasses and display them to the user."""
        if self.g3 == None:
            logging.info("Not Connected.")
            return
        try:
            # define the requests
            req_battery = self.g3._connection.generate_get_request(
                "//system/battery.level"
            )
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
            self.battery_label.setText(
                "Battery: {:.2f}%".format(self.battery_level * 100)
            )
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
            logging.info(
                "Glasses_Hub: get_sd_and_battery_info() Error: Unable to reach Glasses3"
            )

    async def lv_start(self):
        """Start the glasses live view and display it to the user."""
        # TODO: stop live view before recording? can do both i think
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


    def change_ip(self):
        ip_text = self.ip_input.text()
        ip_pattern = r"\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
        if re.fullmatch(ip_pattern, ip_text):
            self.host_ip = ip_text
            self.ip_label.setText(f"Current IP: {self.host_ip}")
            self.ip_input.setText("")
        else:
            print("the text is not in IPV4 format!")
            self.ip_input.setText("")

    async def storage_recordings(self):
        """Show all recordings on the glasses"""
        if self.g3 == None:
            logging.error("Not connected to glasses")
            return
        recordings = await self.g3.recordings._get_children()
        recordings_widget = QWidget()
        recordings_hub: RecordingsHub = RecordingsHub(
            recordings_widget, recordings, self.g3
        )

    def change_glasses_offset(self):
        glasses_offset_text = self.glasses_offset_input.text()
        try:
            self.glasses_offset = float(glasses_offset_text)
            self.glasses_offset_input.setText("")
            self.offset_label.setText("Current offset: " + str(self.glasses_offset))
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    def define_ui(self):
        """Function defining the UI of the Glasses Hub"""
        self.glasses_widget.setWindowTitle("Glasses Hub")
        self.glasses_widget.setGeometry(500, 500, 500, 600)
        self.glasses_widget.closeEvent = self.close_function

        # Set background color
        self.glasses_widget.setAutoFillBackground(True)
        palette = self.glasses_widget.palette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        self.glasses_widget.setPalette(palette)

        # Create the connection label
        self.connection_label = QLabel("Status: Not Connected", self.glasses_widget)
        self.connection_label.setAlignment(Qt.AlignCenter)
        self.connection_label.setStyleSheet("font-weight: bold; color: blue;")

        # Create buttons
        self.connect_button = QPushButton("Connect", self.glasses_widget)
        self.connect_button.setStyleSheet("background-color: lightblue;")
        self.connect_button.clicked.connect(lambda: asyncio.ensure_future(self.connect()))

        self.disconnect_button = QPushButton("Disconnect", self.glasses_widget)
        self.disconnect_button.setStyleSheet("background-color: lightblue;")
        self.disconnect_button.clicked.connect(lambda: asyncio.ensure_future(self.disconnect()))

        self.lv_start_button = QPushButton("Start Live View", self.glasses_widget)
        self.lv_start_button.setStyleSheet("background-color: lightgreen;")
        self.lv_start_button.clicked.connect(lambda: run_async_thread(self.lv_start))

        self.calibrate_button = QPushButton("Calibrate", self.glasses_widget)
        self.calibrate_button.setStyleSheet("background-color: lightgreen;")
        self.calibrate_button.clicked.connect(lambda: asyncio.ensure_future(self.calibrate()))

        self.record_start_button = QPushButton("Start Recording", self.glasses_widget)
        self.record_start_button.setStyleSheet("background-color: orange; font-weight: bold;")

        self.record_start_button.clicked.connect(lambda: self.start_recording("solo_recording_" + "_".join(str(datetime.now()).split(":"))))

        self.record_stop_button = QPushButton("Stop Recording", self.glasses_widget)
        self.record_stop_button.setStyleSheet("background-color: red; font-weight: bold; color: white;")
        self.record_stop_button.clicked.connect(lambda: self.stop_recording())

        self.record_cancel_button = QPushButton("Cancel Recording", self.glasses_widget)
        self.record_cancel_button.setStyleSheet("background-color: lightcoral;")
        self.record_cancel_button.clicked.connect(lambda: self.cancel_recording())

        self.sd_info_button = QPushButton("SD Info", self.glasses_widget)
        self.sd_info_button.setStyleSheet("background-color: lightgoldenrodyellow;")
        self.sd_info_button.clicked.connect(lambda: asyncio.ensure_future(self.get_sd_and_battery_info()))

        self.show_recordings_button = QPushButton("Storage recordings", self.glasses_widget)
        self.show_recordings_button.setStyleSheet("background-color: lightgoldenrodyellow;")
        self.show_recordings_button.clicked.connect(lambda: asyncio.ensure_future(self.storage_recordings()))

        self.battery_label = QLabel(f"Battery: {self.battery_level}%", self.glasses_widget)
        self.battery_label.setStyleSheet("font-weight: bold; color: green;")

        self.sd_card_label = QLabel(f"SD card free space left: {self.storage_free / self.storage_size * 100:.1f}%", self.glasses_widget)
        self.sd_card_label.setStyleSheet("font-weight: bold; color: green;")

        self.ip_input = QLineEdit(self.glasses_widget)
        self.ip_input.setPlaceholderText("Enter IP address")

        self.change_ip_button = QPushButton("Change IP", self.glasses_widget)
        self.change_ip_button.setStyleSheet("background-color: lightblue;")
        self.change_ip_button.clicked.connect(self.change_ip)

        self.ip_label = QLabel(f"Current IP: {self.host_ip}", self.glasses_widget)
        self.ip_label.setStyleSheet("font-weight: bold; color: blue;")

        self.glasses_offset_input = QLineEdit(self.glasses_widget)
        self.glasses_offset_input.setPlaceholderText("Change glasses offset")

        self.change_offset_button = QPushButton("Change Glasses Offset", self.glasses_widget)
        self.change_offset_button.setStyleSheet("background-color: lightblue;")
        self.change_offset_button.clicked.connect(self.change_glasses_offset)

        self.offset_label = QLabel(f"Current offset: {self.glasses_offset}", self.glasses_widget)
        self.offset_label.setStyleSheet("font-weight: bold; color: blue;")

        # Layouts
        vbox = QVBoxLayout()
        vbox.addWidget(self.connection_label)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.connect_button)
        hbox1.addWidget(self.disconnect_button)
        vbox.addLayout(hbox1)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.lv_start_button)
        hbox2.addWidget(self.calibrate_button)
        vbox.addLayout(hbox2)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.record_start_button)
        hbox3.addWidget(self.record_stop_button)
        vbox.addLayout(hbox3)

        vbox.addWidget(self.record_cancel_button)
        vbox.addWidget(self.sd_info_button)
        vbox.addWidget(self.battery_label)
        vbox.addWidget(self.sd_card_label)
        vbox.addWidget(self.show_recordings_button)

        hbox4 = QHBoxLayout()
        hbox4.addWidget(self.ip_input)
        hbox4.addWidget(self.change_ip_button)
        vbox.addLayout(hbox4)

        hbox5 = QHBoxLayout()
        hbox5.addWidget(self.glasses_offset_input)
        hbox5.addWidget(self.change_offset_button)
        vbox.addLayout(hbox5)

        vbox.addWidget(self.ip_label)
        vbox.addWidget(self.offset_label)

        self.glasses_widget.setLayout(vbox)

        # Make widgets stretch properly when resizing
        self.connection_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.connect_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.disconnect_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lv_start_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.calibrate_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.record_start_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.record_stop_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.record_cancel_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sd_info_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.show_recordings_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ip_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.change_ip_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ip_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.glasses_offset_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.change_offset_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.battery_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sd_card_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.offset_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.glasses_widget.setWindowTitle("Glasses Hub")
        # self.glasses_widget.setGeometry(500, 500, 500, 600)
        # self.glasses_widget.closeEvent = self.close_function

        # self.connection_label: QLabel = QLabel(self.glasses_widget)
        # self.connection_label.resize(1000, 20)
        # self.connection_label.setText("Status: Not Connected")

        # # connection buttons
        # self.connect_button: QPushButton = QPushButton(self.glasses_widget)
        # self.connect_button.setText("Connect")
        # self.connect_button.move(50, 50)
        # self.connect_button.clicked.connect(
        #     lambda: asyncio.ensure_future(self.connect())
        # )

        # self.disconnect_button: QPushButton = QPushButton(self.glasses_widget)
        # self.disconnect_button.setText("Disconnect")
        # self.disconnect_button.move(150, 50)
        # self.disconnect_button.clicked.connect(
        #     lambda: asyncio.ensure_future(self.disconnect())
        # )

        # # calibration and live_view
        # self.calibrate_button: QPushButton = QPushButton(self.glasses_widget)
        # self.calibrate_button.setText("Calibrate")
        # self.calibrate_button.move(150, 100)
        # self.calibrate_button.clicked.connect(
        #     lambda: asyncio.ensure_future(self.calibrate())
        # )

        # self.lv_start_button: QPushButton = QPushButton(self.glasses_widget)
        # self.lv_start_button.setText("Start Live View")
        # self.lv_start_button.move(50, 100)
        # self.lv_start_button.clicked.connect(lambda: run_async_thread(self.lv_start))

        # # recording buttons
        # self.record_start_button: QPushButton = QPushButton(self.glasses_widget)
        # self.record_start_button.setText("Start Recording")
        # self.record_start_button.move(50, 150)
        # self.record_start_button.clicked.connect(
        #     lambda: self.start_recording(
        #         "solo_recording_" + "_".join(str(datetime.now()).split(":"))
        #     )
        # )

        # self.record_stop_button: QPushButton = QPushButton(self.glasses_widget)
        # self.record_stop_button.setText("Stop Recording")
        # self.record_stop_button.move(150, 150)
        # self.record_stop_button.clicked.connect(lambda: self.stop_recording())

        # self.record_cancel_button: QPushButton = QPushButton(self.glasses_widget)
        # self.record_cancel_button.setText("Cancel Recording")
        # self.record_cancel_button.move(100, 200)
        # self.record_cancel_button.clicked.connect(lambda: self.cancel_recording())

        # # get SD card info an Battery info
        # self.sd_info_button: QPushButton = QPushButton(self.glasses_widget)
        # self.sd_info_button.setText("SD Info")
        # self.sd_info_button.move(50, 250)
        # self.sd_info_button.clicked.connect(
        #     lambda: asyncio.ensure_future(self.get_sd_and_battery_info())
        # )

        # # define label to show the baattery info
        # self.battery_label: QLabel = QLabel(self.glasses_widget)
        # self.battery_label.resize(1000, 20)
        # self.battery_label.move(50, 300)
        # self.battery_label.setText("Battery: " + str(self.battery_level) + "%")

        # # define label to show the sd card info
        # self.sd_card_label: QLabel = QLabel(self.glasses_widget)
        # self.sd_card_label.resize(1000, 20)
        # self.sd_card_label.move(50, 350)
        # self.sd_card_label.setText(
        #     "SD card free space left: "
        #     + str(self.storage_free / self.storage_size)
        #     + "%"
        # )

        # # define button to show all recordings
        # self.show_recordings_button: QPushButton = QPushButton(self.glasses_widget)
        # self.show_recordings_button.setText("Storage recordings")
        # self.show_recordings_button.move(50, 400)
        # self.show_recordings_button.clicked.connect(
        #     lambda: asyncio.ensure_future(self.storage_recordings())
        # )

        # # define label to show the current IP address
        # self.ip_label: QLabel = QLabel(self.glasses_widget)
        # self.ip_label.resize(1000, 20)
        # self.ip_label.move(350, 450)
        # ip_to_put = self.host_ip if self.host_ip is not None else "not found"
        # self.ip_label.setText("Current IP: " + ip_to_put)
        
        # self.ip_input = QLineEdit(self.glasses_widget)
        # self.ip_input.move(50, 450)
        # self.ip_input.setPlaceholderText("Enter IP address")
        
        # self.change_ip_button = QPushButton(self.glasses_widget)
        # self.change_ip_button.setText("Change IP")
        # self.change_ip_button.move(200, 448)
        # self.change_ip_button.clicked.connect(self.change_ip)
        
        # # define label to show current glasses offset
        # self.offset_label: QLabel = QLabel(self.glasses_widget)
        # self.offset_label.resize(1000, 20)
        # self.offset_label.move(350, 500)
        # self.offset_label.setText("Current offset: " + str(self.glasses_offset))

        # # define input line for glasses offset
        # self.glasses_offset_input = QLineEdit(self.glasses_widget)
        # self.glasses_offset_input.move(50, 500)
        # self.glasses_offset_input.setPlaceholderText("Change glasses offset")
        
        # # define button to change glasses offset
        # self.change_offset_button = QPushButton(self.glasses_widget)
        # self.change_offset_button.setText("Change Glasses Offset")
        # self.change_offset_button.move(200, 498)
        # self.change_offset_button.clicked.connect(self.change_glasses_offset)
        
