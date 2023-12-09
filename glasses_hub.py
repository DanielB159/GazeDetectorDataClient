"""Module with glasses hub class and methods"""
from imports import tk


class GlassesHub:
    """Class representing the Kinect Hub"""

    _instance = None
    _is_initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GlassesHub, cls).__new__(cls)
        return cls._instance

    def __init__(self, root: tk.Tk):
        if not self._is_initialized:
            self._is_initialized = True
            self.root = root
            self.top_level = tk.Toplevel(root)
            self.top_level.title("Glasses Hub")
            self.top_level.geometry("500x500")
            self.top_level.protocol("WM_DELETE_WINDOW", self.__del__)
            self.define_ui()

    def define_ui(self):
        """Function defining the UI of the Glasses Hub"""
        # Create The title label
        label = tk.Label(self.top_level, text="Glasses Hub")
        label.pack()

    def __del__(self):
        self.top_level.destroy()
        self._instance = None
        self._is_initialized = False
