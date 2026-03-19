from functools import partial
import re

class Helpers:
    def create_button_def(self,button,button_cmd, args):
       # print(type(button))
        temp_dict = {}
        temp_dict["button"] = button
        if args:
            temp_dict["command"] = partial(button_cmd, args)
        else:
            temp_dict["command"] = button_cmd

        return temp_dict

class UniversalHelpers:
    @staticmethod
    def get_ints_from_str(usr_input):
        print(usr_input)
        nums = re.findall(r'-?\d+', usr_input)

        nums = [float(n) for n in nums]

        while len(nums) < 6:
            nums.append(0)

        nums = nums[:6]
        angle_arr = nums
        angle_str = "[" + ",".join(map(str, nums)) + ']'

        return angle_str,angle_arr