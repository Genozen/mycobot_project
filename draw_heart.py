# https://docs.elephantrobotics.com/docs/mycobot_280_pi_en/3-FunctionsAndApplications/6.developmentGuide/python/4_coord.html
from pymycobot.mycobot280 import MyCobot280
from pymycobot import PI_PORT, PI_BAUD # When using the Raspberry Pi version of mycobot, you can reference these two variables to initialize MyCobot
import time
import numpy as np

"""
+x = foward
+y = left
+z = up
+rx = roll counterclockwise (-180, 180)
+ry = pitch 
+rz = yaw counterclockwise


x 	-281.45 ~ 281.45
y 	-281.45 ~ 281.45
z 	-70 ~ 412.67
rx 	-180 ~ 180
ry 	-180 ~ 180
rz 	-180 ~ 180


joint id
1 	-168 ~ 168
2 	-140 ~ 140
3 	-150 ~ 150
4 	-150 ~ 150
5 	-155 ~ 160
6 	-180 ~ 180
"""

# Initialize a MyCobot280 object
mc = MyCobot280(PI_PORT, PI_BAUD)
# MyCobot280 class initialization requires two parameters: serial and buad rate

if mc.get_fresh_mode() != 1:
  mc.set_fresh_mode(1)


# # Intelligently plan the route, so that the head reaches the coordinates [57.0, -107.4, 316.3] in a linear manner, and maintains the posture [-93.81, -12.71, -163.49], with a speed of 80mm/s

SPEED = 90 # 1 ~100
MODE = 1
SLEEP_TIME = 0.05
CAM_POSE = [194.6, -1.2, 65.8, -177.57, -1.12, -36.83]


i = np.arange(0, 2*np.pi, 0.02)
scale_factor_x = 1.5
scale_factor_y = 2.5
x = 16*np.sin(i)**3 * scale_factor_x
y = (13*np.cos(i) - 5*np.cos(2*i) - 2*np.cos(3*i) - np.cos(4*i))* scale_factor_y

def test_home_move():
  mc.go_home()

def start_pose():
    mc.send_coords(CAM_POSE, SPEED, MODE)

def draw_heart():
    for i in range(len(x)):
        print(f"Drawing heart: {i} | Pos: {CAM_POSE[0] + x[i]}, {CAM_POSE[1] + y[i]}")
        mc.send_coords([CAM_POSE[0] + x[i], CAM_POSE[1] + y[i], 66.4, -179.78, 0.75, -44.82], SPEED, MODE)
        time.sleep(0.01)

def test_free_drive():
  mc.release_all_servos()

  for i in range(1, 100):
    time.sleep(0.1)
    print(f"free driving timer: {i}/100")

  mc.focus_all_servos()
  print(mc.get_coords())

if __name__ == "__main__":
    # test_free_drive()
    print("Start drawing heart")
    start_pose()
    draw_heart()
    draw_heart()
    print("Heart drawn")