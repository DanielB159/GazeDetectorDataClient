# GazeDetectorDataClient
#### Short description
This client will be used for data collection of gaze data from G3 glasses - and synchronization of them with a kinect camera.

#### Architecture
We will use python's PyQT5 to build the desktop app, and relevant SDK's for handeling the communication with the camera and the glasses.

#### Libraries and dependencies
The used python libraries are listed in .devcontainer/requirements.txt file. To install them run the following command in the terminal command:
```
pip install -r .devcontainer/requirements.txt
```
- We used python-opencv and numpy for processing the images.
- We used the g3pylib library in order to interface with the G3 glasses, and pykinectAzure library to interface with the kinect camera. In order to install the sub-modules that is the g3pylic libray, run the following commands in the following order:
```
git submodule init
git submodule update
pip install ./g3pylib
```
- the pyKinectAzure is contained within `.devcontainer/requirements.txt`


### NTP (Network Time Protocol)
In order to synchronize the internal clocks of all devices that are being used to record, we need to verify that all of the devices are connected to the same **NTP server**. An NTP server is a server which can synchronize the internal clocks of the devices that are connected to it to a few milliseconds of Coordinated Universal Time (UTC).
In order to record using this client and using the glasses, both the computer running the client and the glasses need to be connected to an NTP server. 

#### Connecting the computer to an NTP server
The computer which is running the client needs to also be connected to an NTP server because it's time is used as an initial value to all of the offsets that are recorded in the kinect (the python library datetime uses the OS internal clock which is determined by the NTP server). To connect the computer to the NTP server: `0.il.pool.ntp.org` follow these instructions (Assuming that you are running Windows): 
1. Open Settings: Go to "Settings" > "Time & Language".
2. Click on "Additional date, time, & regional settings" under the "Related settings" section.
3. Click on "Set the time and date".
4. Go to the "Internet Time" tab and click "Change settings".
5. Check "Synchronize with an Internet time server", enter the NTP server address `0.il.pool.ntp.org`, and click "Update now".
6. Apply and OK: Click "OK" to apply the settings.

### Recordings file structure
```
recordings: 
    > recording_name:
        > Glasses3:
            start_timestamp.txt
            gazedata.gz
            imudata.gz
            scenevideo.mp4
        > Kinect:
            start_timestamp.txt
            [timestamp].png
```

### Kinect Hub
1. The kinect hub has the this functionality:
  - Get live view of the current camera feed with depth or without depth.
  - Record a video feed from the current camera with depth or without depth.
2. The depth is measured in milimeters (one thousanth of a meter)
3. The recordings, if dont without the glasses hub are saved in the following file structure:
###### Recordings file structure
```
recordings: 
    > recording_<timestamp_of_recording>:
        > Kinect:
            > timestamp_1
                timestamp_1_depth_greyscale.png - gryescale depth photo
                timestamp_1_.csv - a .csv file with the depth in milimeters of each pixel
                timestamp_1_depth.png - a RGB photo of the depth
                timestamp_1.png - a colored photo
            > timestamp_2
            ...
```
 
#### Design
##### The client will have one main hub screen:
![image](https://github.com/DanielB159/GazeDetectorDataClient/assets/107650756/aa32c0b8-49d1-409b-8fc3-bce0a77a90a4)

##### The glasses hub button will open a glasses hub screen:
![image](https://github.com/DanielB159/GazeDetectorDataClient/assets/107650756/fabc0a0e-e7f6-46cc-bb1f-4b217e4982e0)

##### The kinect hub button will open a kinect hub screen:
![image](https://github.com/DanielB159/GazeDetectorDataClient/assets/107650756/7a01b8c2-cb95-49e6-aefd-4e608a25fdba)
