"""Module with all functionality to run the main hub"""
from glasses_hub import GlassesHub
from kinect_hub import KinectHub
from imports import tk


def start_glasses_hub(root) -> None:
    """Function opening the Glasses Hub"""
    glasses_hub: GlassesHub = GlassesHub(root)


def start_kinect_hub(root) -> None:
    """Function opening the Kinect Hub"""
    kinect_hub: KinectHub = KinectHub(root)


def define_main_ui(root: tk.Tk) -> None:
    """Function defining all of the UI elements of the main hub"""
    root.title("Main Hub")
    root.geometry("500x500")
    # Create The title label
    label = tk.Label(root, text="Main Hub")
    label.pack()

    # Create the button for the glasses hub
    glasses_hub_btn = tk.Button(
        root, text="Glasses Hub", command=lambda: start_glasses_hub(root)
    )
    # Create the button for the kinect hub
    kinect_hub_btn = tk.Button(
        root, text="Kinect Hub", command=lambda: start_kinect_hub(root)
    )
    glasses_hub_btn.pack()
    kinect_hub_btn.pack()


def start_main_hub() -> None:
    """Function opening the main hub"""

    # Create the main window
    root = tk.Tk()

    # Define the UI
    define_main_ui(root)

    # Start the event loop
    root.mainloop()
