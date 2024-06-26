import json # import somewhere else
import os   # later do for the entire directory
import cv2
import shutil
import gzip
import heapq
import numpy as np
from datetime import datetime, timedelta
import copy

REC_DIR_LOC = './recordings'    #linux?
POST_DIR_LOC = './processed_recordings'
rec_name = '2024-06-12 17_01_48.832935'

class FrameData:
    # NOTE: all timestamps must already be synchronized to the kinect image at this point
    def __init__(self, recording_name: str, glasses_gyro : np.array):
        self.recording_name = recording_name
        
        self.kinect_image_name : str = None      # name of timestamp.png
        self.current_gaze : list = []     # gaze data queue for the latest kinect image, changes every save
        self.glasses_imu : dict = None      # current imu data
        self.glasses_gaze : list = []     # gaze data queue, will keep updating after save
        # keep enqueueing, dequeue to needed time with new kinect image
        self.glasses_image : float = None   # cv2 float

        self.gaze_time_threshold : float = 1    # seconds, earliest gaze delta time to compare against
        self.gaze_time_epsilon : float = 0.1    # seconds, earliest gaze delta time to consider saving
        self.gaze_distance_episilon: float = .5  # ?, largest distance to allow for eye movement or something
        self.variance_epsilon: float = 0.5

    # check if this sample can be trusted
    def validate_sample(self) -> bool:
        if self.kinect_image_name == None:
            # no image to save
            return False
        if len(self.current_gaze) == 0:
            # not enough gaze samples
            return False
        
        latest_gaze = self.current_gaze[len(self.current_gaze) - 1]

        def normalize(v):
            norm = np.linalg.norm(v)
            if norm == 0:
                return v    # problem!
            return np.divide(v, norm)
        direction_list = []
        for sample in self.current_gaze:
            direction_list.append(normalize(sample["data"]["gaze3d"]))    # what if 0

        # verify most recent gaze data is not too far
        if (abs((float(self.kinect_image_name) * (10**-6)) - latest_gaze["timestamp"]) > self.gaze_time_epsilon):
            # most recent gaze data too far back in the timeline
            return False
        
        # verify most recent gaze data is not too far from the mean
        mean_gaze = np.mean(direction_list)
        if (np.linalg.norm(mean_gaze - normalize(latest_gaze["data"]["gaze3d"])) > self.gaze_distance_episilon):
            return False
        
        # verify not too much movement happened
        if (np.var(direction_list) > self.variance_epsilon):
            return False

        return True


    def save_frame(self):
        if not self.validate_sample():
            return

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
        shutil.copy2(recording_path + "/Kinect/" + self.kinect_image_name + "/" + self.kinect_image_name + ".png",
                     post_path + "/" + self.kinect_image_name + "/" + self.kinect_image_name + ".png")
        shutil.copy2(recording_path + "/Kinect/" + self.kinect_image_name + "/" + self.kinect_image_name + "_depth.csv",
                     post_path + "/" + self.kinect_image_name + "/" + self.kinect_image_name + "_depth.csv")
        
        imu_file = open(post_path + "/" + self.kinect_image_name + "/gaze_data.json ", 'w')
        imu_file.write(str(self.current_gaze[len(self.current_gaze) - 1]))
        imu_file.close()

        print(post_path + "/" + self.kinect_image_name + "/")   # save current frame to a new folder

    # need more encapsulation for adding imu and shit
    def update_kinect_image(self, name : int):
        self.kinect_image_name = str(name)
        # timestamp is 10^(-6)
        while (len(self.glasses_gaze) > 0) and (abs((float(self.kinect_image_name) * (10**-6)) - self.glasses_gaze[0]["timestamp"]) > self.gaze_time_threshold):
            # gaze sample too far to be considered
            self.glasses_gaze.pop(0) # remove item from the queue
        self.current_gaze = copy.deepcopy(self.glasses_gaze) # copy current content to the current gaze
    
    def update_glasses_imu(self, data : dict):
        if "gyroscope" in data["data"]:
            # update gyro
            self.glasses_imu = data
    
    def update_glasses_gaze(self, data : dict):
        # enqueue new gaze data
        self.glasses_gaze.append(data)
    
    def update_glasses_image(self, image: float):
        self.glasses_image = image

def process_frames():
    current_dir = REC_DIR_LOC + '/' + rec_name
    
    # get offset of glasses and kinect
    with open(current_dir + '/Kinect/start_timestamp.txt', 'r') as f:
        time_str = f.readline()
        print(time_str)
        kinect_start_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")

    with open(current_dir + '/Glasses3/start_timestamp.txt', 'r') as f:
        time_str = f.readline()
        print(time_str)
        glasses_start_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")

    # deduct offset to glasses timestamp to synchronize
    delta_start_time = glasses_start_time - kinect_start_time
    glasses_offset = delta_start_time.seconds + ((10**(-6)) * delta_start_time.microseconds)

    with gzip.open(current_dir + '/Glasses3/gazedata.gz', 'rb') as f:
        lines = f.readlines()
        glasses_gaze_data = []  # keys are timestamps!
        for line in lines:
            dict = json.loads(line[: -1])
            dict["timestamp"] -= glasses_offset # synchronize glasses with kinect
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
            
            dict["timestamp"] -= glasses_offset # synchronize glasses with kinect
            glasses_imu_data.append((dict["timestamp"], is_magnetometer, dict))
        heapq.heapify(glasses_imu_data)
        #print(glasses_imu_data)

    # with open(current_dir + '/Glasses3/imudata.gz') as f:
    #     glasses_imu_data = json.load(f)
    
    # NOTE: not sycnrhonized
    glasses_video = cv2.VideoCapture(current_dir + '/Glasses3/scenevideo.mp4')
    glasses_video_fps = glasses_video.get(cv2.CAP_PROP_FPS)
    glasses_video_frame_total = glasses_video.get(cv2.CAP_PROP_FRAME_COUNT)  # total frame count

    kinect_images_strings = os.listdir(current_dir + '/Kinect') # list of file names
    kinect_images_timestamps = []
    for s in kinect_images_strings:
        if (s[-4:] != ".txt"):
            try:
                kinect_images_timestamps.append(int(s))
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
    current_frame = FrameData(recording_name=rec_name, glasses_gyro=np.array([0, 0, 0], float))

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