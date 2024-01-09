# GazeDetectorDataClient
#### Short description
This client will be used for data collection for netural network training - a CNN for gaze detection.

#### Architecture
We will use python's Tkinter to build the desktop app, and relevant SDK's for handeling the communication with the camera and the glasses.

#### Libraries and dependencies
The used python libraries are listed in .devcontainer/requirements.txt file. To install them run the following command in the terminal command:
```
pip install -r .devcontainer/requirements.txt
```
We also used the g3pylib library in order to interface with the G3 glasses. In order to install the sub-module that is the g3pylic libray, run the following commands in the following order:
```
git submodule init
git submodule update
pip install ./g3pylib
```

### NTP (Network Time Protocol)
In order to synchronize the internal clocks of all devices that are being used to record, we need to verify that all of the devices are connected to the same **NTP server**. An NTP server is a server which can synchronize the internal clocks of the devices that are connected to it to a few milliseconds of Coordinated Universal Time (UTC).
In order to record using this client and using the glasses, both the computer running the client and the glasses need to be connected to an NTP server. 

#### Connecting the computer to an NTP server
The computer which is running the client needs to also be connected to an NTP server because it's time is used as an initial value to all of the offsets that are recorded in the kinect (the python library datetime uses the OS internal clock which is determined by the NTP server). To connect the computer to the NTP server: `server 0.il.pool.ntp.org` follow these instructions (Assuming that you are running Windows): 
1. Open Settings: Go to "Settings" > "Time & Language".
2. Click on "Additional date, time, & regional settings" under the "Related settings" section.
3. Click on "Set the time and date".
4. Go to the "Internet Time" tab and click "Change settings".
5. Check "Synchronize with an Internet time server", enter the NTP server address `server 0.il.pool.ntp.org`, and click "Update now".
6. Apply and OK: Click "OK" to apply the settings.


### Kinect Hub
The kinect hub has the current functionality:
- Get live view of the current camera feed.
- Record a video feed from the current camera.
  **Note:** The recording does not save a recording file, but saves the recording in **images** in the filepath recordings/recording(x) where x is the lowest natural number that is not taken in this path. After the recording is done a *start_timestamp.txt* file is also saved with the UTC+2 start time of the recording (Israel time).

#### Design
##### The client will have one main hub screen:
![image](https://github.com/DanielB159/GazeDetectorDataClient/assets/107650756/aa32c0b8-49d1-409b-8fc3-bce0a77a90a4)

##### The glasses hub button will open a glasses hub screen:
![image](https://github.com/DanielB159/GazeDetectorDataClient/assets/107650756/fabc0a0e-e7f6-46cc-bb1f-4b217e4982e0)

##### The kinect hub button will open a kinect hub screen:
![image](https://github.com/DanielB159/GazeDetectorDataClient/assets/107650756/7a01b8c2-cb95-49e6-aefd-4e608a25fdba)
