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

#### Design
##### The client will have one main hub screen:
![image](https://github.com/DanielB159/GazeDetectorDataClient/assets/107650756/aa32c0b8-49d1-409b-8fc3-bce0a77a90a4)

##### The glasses hub button will open a glasses hub screen:
![image](https://github.com/DanielB159/GazeDetectorDataClient/assets/107650756/fabc0a0e-e7f6-46cc-bb1f-4b217e4982e0)

##### The kinect hub button will open a kinect hub screen:
![image](https://github.com/DanielB159/GazeDetectorDataClient/assets/107650756/7a01b8c2-cb95-49e6-aefd-4e608a25fdba)
