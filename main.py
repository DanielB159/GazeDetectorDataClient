"""Module for running the main function"""
from main_hub import start_main_hub
from imports import dotenv

if __name__ == "__main__":
    dotenv.load_dotenv()
    start_main_hub()


#  self.recording_table.setWindowTitle("Recordings")
#         self.recording_table.setRowCount(len(self.recordings))
#         self.recording_table.setColumnCount(5)
#         self.recording_table.setHorizontalHeaderLabels(
#             ["Name", "Date", "Duration", "Download", "Delete"]
#         )
#         self.recording_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
#         self.recording_table.setAlternatingRowColors(True)
#         self.recording_table.setStyleSheet("alternate-background-color: lightblue; background-color: white;")
#         self.recording_table.move(0, 0)
#         self.recording_table.resize(1170, 500)
#         self.recording_table.closeEvent = self.closeEvent

#         iteration = 0
#         for rec_name, rec_obj in self.recordings.items():
#             self.recording_table.setItem(iteration, 0, QTableWidgetItem(rec_name))
#             self.recording_table.setItem(iteration, 1, QTableWidgetItem(str(await rec_obj.get_created())))
#             self.recording_table.setItem(iteration, 2, QTableWidgetItem(str(await rec_obj.get_duration())))

#             download_btn = QPushButton("Download")
#             download_btn.setStyleSheet("background-color: lightgreen;")
#             download_btn.clicked.connect(lambda _, rec_name=rec_name: self.download_recording(rec_name))
#             self.recording_table.setCellWidget(iteration, 3, download_btn)

#             delete_btn = QPushButton("Delete")
#             delete_btn.setStyleSheet("background-color: lightcoral;")
#             delete_btn.clicked.connect(lambda _, rec_name=rec_name: self.delete_recording(rec_name))
#             self.recording_table.setCellWidget(iteration, 4, delete_btn)

#             iteration += 1

#         self.recording_table.resizeColumnsToContents()
#         self.recording_table.resizeRowsToContents()
        