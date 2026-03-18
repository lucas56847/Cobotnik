import tkinter as tk
import threading
from tkinter import ttk, Message
from tkinter import messagebox
import os
import time
from helpers import *
from PIL import Image, ImageTk
from tkinter import filedialog as fd
from models import *


import views
from server.client import VideoReceiver
from views import *

class Controller:
    def __init__(self,view):
        self.view = view
        self.view.set_controller(self)
        self.model = None
        self.setting_color_currently = False
        self.movement_lock = False
        self.camera_lock = False
        self.receiver = None
        self.cam_window  = None


    def calibration_click(self):
        tk.messagebox.showinfo(title=None, message="Move all joints to 'zero' position and press Okay")


        self.model.calibrate_servos()
        self.view.resultbox.set("Calibrated.")

    def patrol_click(self):
        self.model.reset_joint_minimum(1,-90)
        self.model.reset_joint_maximum(1, 160)
        pass

    def update_status(self, status):
        self.view.resultbox.set(self.view.resultbox.get() + status)
        return

    def _set_color_background(self, color, entry_box):
        self.model.set_color(color)
        self.update_status("Success")

    def _release_servos_threaded(self):
        self.update_status("\nReleasing Servos.....")
        if self.model.release_servos():
            self.update_status("Failure")
        else:
            self.update_status("Success")

        self.movement_lock = False

    def release_servos_click(self):
        if self.movement_lock:
            return
        try:
            self.movement_lock = True
            thread = threading.Thread(target=self._release_servos_threaded, args=())
            thread.start()
        except:
            self.update_status("Failure")

    def lock_all_servos(self):
        if self.movement_lock:
            return

        try:
            self.movement_lock = True
            thread = threading.Thread(target=self._lock_servos_thread, args=())
            thread.start()
        except Exception as e:
            self.update_status("Failed")
            print(str(e))

    def _lock_servos_thread(self):
        self.update_status("\nLocking all servos.... ")
        try:
            if abs(self.model.lock_servos()) == 1:
                self.update_status("Locked!")

            else:
                self.update_status("Failure.")
        finally:
            self.movement_lock = False

    def reset_movement(self):
        if self.movement_lock:
            return
        self.movement_lock = True
        self.update_status("\nResetting joints back to origin...")
        thread = threading.Thread(target=self.reset_movement_threaded, args=())
        try:
            thread.start()
        except Exception as e:
            self.update_status("Failure")
            self.update_status(str(e))

    def reset_movement_sequential(self):
        if self.movement_lock:
            return
        self.movement_lock = True
        self.update_status("\nResetting joints back to origin sequentially...")
        thread = threading.Thread(target=self.reset_movement_sequential_threaded, args=())
        try:
            thread.start()
        except Exception as e:
            self.update_status("Failure\n")
            self.update_status(str(e))

    def reset_movement_sequential_threaded(self):
        try:
            for i in range(1,7):
                self.model.send_single_movement(i, 0)
                if i == 6:
                    self.view.after(0, lambda: self.update_status("Success"))
        finally:
            self.movement_lock = False

    def reset_movement_threaded(self):
        try:
            self.model.reset_all_servos()
            self.view.after(0, lambda: self.update_status("Success"))
        finally:
            self.movement_lock = False

    def send_angle_sequential(self, angleList):
        if self.movement_lock:
            return

        self.movement_lock = True
        self.update_status("\nSending angles to joints sequentially...")
        thread = threading.Thread(target=self.send_angle_thread_seq, args=(angleList,))
        try:
            thread.start()
        except Exception as e:
            self.update_status("Failure\n")
            self.update_status(str(e))

    def send_angle_concurrent(self, angleList):
        if self.movement_lock:
            return

        self.movement_lock = True
        self.update_status("\nSending angles to joints concurrently...")
        thread = threading.Thread(target=self.send_angle_thread_concurr, args=(angleList,))
        try:
            thread.start()
        except Exception as e:
            self.update_status("Failure\n")
            self.update_status(str(e))

    def send_angle_thread_seq(self,  angleList):
        try:
            for i in range(0,6):
                self.model.send_single_movement(i+1, angleList[i])
                if i == 5:
                    self.view.after(0, lambda: self.update_status("Success"))
        finally:
            self.movement_lock = False
            self.model.cleanup()

    def send_angle_thread_concurr(self,  angleList):
        try:
            self.model.send_movement_concurrently(angleList)
            self.view.after(0, lambda: self.update_status("Success"))
        finally:
            self.movement_lock = False
            self.model.cleanup()

    def set_led_color(self, entry_box):
        if self.setting_color_currently:
            return
        try:
            self.setting_color_currently = True
            self.update_status("\nSetting Color....")
            color = entry_box.get()

            if len(color) > 0:
                thread = threading.Thread(target=self._set_color_background, args=(color, entry_box))
                thread.start()
                entry_box.config(bg="green")
            else:
                self.update_status("Failure")
        except Exception:
            entry_box.config(bg="red")
            self.update_status("Failure")
        finally:
            self.setting_color_currently = False

    def send_angle_from_user(self, args):
        #-160 to pos camera upright

        angle_str = args[0].get()
        angle_txt,angle_arr = UniversalHelpers.get_ints_from_str(angle_str)
        status = f"\nQueued up {angle_txt} to send to robot..."
        self.retarded_status_update_threaded(status)
        if args[1] == True: #if concurrent
            #thread = threading.Thread(target=self.send_angleList_thread(angle_arr), args=(angle_arr,))
            self.send_angle_concurrent(angle_arr)
        else:
            #thread = threading.Thread(target=self.send_angle_sequential, args=(angle_arr,))
            self.send_angle_sequential(angle_arr)


    def display_camera_feed(self):
        if self.camera_lock:
            return

        self.camera_lock = True
        self.update_status("\nInitializing camera feed...")

        #thread = threading.Thread(target=self.camera_thread, daemon=True)

        try:

            self.camera_thread()
        except Exception as e:
            self.update_status("Failed.")
            print(str(e))
        finally:
            self.camera_lock = False


    def camera_thread(self):
        if self.cam_window != None and self.cam_window.winfo_exists():
            self.cam_window.lift()
            return
        self.cam_window = tk.Toplevel(self.view)
        self.cam_window.geometry("720x480")
        video_frame = ttk.LabelFrame(self.cam_window, text="Video Stream", padding="10")
        video_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # Video label with black background
        self.video_label = tk.Label(self.cam_window, bg='black', relief=tk.SUNKEN, borderwidth=2)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        if self.receiver == None:
            self.receiver = VideoReceiver('192.168.1.157', 25666)
            try:
                self.receiver.start()
                self.update_frame()
                #self.model.show_camera_feed()
                #self.camera_lock = False
            except Exception as e:
                print("exception inside camera feed: " + str(e))
            finally:
                print("All clean!")
        else:
            self.update_frame()

    def update_frame(self):
        if self.receiver.is_running():
            frame = self.receiver.get_frame()

            if frame is not None:
                try:
                    pil_image = Image.fromarray(frame)
                    pil_image = pil_image.resize((720, 480), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(pil_image)
                    self.video_label.config(image=photo)
                    self.video_label.image = photo
                except Exception as e:
                    print(str(e))
                    return

            self.view.after(30, self.update_frame)

    def set_model(self, model):
        self.model = model

    def set_callbacks(self,button,cmd):
        button.config(command=cmd)

    def retarded_status_update_threaded(self,status):
        self.update_status(status)

    def move_joint_pos20(self, joint_box):
        if self.movement_lock:
            return
        try:
            joint = joint_box.get()

            if len(joint) > 0 and 7 > int(joint) > 0:
                current_angles = self.model.get_angles()

                self.update_status("\nMoving joint by 20 deg...")
                self.movement_lock = True
                self.model.send_single_movement(int(joint), current_angles[int(joint)-1]+20)
                #thread = threading.Thread(target=self._set_color_background, args=(color, entry_box))
                #thread.start()
                joint_box.config(bg="green")
            else:
                joint_box.config(bg="red")
        except Exception:
            joint_box.config(bg="red")
            self.update_status("Failure")
        finally:
            self.movement_lock = False

    def move_joint_neg20(self, joint_box):
        if self.movement_lock:
            return
        try:
            joint = joint_box.get()

            if len(joint) > 0 and 7 > int(joint) > 0:
                current_angles = self.model.get_angles()

                if (int(joint) == 1 and (current_angles[0] - 20) < -85 ):
                    raise Exception("Weird case where this angle is illegal, but robot doesn't detect it.")
                self.update_status("\nMoving joint by 20 deg...")
                self.movement_lock = True
                self.model.send_single_movement(int(joint), current_angles[int(joint)-1]-20)
                #thread = threading.Thread(target=self._set_color_background, args=(color, entry_box))
                #thread.start()
                joint_box.config(bg="green")
            else:
                joint_box.config(bg="red")
        except Exception as e:
            joint_box.config(bg="red")
            self.update_status("Failure\n")
            print(str(e))
        finally:
            self.movement_lock = False

    def complex_move(self):
        filetypes = (
            ('text files', '*.txt'),
        )

        # Show the "Open" dialog and get the file path
        filepath = fd.askopenfilename(
            title='Choose a file',
            initialdir=os.getcwd(),  # Sets the initial directory to the current working directory
            filetypes=filetypes
        )

        if filepath:
            with open(filepath, 'r') as file:
                content = file.read()
                arrays = content.splitlines()
                delay = 1000
                for array in arrays:
                    angle_txt, angle_arr = UniversalHelpers.get_ints_from_str(array)

                    self.send_angle_concurrent_with_delay(angle_arr,3)
                    #delay *= 5
                    self.movement_lock = False
                   # self.view.after(delay, self.send_angle_concurrent, angle_arr)
    def send_angle_concurrent_with_delay(self, angleList,delay):
        if self.movement_lock:
            return
        time.sleep(delay)
        self.movement_lock = True
        self.update_status("\nSending angles to joints concurrently...")
        thread = threading.Thread(target=self.send_angle_thread_concurr, args=(angleList,))
        try:
            thread.start()
        except Exception as e:
            self.update_status("Failure\n")
            self.update_status(str(e))




