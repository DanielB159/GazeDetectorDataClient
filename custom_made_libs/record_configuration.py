from typing import Any
from pykinect_azure.k4a import _k4a
from pykinect_azure.k4arecord import _k4arecord


class RecordConfiguration:
    def __init__(self, configuration_handle=None):
        if configuration_handle:
            self._handle = configuration_handle
        else:
            self.create()
    
    def hande(self):
        return self._handle
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Run on change function when configuration parameters are changed"""
        if hasattr(self, name):
            if name != "_handle":
                if int(self.__dict__[name]) != value:
                    self.__dict__[name] = value
                    self.on_value_change()
            else:
                self.__dict__[name] = value
        else:
            self.__dict__[name] = value
        

    def __getattr__(self, name):
        """Pass the handle parameter, when asked"""
        if name == "_handle":
            return self.__dict__[name]
        else:
            return self._handle.__dict__[name]


    def __str__(self):
        """Print the current settings and a short explanation"""
        message = (
            "Record configuration: \n"
            f"\tcolor_format: {self._handle.color_format} \n\t(0:JPG, 1:NV12, 2:YUY2, 3:BGRA32)\n\n"
            f"\tcolor_resolution: {self._handle.color_resolution} \n\t(0:OFF, 1:720p, 2:1080p, 3:1440p, 4:1536p, 5:2160p, 6:3072p)\n\n"
            f"\tdepth_mode: {self._handle.depth_mode} \n\t(0:OFF, 1:NFOV_2X2BINNED, 2:NFOV_UNBINNED,3:WFOV_2X2BINNED, 4:WFOV_UNBINNED, 5:Passive IR)\n\n"
            f"\tcamera_fps: {self._handle.camera_fps} \n\t(0:5 FPS, 1:15 FPS, 2:30 FPS)\n\n"
            f"\tcolor_track_enabled: {self._handle.color_track_enabled} \n\t(True of False). If Color camera images exist\n\n"
            f"\tdepth_track_enabled: {self._handle.depth_track_enabled} \n\t(True of False). If Depth camera images exist\n\n"
            f"\tir_track_enabled: {self._handle.ir_track_enabled} \n\t(True of False). If IR camera images exist\n\n"
            f"\timu_track_enabled: {self._handle.imu_track_enabled} \n\t(True of False). If IMU samples exist\n\n"
            f"\tdepth_delay_off_color_usec: {self._handle.depth_delay_off_color_usec} us. \n\tDelay between the color image and the depth image\n\n"
            f"\twired_sync_mode: {self._handle.wired_sync_mode}\n\t(0:Standalone mode, 1:Master mode, 2:Subordinate mode)\n\n"
            f"\tsubordinate_delay_off_master_usec: {self._handle.subordinate_delay_off_master_usec} us.\n\tThe external synchronization timing.\n\n"
            f"\tstart_timestamp_offset_usec: {self._handle.start_timestamp_offset_usec} us. \n\tStart timestamp offset.\n\n"
            )
        return message
    
    def create(self):
        self.color_format = _k4a.K4A_IMAGE_FORMAT_COLOR_MJPG
        self.color_resolution = _k4a.K4A_COLOR_RESOLUTION_720P
        self.depth_mode = _k4a.K4A_DEPTH_MODE_WFOV_2X2BINNED
        self.camera_fps = _k4a.K4A_FRAMES_PER_SECOND_30
        self.color_track_enabled = True
        self.depth_track_enabled = True
        self.ir_track_enabled = True
        self.imu_track_enabled = True
        self.depth_delay_off_color_usec = 0
        self.wired_sync_mode = _k4a.K4A_WIRED_SYNC_MODE_STANDALONE
        self.subordinate_delay_off_master_usec = 0
        self.start_timestamp_offset_usec = 0

        self.on_value_change()

    def create_from_handle(self, configuration_handle):
        self.color_format = configuration_handle.color_format
        self.color_resolution = configuration_handle.color_resolution
        self.depth_mode = configuration_handle.depth_mode
        self.camera_fps = configuration_handle.camera_fps
        self.color_track_enabled = configuration_handle.color_track_enabled
        self.depth_track_enabled = configuration_handle.depth_track_enabled
        self.ir_track_enabled = configuration_handle.ir_track_enabled
        self.imu_track_enabled = configuration_handle.imu_track_enabled
        self.depth_delay_off_color_usec = configuration_handle.depth_delay_off_color_usec
        self.wired_sync_mode = configuration_handle.wired_sync_mode
        self.subordinate_delay_off_master_usec = configuration_handle.subordinate_delay_off_master_usec
        self.start_timestamp_offset_usec = configuration_handle.start_timestamp_offset_usec

        self._handle = configuration_handle

    def on_value_change(self):
        self._handle = _k4arecord.k4a_record_configuration_t(self.color_format, \
                                            self.color_resolution,\
                                            self.depth_mode,\
                                            self.camera_fps,\
                                            self.color_track_enabled,\
                                            self.depth_track_enabled,\
                                            self.ir_track_enabled,\
                                            self.imu_track_enabled,\
                                            self.depth_delay_off_color_usec,\
                                            self.wired_sync_mode,\
                                            self.subordinate_delay_off_master_usec,\
                                            self.start_timestamp_offset_usec)
                  

default_configuration_record = RecordConfiguration()