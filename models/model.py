import time
import tkinter as tk
from tkinter import *
from server import *

from pymycobot import MyCobot280
from pymycobot import MyCobot280Socket
from PIL import ImageColor

from server.client import VideoReceiver


def update_coords(func):
    def wrapper(self, *args, **kwargs):
        print(self.mc.get_angles())

        result = func(self, *args, **kwargs)
        return result

    return wrapper


class RoboModel:
    def __init__(self, controller):
        self.dummy = ""
        self.controller = controller
        self.mc = None
        self.VideoReceiver = None
        self.controller.set_model(self)
        self.status = self.controller.view.resultbox
        try:
            self.start_client()
        except:
            tk.messagebox.showinfo(title="Error", message="Could not connect to robot!")
            self.status.set(self.status.get() + " FAILURE")



    @update_coords
    def release_servos(self):
        self.mc.clear_error_information()
        if self.mc.release_all_servos():
            return 0
        else:
            return -1

    def lock_servos(self):
      #  val = self.mc.focus_all_servos()
        return self.mc.focus_all_servos()

    @update_coords
    def calibrate_servos(self):

        for i in range(1,7):
            self.mc.focus_servo(i)
            time.sleep(1)
            self.mc.set_servo_calibration(i)

            time.sleep(1)
            print("After calibration...:")
            print(self.mc.get_angles())

    def reset_all_servos(self):
        self.mc.send_angles([0, 0, 0, 0, 0, 0], 60)
        print(self.mc.get_error_information())

    def get_angles(self):
        return self.mc.get_angles()

    def send_single_movement(self, joint, angle):
        if self.check_limits(joint, angle):
            self.status.set(self.status.get() + "\njoint" + str(joint)+ " was sent an illegal angle!\n")
            print(f"joint {joint} cannot be sent an angle of {angle}")
            return
        self.mc.send_angle(joint,angle, 99)
        print(self.mc.get_error_information())

    def send_movement_concurrently(self, angleList):
        i = 1
        for angle in angleList:
            if self.check_limits(i,angle):
                self.status.set(self.status.get() + "\n" + str("joint: " + str(i))+ f" was sent an illegal angle of {angle}!\n")
                return
            else:
                i += 1
        self.mc.send_angles(angleList, 60)
        print(self.mc.get_error_information())


    def check_limits(self, joint, angle):

        min_angle = self.mc.get_joint_min_angle(joint)
        max_angle = self.mc.get_joint_max_angle(joint)
        print(
            f"angle: {angle} min ang: {min_angle} + max angle: {max_angle}")
        if float(angle) < min_angle:
            return 1
        elif float(angle) > max_angle:
            return 1
        else:
            return 0

    def cleanup(self):
        self.mc.clear_error_information()

    def start_client(self): #cannot use decorator here as mc not defined yet
        self.status.set(self.status.get() + "Connecting to robot .......")
        self.mc = MyCobot280Socket("192.168.1.157", 9000)
        self.status.set(self.status.get() + "Successful.")


    def set_color(self, colorStr):
        rgb_tup = ImageColor.getrgb(colorStr)

        self.mc.set_color(rgb_tup[0], rgb_tup[1], rgb_tup[2])
        pass

    def show_camera_feed(self):
        self.VideoReceiver = VideoReceiver('192.168.1.157', 25666)

        try:
            self.VideoReceiver.start()

            while self.VideoReceiver.running:
                print("video client in receiving")
                time.sleep(1)

        except Exception as e:
            print("exception starting vid recvr: " + str(e))
        finally:
            self.VideoReceiver.stop()

    def reset_joint_minimum(self, joint_id, angle):
        self.mc.set_joint_min(joint_id,angle)

    def reset_joint_maximum(self, joint_id, angle):
        self.mc.set_joint_max(joint_id,angle)
