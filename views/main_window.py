import tkinter as tk
from tkinter import ttk
from functools import partial
from PIL import ImageTk, Image
from controllers import *
from helpers import *
from models import *

class MainView(tk.Frame): #changed from ttk.Frame to tk.Frame
    def __init__(self, parent):
        super().__init__(parent)
        self.result_bg_color = "#222222"
        self.controller = None
        self.resultbox = tk.StringVar()
        self.btn_dict_list = []
        self.status_text = None
        self.helpers = Helpers()
        self.btn_dict = {}


    def set_controller(self, controller):
        self.controller = controller

    def create_main_view(self, parent):

        main_panel = tk.Frame(parent, bg="lightblue")
        main_panel.pack(expand=True,fill="both")

        left_col = tk.Frame(main_panel, bg="#222222")
        left_col.pack(side="left",expand=True,fill="both",padx=10,pady=20)

        right_col = tk.Frame(main_panel,bg="#222222")
        right_col.pack(side="right",expand=True,fill="both",padx=10,pady=20)

        self.create_buttons(left_col)
  #      self.create_text_boxes(right_col)
        self.create_scroll_status(right_col)

    def create_scroll_status(self,right_col):
        canvas = tk.Canvas(right_col, width=300, height=300,bg="#222222")
        scrollbar = tk.Scrollbar(right_col, orient="vertical", command=canvas.yview)

        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((50, 0), window=scrollable_frame, anchor="center")
        canvas.configure(yscrollcommand=scrollbar.set)

        tk.Label(scrollable_frame, textvariable=self.resultbox, pady=5, padx=70, fg="#FFFFFF",bg="#222222",
                 anchor="center", wraplength=290).pack(expand=True)

        canvas.pack(side="left", fill="both", expand=True, anchor="center")
        scrollbar.pack(side="right", fill="y")

    def create_buttons(self,frame):
        cal_button = tk.Button(frame, text="Calibrate")
        cal_button.pack(pady="10", padx="10", anchor='w')

        patrol_loop_button = tk.Button(frame, text="Correct Limits",bg="green")
        patrol_loop_button.pack(pady="10",padx="10", anchor='w')

        release_servos_button = tk.Button(frame, text="Release Servos", bg="yellow")
        release_servos_button.pack(pady="10", padx="10", anchor='w')

        dummy_frame = tk.Frame(frame, bg=frame.cget('bg'))
        dummy_frame.pack(anchor='nw')

        change_color_button = tk.Button(dummy_frame, text="Change LED color", bg="lightblue")
        change_color_button.pack(pady="10", padx="10", side=tk.LEFT)

        entry_box = tk.Entry(dummy_frame, width=30)
        entry_box.pack(pady="13", padx="20", side=tk.LEFT)

        reset_movement_button = tk.Button(frame, text="Reset Movement", bg="white")
        reset_movement_button.pack(pady="10", padx="10", anchor='w')

        lock_servos_button = tk.Button(frame, text="Lock Servos", bg="red")
        lock_servos_button.pack(pady="10", padx="10", anchor='w')

        reset_movement_seq_button = tk.Button(frame, text="Reset Movement Sequentially", bg="white")
        reset_movement_seq_button.pack(pady="10", padx="10", anchor='w')

        angle_frame = tk.Frame(frame, bg=frame.cget('bg'))
        angle_frame.pack(anchor='nw')

        send_angle_button = tk.Button(angle_frame, text="Send Angles To Bot", bg="lightblue")
        #send_angle_button.pack(pady="10", padx="10", side=tk.LEFT)

        angle_box = tk.Entry(angle_frame, width=30)
        #angle_box.pack(pady="13", padx="20", side=tk.LEFT)

        send_angle_concurrently_button = tk.Button(angle_frame, text="Send Angles Concurrently", bg="lightblue")
        #send_angle_concurrently_button.pack(pady="10", padx="10", anchor="s", side=tk.BOTTOM)

        send_angle_button.grid(row=0, column=0, pady=10, padx=10)
        angle_box.grid(row=0, column=1, pady=0, padx=20)
        send_angle_concurrently_button.grid(row=1, column=1, pady=1, padx=10)

        view_camera_button = tk.Button(frame, text="View Feed", bg="light green")
        view_camera_button.pack(pady="10", padx="10", anchor='w')

        up_down_frame = tk.Frame(frame, bg=frame.cget('bg'))
        up_down_frame.pack(anchor='nw')

        move_joint_text = tk.Label(up_down_frame,text="Move angle by 20 deg",bg=frame.cget('bg'), padx=0, pady=0,foreground='white')
        joint_box = tk.Entry(up_down_frame, width=3)
        try:
            photo = ImageTk.PhotoImage(Image.open("up_arr_25x25.png"))
            up_arrow_button = tk.Button(up_down_frame, image=photo)
            up_arrow_button.image = photo
           # up_arrow_button.pack(pady="10", padx="10", anchor='w')
        except Exception as e:
            print ("cant load image: " + str(e))

        try:
            down_arr_img = ImageTk.PhotoImage(Image.open("down_arr_25x25.png"))
            down_arrow_button = tk.Button(up_down_frame, image=down_arr_img)
            down_arrow_button.image = down_arr_img
           # down_arrow_button.pack(pady="10", padx="10", anchor='w')
        except Exception as e:
            print ("cant load image: " + str(e))

        joint_box.grid(row=1, column=1, pady=00, padx=00,columnspan=1)
        move_joint_text.grid(row=0, column=0, pady=00, padx=00,columnspan=3)
        up_arrow_button.grid(row=1, column=0, pady=10, padx=10)
        down_arrow_button.grid(row=1, column=2, pady=10, padx=10)
        #send_angle_concurrently_button.grid(row=1, column=1, pady=1, padx=10)

        complex_move_button = tk.Button(frame, text="Complex Movement", bg="blue")
        complex_move_button.pack(pady="10", padx="10", anchor='w')

        self.btn_dict_list.append(self.helpers.create_button_def(cal_button,self.controller.calibration_click, []))
        self.btn_dict_list.append(self.helpers.create_button_def(patrol_loop_button, self.controller.reset_limits, []))
        self.btn_dict_list.append(self.helpers.create_button_def(release_servos_button, self.controller.release_servos_click, []))
        self.btn_dict_list.append(self.helpers.create_button_def(change_color_button, self.controller.set_led_color, entry_box))
        self.btn_dict_list.append(
            self.helpers.create_button_def(reset_movement_button, self.controller.reset_movement,[]))
        self.btn_dict_list.append(
            self.helpers.create_button_def(reset_movement_seq_button, self.controller.reset_movement_sequential, []))
        self.btn_dict_list.append(
            self.helpers.create_button_def(send_angle_button, self.controller.send_angle_from_user, [angle_box, 0]))
        self.btn_dict_list.append(
            self.helpers.create_button_def(send_angle_concurrently_button, self.controller.send_angle_from_user, [angle_box, 1])
        )
        self.btn_dict_list.append(
            self.helpers.create_button_def(view_camera_button, self.controller.display_camera_feed,
                                           [])
        )

        self.btn_dict_list.append(
            self.helpers.create_button_def(up_arrow_button, self.controller.move_joint_pos20, joint_box))
        self.btn_dict_list.append(
            self.helpers.create_button_def(down_arrow_button, self.controller.move_joint_neg20, joint_box))

        self.btn_dict_list.append(
            self.helpers.create_button_def(lock_servos_button, self.controller.lock_all_servos, []))

        self.btn_dict_list.append(
            self.helpers.create_button_def(complex_move_button, self.controller.complex_move, []))


        for item in self.btn_dict_list:
            self.controller.set_callbacks(item["button"], item["command"])


    def create_text_boxes(self,frame):
        self.resultbox.set("Connecting to robot.......")
        status_label = tk.Label(frame,fg="#FFFFFF", text="Status" ,bg="#222222")

        status_label.pack()
        self.status_text = tk.Label(frame, fg="#FFFFFF", textvariable=self.resultbox, bg=self.result_bg_color)

        self.status_text.pack()

    def set_callbacks(self,cal_button, patrol_button): #toyed with the idea of doing this here ....
        #but you have to include the button reference SOMEWHERE so never wound up doing it this way.
        #leaving here in case i find a better way
        pass



