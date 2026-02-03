# https://docs.elephantrobotics.com/docs/mycobot_280_pi_en/3-FunctionsAndApplications/6.developmentGuide/python/4_coord.html
from pymycobot.mycobot280 import MyCobot280
from pymycobot import PI_PORT, PI_BAUD # When using the Raspberry Pi version of mycobot, you can reference these two variables to initialize MyCobot
import time

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
CAM_POSE = [-8.5, -78.2, 411.1, -88.32, 44.59, -128.81]

def test_home_move():
  # mc.send_coords([51.9, -63.2, 410.0, -90.87, -0.69, -88.4], SPEED, MODE)
  mc.go_home()

def test_linear_move():
  # Starting position
  OFFSET = 50
  mc.send_coords([170.5, -58.3, 182.7, 180, -5, -45], SPEED, MODE)
  print(mc.get_coords())
  time.sleep(SLEEP_TIME)

  # test X axis
  mc.send_coords([170.5 + OFFSET, -58.3, 182.7, 180, -5, -45], SPEED, MODE)
  time.sleep(SLEEP_TIME)
  print(mc.get_coords())

  mc.send_coords([170.5 - OFFSET, -58.3, 182.7, 180, -5, -45], SPEED, MODE)
  time.sleep(SLEEP_TIME)
  print(mc.get_coords())

  # test Y axis
  mc.send_coords([170.5, -58.3 + OFFSET, 182.7, 180, -5, -45], SPEED, MODE)
  time.sleep(SLEEP_TIME)
  print(mc.get_coords())

  mc.send_coords([170.5, -58.3 - OFFSET, 182.7, 180, -5, -45], SPEED, MODE)
  time.sleep(SLEEP_TIME)
  print(mc.get_coords())

  # test Z axis
  mc.send_coords([170.5, -58.3, 182.7 + OFFSET, 180, -5, -45], SPEED, MODE)
  time.sleep(SLEEP_TIME)
  print(mc.get_coords())

  mc.send_coords([170.5, -58.3, 182.7 - OFFSET, 180, -5, -45], SPEED, MODE)
  time.sleep(SLEEP_TIME)
  print(mc.get_coords())

def test_rotation_move():
  DEG_OFFSET = 45
  mc.send_coords(CAM_POSE, SPEED, MODE)

  for i in range(0,180, 5):
    mc.send_coords([-8.5, -78.2, 411.1, -88.32, 44.59, -128.81 + i], SPEED, MODE)
    print(mc.get_coords())

  # print("---")
  # for i in range(1,18):
  #   mc.send_coords([-8.5, -78.2, 411.1, (-i*10 + -88.32), 44.59, -128.81], SPEED, MODE)
  #   print(mc.get_coords())

  # mc.send_coords([170.5, -58.3, 182.7, 0, 0, 0], SPEED, MODE)
  # time.sleep(SLEEP_TIME)
  # print(mc.get_coords())

  # mc.send_coords([170.5, -58.3, 182.7, 0, 0, 0], SPEED, MODE)
  # time.sleep(SLEEP_TIME)
  # print(mc.get_coords())  


  # mc.send_coords([170.5, -58.3, 182.7, 0 + DEG_OFFSET, -5, -45], SPEED, MODE)
  # time.sleep(SLEEP_TIME)
  # print(mc.get_coords())

  # mc.send_coords([170.5, -58.3, 182.7, 0 - DEG_OFFSET, -5, -45], SPEED, MODE)
  # time.sleep(SLEEP_TIME)
  # print(mc.get_coords())

  # mc.send_coords([170.5, -58.3, 182.7, 180, -5 + DEG_OFFSET, -45], SPEED, MODE)
  # time.sleep(SLEEP_TIME)
  # print(mc.get_coords())

  # mc.send_coords([170.5, -58.3, 182.7, 180, -5 - DEG_OFFSET, -45], SPEED, MODE)
  # time.sleep(SLEEP_TIME)
  # print(mc.get_coords())

  # mc.send_coords([170.5, -58.3, 182.7, 180, -5, -45], SPEED, MODE)
  # time.sleep(SLEEP_TIME)
  # print(mc.get_coords())

def test_joint_angles_move():
  for i in range(-168, 168, 10):
    mc.send_angle(1, i, 50)

def test_free_drive():
  mc.release_all_servos()

  for i in range(1, 100):
    time.sleep(0.1)
    print(f"free driving timer: {i}/100")

  mc.focus_all_servos()
  print(mc.get_coords())

def test_jog_move():
  while True:
    mc.jog_increment_angle(joint_id=1, increment=-10, speed=100, _async=True)

if __name__ == "__main__":

  # mc.send_coords(CAM_POSE, SPEED, MODE)
  print(mc.get_coords())
  print(mc.get_angles())
  # test_home_move()
  # test_linear_move()
  # test_rotation_move()
  # test_free_drive()
  # test_joint_angles_move()
  # test_jog_move()