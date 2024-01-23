
from pykinect_azure import k4a, default_configuration, Device, Capture, ImuSample
import pykinect_azure as pykinect
import cv2
import numpy as np


if __name__ == '__main__':

    # Configure the device for camera and IMU
    device_config = default_configuration
    pykinect.initialize_libraries()
    device : Device = pykinect.start_device(config=device_config)
    while True:
        capture: Capture = device.update()
        img_obj = capture.get_color_image_object()
        # ret, raw_color_image = capture.get_color_image()
        ret, raw_color_image = img_obj.to_numpy()
        
        imu_sample : ImuSample = ImuSample(device.get_imu_sample())

        print("Gyro Time:", imu_sample.get_gyro_time())
        
        if not ret:
            continue
        image : np.ndarray = cv2.putText(raw_color_image, "Test", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow("Test", image)




        # Press q to exit
        if cv2.waitKey(1) == ord('q'):
            cv2.destroyWindow("Test")
            break
    device.close()
    cv2.destroyAllWindows()