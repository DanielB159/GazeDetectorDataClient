from glassesHub import GlassesHub
from kinectHub import KinectHub
from imports import tk


def start_glasses_hub(root) -> None:
    """Function opening the Glasses Hub"""
    glasses_hub: GlassesHub = GlassesHub(root)


def start_kinect_hub(root) -> None:
    """Function opening the Kinect Hub"""
    kinect_hub: KinectHub = KinectHub(root)

def start_main_hub() -> None:
    """Function opening the main hub"""
    
    # Create the main window
    root = tk.Tk()
    root.title("Main Hub")
    root.geometry("500x500")

    # Create The title label
    label = tk.Label(root, text="Main Hub")
    label.pack()

    # Create the button for the glasses hub
    button = tk.Button(
        root, text="Glasses Hub", command=lambda: start_glasses_hub(root)
    )
    # Create the button for the kinect hub
    button = tk.Button(
        root, text="Kinect Hub", command=lambda: start_kinect_hub(root)
    )
    button.pack()

    # Start the event loop
    root.mainloop()
