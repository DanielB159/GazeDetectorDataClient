# import glasses_hub
# import kinect_hub
import asyncio

class RecordingManager:
    _instance = None
    _is_initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RecordingManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._is_initialized:
            # self.glasses_hub : glasses_hub.GlassesHub = None
            # self.kinect_hub : kinect_hub.KinectHub = None
            self.glasses_is_connected = False
            self.glasses_is_recording = False
            self.kinect_is_recording = False

    def is_glasses_available(self):
        print(self.glasses_hub)
        print(self.glasses_is_connected)
        print(self.glasses_is_recording)
        return self.glasses_hub and self.glasses_is_connected and not self.glasses_is_recording
    
    def is_kinect_available(self):
        print(self.kinect_hub)
        print(self.kinect_is_recording)
        return self.kinect_hub and not self.kinect_is_recording
