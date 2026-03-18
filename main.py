

from models import model
from models.model import RoboModel
from views import MainView
from controllers import *
import tkinter as tk

class Application:
    def __init__(self):
        self.root = root
        self.root.title("Cobot Client")
        self.root.geometry("1024x760")
        self.view = MainView(self.root)

        self.controller = Controller(self.view)
        self.view.create_main_view(self.root)
        self.model = RoboModel(self.controller)



    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = Application()
    app.run()