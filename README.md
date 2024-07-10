# GazeDetectorDataClient
#### Short description
This client manages the simultaneous recording from a USB connected Azure Kinect DK, and a Tobii Glasses3 unit over Wi-Fi.
It also contains a module for synchronizing those recordings and organizing them.

#### Architecture
This implementation uses python’s PyQT5 for the desktop UI, and relevant SDKs for handling the communication with the camera and the glasses.

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

##### **Note:** Be sure to check the Glasses3 developer guide at "https://go.tobii.com/tobii-pro-glasses-3-developer-guide".

### Usage
This section is a step by step explanation of how to make use of this client to create a recording. Individual explanation of components will be detailed on later sections.

#### Client hubs
Both the glasses and the kinect individually communicate with their respective hubs, where you can interact with them individually.
To record them simultaneously both hubs must be running, which will allow the main hub to run the recordings both at once.

#### Connect to glasses
The client and the Glasses3 unit must be on the same network to communicate:
1. Connect a computer to the Glasses3 unit via an ethernet cable. Or connect to the wifi signal that the glasses broadcast while not connected to any network.
2. On your browser, connect to 'http://\<g3-address\>'. Where \<g3-address\> is by default the serial number of the glasses. Ex. 'TG03B-080202048921'. Note that some browsers fail to find this DNS address, and instead you have to replace \<g3-address\> with the glasses's ip that is connected to your computer. We found that Firefox is consistently able to connect.
3. Go to "Network".
4. Create a new configuration, set ipv4 mode to dhcp, SSID to your network name, if the network is passowrd protected then set Security to wpa-psk and put the password under Pre Shared Key.
5. Mark AutoConnect on and hit apply.
6. On the Glasses Hub window, input the in network ipv4 address of the glasses. Ex. '192.168.80.29'
7. The glasses should now automatically connect to the network, and the client will be able to communicate with them.

#### Calibration
With each new wearer, the glasses must be calibrated to them for best gaze detection accuracy. 
1. The wearer should hold up the calibration cards an arm's length away from their face, and stare directly at the dot on center on the card. 
2. Open the Glasses Hub, connect to your Glasses3 unit with the "Connect" button.
3. Click the "Calibrate" button, and wait for the calibration to succeed.
Should the calibration be successful, you are now ready to start the recording. *NOTE add calibration notification. *NOTE add verification instructions

#### Recording procedure
1. Before starting a new recording, make sure both hubs are running, and connect to the glasses in the Glasses Hub.
2. Using the glasses API webpage at 'http://\<g3-address\>', under the API tab > network, you may request to see the glasses current time. Set the offset on the Glasses Hub to fix any time difference between your computer's time and the glasses'. This will usually be because the glasses are at a different timezone to yours.
3. Click the "Start Recording" button on the Main Hub, this will start a recording on both the glasses and kinect.
4. When the recording is complete, click the "End Recording" button on the Main Hub to stop the recording. This will then download and compile all files into the "recordings" folder.
Note: To abort a recording without saving it to the glasses, hit "Cancel Recording" instead.
*NOTE risks of running the recording too long.

[Synchronization!!!]
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
    > recording_name (timestamp_of_recording):
        > Glasses3:
            start_timestamp.txt
            gazedata.gz
            imudata.gz
            eventdata.gz
            scenevideo.mp4
        > Kinect:
            > timestamp_1
                timestamp_1_depth_greyscale.png    - gryescale depth photo
                timestamp_1_.csv                   - a .csv file with the depth in milimeters of each pixel
                timestamp_1_depth.png              - a RGB photo of the depth
                timestamp_1.png                    - a colored photo
            > timestamp_2
            ...
```

#### Data and recordings
explanation of the data recorded

### Component explanation

#### Main Hub
The main hub is used to manage both the kinect and glasses hubs together:
  - The "Glasses Hub" and "Kinect Hub" buttons open their corresponding hubs.
  - The "Start Recording", "End Recording" and "Cancel Recording" buttons control recording with *both* devices at once.
    Both hubs must be running and neither in the process of a recording to begin a recording from the main hub/

#### Kinect Hub
1. The kinect hub has the this functionality:
  - Get live view of the current camera feed with depth or without depth.
  - Record a video feed from the current camera with depth or without depth.
2. The depth is measured in milimeters (one thousanth of a meter)
3. The recordings, if dont without the glasses hub are saved in the following file structure:

#### Glasses Hub
The galsses hub is used to manage the glasses individually:
  - "Connect" and "Disconnect" buttons connect you to the Glasses3 unit to be able to send request to it.
  - "Start Live View" allows you to see in real time the video feed from the glasses forward facing camera. [Note] quit with q
  - "Calibrate" button is used in the calibration procedure to calibrate the glasses to the wearer.
  - "Start Recording", "Stop Recording" and "Cancel Recording" buttons control recording from the glasses individually.
  - "SD Info" button requests how much battery and space on the SD card remains in the unit.
  - "Storage Recordings" button lets you browse, download and delete past recordings from the glasses unit.
  - "Change IP" is used to input the glasses ipv4 in your network.
  - "Change Glasses Offset" is used to change the offset of time between the glasses and your machine.

[hubs] are singletons