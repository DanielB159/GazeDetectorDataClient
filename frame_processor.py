import json # import somewhere else
import os   # later do for the entire directory
import cv2
import shutil
import gzip
import heapq
import numpy as np

REC_DIR_LOC = './recordings'    #linux?
POST_DIR_LOC = './processed_recordings'
rec_name = 'test'

class FrameData:
    def __init__(self, recording_name: str, timestamp_offset: float, glasses_gyro : np.array):
        self.recording_name = recording_name
        
        self.kinect_image : str = None      # name of timestamp.png
        self.glasses_imu : dict = None      # current imu data
        self.glasses_gaze : dict = None     # current gaze data
        self.glasses_image : float = None   # cv2 float

        # IMPORTANT assume all timestamps given are in absolute time (meaning already added the offset)
        self.gyro_state : np.array = glasses_gyro   # 3d vector of direction relative to glasses
        self.gyro_timestamp : float = timestamp_offset

    def save_frame(self):
        # TODO: dont let it override
        recording_path = REC_DIR_LOC + "/" + self.recording_name
        post_path = POST_DIR_LOC + "/" + self.recording_name
        if (not os.path.exists(post_path)):
            # create recording directory if none exist
            os.mkdir(post_path)
        if (os.path.exists(post_path + "/" + self.kinect_image_name)):
            # remove frame to replace it if already exists
            shutil.rmtree(post_path + "/" + self.kinect_image_name)
        
        os.mkdir(post_path + "/" + self.kinect_image_name)    # create dir for frame
        shutil.copy2(recording_path + "/Kinect/" + self.kinect_image_name + ".png",
                     post_path + "/" + self.kinect_image_name + "/" + self.kinect_image_name + ".png")
        
        imu_file = open(post_path + "/" + self.kinect_image_name + "/imu_data.txt", 'w')
        imu_file.write(str(self.gyro_state))
        imu_file.close()

        print(post_path + "/" + self.kinect_image_name + "/")   # save current frame to a new folder

    # need more incapsulation for adding imu and shit
    def update_kinect_image(self, name : int):
        self.kinect_image_name = str(name)
        # timestamp is 10^(-6)
    
    def update_glasses_imu(self, data : dict):
        if "gyroscope" in data["data"]:
            # update gyro
            deltaTime = data["timestamp"] - self.gyro_timestamp
            print(data["data"]["gyroscope"])
            temp = deltaTime * np.array(data["data"]["gyroscope"], float)
            self.gyro_state += temp
            self.gyro_timestamp = data["timestamp"]
        self.glasses_imu = data
    
    def update_glasses_gaze(self, data : dict):
        self.glasses_gaze = data
    
    def update_glasses_image(self, image: float):
        self.glasses_image = image

def process_frames():
    current_dir = REC_DIR_LOC + '/' + rec_name
    
    with gzip.open(current_dir + '/Glasses3/gazedata.gz', 'rb') as f:
        lines = f.readlines()
        glasses_gaze_data = []  # keys are timestamps!
        for line in lines:
            dict = json.loads(line[: -1])
            glasses_gaze_data.append((dict["timestamp"], dict))
        heapq.heapify(glasses_gaze_data)
        #print(glasses_gaze_data)

    # with open(current_dir + '/Glasses3/gazedata.gz') as f:
    #     glasses_gaze_data = json.load(f)
    #     print(glasses_gaze_data)
    
    with gzip.open(current_dir + '/Glasses3/imudata.gz', 'rb') as f:    # split to accel and magno
        lines = f.readlines()
        glasses_imu_data = []
        for line in lines:
            dict = json.loads(line[: -1])
            is_magnetometer = False
            if "magnetometer" in dict["data"]:
                is_magnetometer = True
                # to separate equal timestamps
            glasses_imu_data.append((dict["timestamp"], is_magnetometer, dict))
        heapq.heapify(glasses_imu_data)
        #print(glasses_imu_data)

    # with open(current_dir + '/Glasses3/imudata.gz') as f:
    #     glasses_imu_data = json.load(f)
    
    glasses_video = cv2.VideoCapture(current_dir + '/Glasses3/scenevideo.mp4')
    glasses_video_fps = glasses_video.get(cv2.CAP_PROP_FPS)
    glasses_video_frame_total = glasses_video.get(cv2.CAP_PROP_FRAME_COUNT)  # total frame count

    kinect_images_strings = os.listdir(current_dir + '/Kinect') # list of file names
    kinect_images_timestamps = []
    for s in kinect_images_strings:
        if (s[-4:] == ".png"):
            try:
                kinect_images_timestamps.append(int(s[:-4]))
            except:
                print("Warning: " + s + " is not in the correct format for a Kinect recording file.")
    heapq.heapify(kinect_images_timestamps)

    # now create a dictionary with time, type, and info
    # perhaps for things like mp4 have the info just be frame number or next frame

    # HOW TO READ FROM MP4
    # while success: 
  
    #     # vidObj object calls read 
    #     # function extract frames 
    #     success, image = vidObj.read() 
  
    #     # Saves the frames with frame-count 
    #     cv2.imwrite("frame%d.jpg" % count, image) 
  
    #     count += 1

    # FROM THIS POINT ON, ASSUME SYNCHRONIZATION
    glasses_imu_start = 0   # start time relative to outer video
    glasses_gaze_start = 0
    glasses_video_start = 0
    kinect_video_start = 0  # will always be 0 since this is the relative point - 10^-6 of a second

    MAX_INT = pow(2, 32)
    KINECT_MUL = pow(10, -6)
    current_frame = FrameData(recording_name=rec_name ,timestamp_offset=glasses_imu_start, glasses_gyro=np.array([0, 0, 0], float))

    # TODO: make sure the timestamps actually mean the same thing and do the synchronization!
    # TODO: actually update the gyro stuff
    # init minimal values
    vid_frame_exists, image = glasses_video.read()
    if (vid_frame_exists):
        min_glasses_video_timestamp = glasses_video.get(cv2.CAP_PROP_POS_MSEC)
    else:
        min_glasses_video_timestamp = MAX_INT
    if (len(kinect_images_timestamps) > 0):
        min_kinect_timestamp = kinect_images_timestamps[0] * KINECT_MUL
    else:
        min_kinect_timestamp = MAX_INT
    if (len(glasses_gaze_data) > 0):
        min_gaze_timestamp = glasses_gaze_data[0][0]
    else:
        min_gaze_timestamp = MAX_INT
    if (len(glasses_imu_data) > 0):
        min_glasses_imu_timestamp = glasses_imu_data[0][0]
    else:
        min_glasses_imu_timestamp = MAX_INT

    while len(kinect_images_timestamps) > 0:
        min_timestamp = min(min_glasses_video_timestamp,
                            min_glasses_imu_timestamp,
                            min_gaze_timestamp,
                            min_kinect_timestamp)
        print(min_timestamp)

        # prio updating before saving a new kinect image
        if (min_timestamp == min_glasses_video_timestamp):
            current_frame.update_glasses_image(image)
            vid_frame_exists, image = glasses_video.read()
            # update min glasses timestamp
            if (vid_frame_exists):
                min_glasses_video_timestamp = glasses_video.get(cv2.CAP_PROP_POS_MSEC)
            else:
                # doesnt exist, remove image?
                min_glasses_video_timestamp = MAX_INT
        elif (min_timestamp == min_gaze_timestamp):
            current_frame.update_glasses_gaze(glasses_gaze_data[0][1])
            # update min glasses timestamp
            if (len(glasses_gaze_data) > 1):
                # if not then cant pop
                heapq.heappop(glasses_gaze_data)
                min_gaze_timestamp = glasses_gaze_data[0][0]
            else:
                # doesnt exist, remove image cuz outdated?
                if (len(glasses_gaze_data) == 1):
                    # empty the queue
                    heapq.heappop(glasses_gaze_data)
                min_gaze_timestamp = MAX_INT
        elif (min_timestamp == min_glasses_imu_timestamp):
            current_frame.update_glasses_imu(glasses_imu_data[0][2])
            # update min glasses timestamp
            if (len(glasses_imu_data) > 1):
                # if not then cant pop
                heapq.heappop(glasses_imu_data)
                min_glasses_imu_timestamp = glasses_imu_data[0][0]
            else:
                if (len(glasses_gaze_data) == 1):
                    # empty the queue
                    heapq.heappop(glasses_imu_data)
                min_glasses_imu_timestamp = MAX_INT
        elif (min_timestamp == min_kinect_timestamp):
            current_frame.update_kinect_image(kinect_images_timestamps[0])
            current_frame.save_frame()  # save each frame of kinect data
            # update min kinect timestamp
            if (len(kinect_images_timestamps) > 1):
                # if not then cant pop
                heapq.heappop(kinect_images_timestamps)
                min_kinect_timestamp = kinect_images_timestamps[0] * KINECT_MUL
            else:
                if (len(kinect_images_timestamps) == 1):
                    # empty the queue
                    heapq.heappop(kinect_images_timestamps)
                min_kinect_timestamp = MAX_INT
        else:
            print ("Error: timestamp does not exist.")

process_frames()