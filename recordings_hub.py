from PyQt5.QtWidgets import (
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QPushButton,
    QHeaderView
)
from qasync import QEventLoop
from imports import asyncio
from imports import g3pylib
from g3pylib import Glasses3
from imports import os
from imports import cv2
from g3pylib.recordings.recording import Recording
from datetime import datetime, timedelta
import threading
import logging
import requests
import json


def thread_function_async(func, func_arg1):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(func(func_arg1))
    loop.close()


def run_async_thread(func):
    rtsp_thread: threading.Thread = threading.Thread(
        target=lambda x: thread_function(x), args=(func,)
    )
    rtsp_thread.start()


def thread_function(func):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(func())
    loop.close()


def download_recording_thread(rec_name: str, http_url, directory, glasses_offset = 3):
    # send a request to the glasses to download the recording
    r_recording = requests.get(
        http_url + f"/recordings/{rec_name}" + "/scenevideo.mp4", stream=True
    )
    print("Starting download of recording and gaze data. Please wait until it finishes")
    if r_recording.status_code == 200:
        # save the recording to the directory
        path = os.path.join(directory, "scenevideo.mp4")
        with open(path, "wb") as f:
            for chunk in r_recording.iter_content(1024):
                f.write(chunk)
        print("Recording downloaded.")
    else:
        print("Recording not downloaded.")
    r_gaze_data = requests.get(
        http_url + f"/recordings/{rec_name}" + "/gazedata.gz", stream=True
    )
    if r_gaze_data.status_code == 200:
        # save the recording to the directory
        path = os.path.join(directory, "gazedata.gz")
        with open(path, "wb") as f:
            for chunk in r_gaze_data.iter_content(1024):
                f.write(chunk)
        print("Gaze data downloaded.")
    else:
        print("Gaze data not downloaded.")
    r_event_data = requests.get(
        http_url + f"/recordings/{rec_name}" + "/eventdata.gz", stream=True
    )
    if r_event_data.status_code == 200:
        # save the recording to the directory
        path = os.path.join(directory, "eventdata.gz")
        with open(path, "wb") as f:
            for chunk in r_event_data.iter_content(1024):
                f.write(chunk)
        print("Event data downloaded.")
    else:
        print("Event data not downloaded.")
    r_imu_data = requests.get(
        http_url + f"/recordings/{rec_name}" + "/imudata.gz", stream=True
    )
    if r_imu_data.status_code == 200:
        # save the recording to the directory
        path = os.path.join(directory, "imudata.gz")
        with open(path, "wb") as f:
            for chunk in r_imu_data.iter_content(1024):
                f.write(chunk)
        print("IMU data downloaded.")
    else:
        print("IMU data not downloaded.")
    # get the meta data of the recording
    r_meta_data = requests.get(http_url + f"/recordings/{rec_name}", stream=True)
    if r_meta_data.status_code == 200:
        # read the meta data as a json and extract the key "created"
        meta_data = r_meta_data.json()
        created = meta_data["created"]
        # convert the created string to a datetime object
        created = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(
            hours=glasses_offset
        )

        # created += datetime(hour=2) # offset timestamp
        # save the creation date of the recording to a file
        with open(os.path.join(directory, "start_timestamp.txt"), "w") as f:
            f.write(str(created))
        print("Meta data downloaded.")
    else:
        print("Meta data not downloaded.")

    print("Finished with all download attempts.")


class RecordingsHub:
    """Class representing the recordings Hub"""

    _instance = None
    _is_initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RecordingsHub, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        recordings_hub_widget: QWidget,
        recordings: dict[str, Recording],
        glasses: Glasses3,
        glasses_offset=3,
    ):
        if not self._is_initialized:
            self._is_initialized: bool = True
            # self.recordings_hub_widget: QWidget = recordings_hub_widget
            self.recordings: dict[str, Recording] = recordings
            self.recording_table = QTableWidget()
            self.g3: Glasses3 = glasses
            asyncio.ensure_future(self.define_ui())
            # self.recordings_hub_widget.show()

    async def define_ui(self):
        """Function defining the UI of the Recordings Hub"""
        # add labels of all of the recordings
        self.recording_table.setWindowTitle("Recordings")
        self.recording_table.setRowCount(len(self.recordings))
        self.recording_table.setColumnCount(5)
        self.recording_table.setHorizontalHeaderLabels(
            ["Name", "Date", "Duration", "download", "Delete"]
        )
        self.recording_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recording_table.setAlternatingRowColors(True)
        self.recording_table.setStyleSheet("alternate-background-color: lightblue; background-color: white;")
        self.recording_table.move(0, 0)
        self.recording_table.resize(1170, 500)
        self.recording_table.closeEvent = self.closeEvent
        # lengthen the columns
        self.recording_table.setColumnWidth(0, 400)
        self.recording_table.setColumnWidth(1, 250)
        self.recording_table.setColumnWidth(2, 250)
        self.recording_table.setColumnWidth(3, 100)
        self.recording_table.setColumnWidth(4, 100)

        iteration: int = 0
        for rec_name, rec_obj in self.recordings.items():
            # add the name of the recording
            self.recording_table.setItem(iteration, 0, QTableWidgetItem(rec_name))
            # add the date of the recording
            self.recording_table.setItem(
                iteration, 1, QTableWidgetItem(str(await rec_obj.get_created()))
            )
            # add the duration of the recording
            self.recording_table.setItem(
                iteration, 2, QTableWidgetItem(str(await rec_obj.get_duration()))
            )
            # add a button to download the recording
            download_btn = QPushButton("Download")
            download_btn.clicked.connect(
                lambda _, rec_name=rec_name: self.download_recording(rec_name)
            )
            download_btn.setStyleSheet("background-color: lightgreen;")
            self.recording_table.setCellWidget(iteration, 3, download_btn)
            delete_btn = QPushButton("Delete")
            # download_btn.clicked.connect(lambda _, rec_name=rec_name: self.download_recording(rec_name))
            delete_btn.clicked.connect(
                lambda _, rec_name=rec_name: self.delete_recording(rec_name)
            )
            delete_btn.clicked.connect(lambda _, rec_name=rec_name: self.delete_recording(rec_name))

            self.recording_table.setCellWidget(iteration, 4, delete_btn)

            iteration += 1
        self.recording_table.resizeColumnsToContents()
        self.recording_table.resizeRowsToContents()
        self.recording_table.show()

    def delete_recording_thread(self, rec_name: str, g3: Glasses3, loop):
        # send a request to the glasses to delete the recording
        req_post = g3._connection.generate_post_request(
            "//recordings!delete", [rec_name]
        )
        future = asyncio.run_coroutine_threadsafe(
            g3._connection.require(req_post), loop
        )
        future.result()

        # get the updated list of recordings from the glasses
        future_recordings = asyncio.run_coroutine_threadsafe(
            self.g3.recordings._get_children(), loop
        )
        self.recordings = future_recordings.result()

        # update the UI to reflect the changes in the recordings list
        future_ui = asyncio.run_coroutine_threadsafe(self.define_ui(), loop)
        future_ui.result()

    def download_recording(self, rec_name: str):
        # ask the user to choose a directory to save the recording
        options = QFileDialog.Options()
        directory = QFileDialog.getExistingDirectory(
            self.recording_table, "Select Directory", options=options
        )
        # make a directory for the recording with rec_name as the name
        directory = os.path.join(directory, rec_name)
        # check if the directory exists
        if not os.path.exists(directory):
            os.mkdir(directory)
        threading.Thread(
            target=download_recording_thread,
            args=(rec_name, self.g3.recordings._http_url, directory),
        ).start()
        # thread_function(lambda: download_recording_thread(rec_name, self.g3.recordings._http_url, directory))

    def delete_recording(self, rec_name: str):
        thread_delete = threading.Thread(
            target=self.delete_recording_thread,
            args=(rec_name, self.g3, asyncio.get_event_loop()),
        )
        thread_delete.start()
        # Add your logic here after the thread has finished running

    def closeEvent(self, event):
        """Function to handle the close event"""
        logging.info("RecordingHub window closed.")
        self._instance = None
        self._is_initialized = False
        self.__del__()

    def __del__(self):
        logging.info("Recording Hub instance destroyed.")
