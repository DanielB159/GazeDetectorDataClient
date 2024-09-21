# GazeDetectorDataClient
#### Short description
This client manages the simultaneous recording from a USB connected Azure Kinect, and a Tobii Glasses3 unit over Wi-Fi.
It also contains a module for synchronizing those recordings and organizing them.

#### Architecture
This implementation uses python’s PyQT5 for the desktop UI, Azure Kinect SDK for handling the communication with the kinect camera, and the g3pylib python library for the glasses.

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

##### **Note:** Be sure to install the Azure Kinect SDK 1.4.1.exe which contains the relevant firmware for the Azure Kinect. 
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
4. Create a new configuration, set ipv4 mode to dhcp, SSID to your network name, if the network is password protected then set Security to wpa-psk and put the password under Pre Shared Key.
5. Mark AutoConnect on and hit apply.
6. On the Glasses Hub window, input the in network ipv4 address of the glasses. Ex. '192.168.80.29'
7. The glasses should now automatically connect to the network, and the client will be able to communicate with them.

#### Calibration
With each new wearer, the glasses must be calibrated to them for best gaze detection accuracy. 
1. The wearer should hold up the calibration cards an arm's length away from their face, and stare directly at the dot on center on the card. 
2. Open the Glasses Hub, connect to your Glasses3 unit with the "Connect" button.
3. Click the "Calibrate" button, and wait for the calibration to succeed.
4. Should the calibration be successful, which is indicated by an output in the console, you are now ready to start the recording.
Note: It is often useful to calibrate while watching the Live View, this is a good way to confirm the calibration is actually successful and the gaze direction is accurate.

#### Recording procedure
1. Notice that the recording uses an .env file for default configuration of the glasses hostname and of the glasses time offset. You can find an example .env file in the project directory.
2. Before starting a new recording, make sure both hubs are running, and connect to the glasses in the Glasses Hub. You may need to update the "G3_HOSTNAME" variable in the environemnt variables file to the glasses' ipv4 in your network. Or update it within the glasses hub. 
3. The glasses NTP server and your own computer's NTP server may be in different time zones. Make sure to modify the "GLASSES_OFFSET" variable in the environment variables file, so that the program can synchronize both recordings. Or update it within the glasses hub.
4. Using the glasses API webpage at 'http://\<g3-address\>', under the API tab > network, you may request to see the glasses current time. Set the offset on the Glasses Hub to fix any time difference between your computer's time and the glasses'. This will usually be because the glasses are at a different timezone to yours.
5. Click the "Start Recording" button on the Main Hub, this will start a recording on both the glasses and kinect.
6. When the recording is complete, click the "End Recording" button on the Main Hub to stop the recording. This will then download and compile all files into the "recordings" folder.
Note: To abort a recording without saving it to the glasses, hit "Cancel Recording" instead.
Note: 

### Recordings file structure
```
recordings: 
    > recording_name (timestamp_of_recording):
        > Glasses3:
            start_timestamp.txt                    - exact time at which the glasses began recording, based on the glasses' clock
            gazedata.gz                            - compressed JSON with data about the gaze directions
            imudata.gz                             - compressed JSON with IMU data about the glasses
            eventdata.gz                           - compressed JSON with data about events in the glasses, mostly unused
            scenevideo.mp4                         - video recording from the glasses camera
        > Kinect:
            start_timestamp.txt                    - time at which the kinect began recording
            > timestamp_1
                timestamp_1_depth_greyscale.png    - gryescale depth photo
                timestamp_1_.csv                   - a .csv file with the depth in milimeters of each pixel
                timestamp_1_depth.png              - a RGB photo of the depth
                timestamp_1.png                    - a colored photo
            > timestamp_2
            ...
```

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

#### Glasses Hub
The galsses hub is used to manage the glasses individually:
  - "Connect" and "Disconnect" buttons connect you to the Glasses3 unit to be able to send request to it.
  - "Start Live View" allows you to see in real time the video feed from the glasses forward facing camera.
  - "Calibrate" button is used in the calibration procedure to calibrate the glasses to the wearer.
  - "Start Recording", "Stop Recording" and "Cancel Recording" buttons control recording from the glasses individually.
  - "SD Info" button requests how much battery and space on the SD card remains in the unit.
  - "Storage Recordings" button lets you browse, download and delete past recordings from the glasses unit.
  - "Change IP" is used to input the glasses ipv4 in your network.
  - "Change Glasses Offset" is used to change the offset of time between the glasses and your machine.

* Recording may be done in each hub independently, in which case will be saved in its own folder.

### Frame Processor
The frame processor is an additional program that pre-processes the images and gaze data before transforming it to fit the camera's axes. It also filters some inconsistent images that do not have adequately accurate gaze information in relation to the kinect image.
It synchronizes the recording and splits them into folders by timestamp, with the appropriate kinect image, depth information, and gaze information for that timestamp.
To run, make sure that your recording is the "recordings" folder, and run the command line prompt of:
> python frame_processor.py "recording_folder_name"     (without a folder location ./recordings)
At which point the procedure will run, and save the result into the "processed_recordings" folder.
Each processed recording will have the file structure of:
```
recordings: 
    > recording_name (timestamp_of_recording):
        > timestamp1:
            timestamp1.png                          - kinect image
            timestamp1.csv                          - csv of depth information
            gaze_data.gz
        > timestamp2:
            timestamp2.png
            timestamp2.csv
            gaze_data.gz
        ...
```
**Note:** We added a powershell script `process_all_recordings` for running frame processor on all of the recording folders in the `/recordings` directory. It should e ran from the main directory of the repo.

### Implementation details
the implementation details are explicitly described in the project report file.