"""
+x = forward
+y = left
+z = up
+roll = 
+pitch =
+yaw =
"""


from pymycobot import MyCobot280
from pymycobot import PI_PORT, PI_BAUD # When using the Raspberry Pi version of mycobot, you can reference these two variables to initialize MyCobot
import time

SPEED = 90 # 1 ~100
MODE = 1
OFFSET = 50
SLEEP_TIME = 0.3

mc = MyCobot280(PI_PORT, PI_BAUD)

if mc.get_fresh_mode() != 1:
  mc.set_fresh_mode(1)

# starting pose
mc.send_coords([170.5, -58.3, 182.7, 180, -5, -45], SPEED, MODE)
time.sleep(SLEEP_TIME)

mc.send_coords([170.5 + OFFSET, -58.3, 182.7, 180, -5, -45], SPEED, MODE)
time.sleep(SLEEP_TIME)

mc.set_gripper_state(0, 80)

mc.send_coords([170.5 + OFFSET, -58.3, 182.7 - OFFSET, 180, -5, -45], SPEED, MODE)
time.sleep(SLEEP_TIME)

mc.set_gripper_state(1, 80)


mc.send_coords([170.5 + OFFSET, -58.3, 182.7, 180, -5, -45], SPEED, MODE)
time.sleep(SLEEP_TIME)

mc.send_coords([170.5 + OFFSET, -58.3, 182.7 - OFFSET, 180, -5, -45], SPEED, MODE)
time.sleep(SLEEP_TIME)

mc.set_gripper_state(0, 80)
mc.send_coords([170.5, -58.3, 182.7, 180, -5, -45], SPEED, MODE)
mc.set_gripper_state(1, 80)
