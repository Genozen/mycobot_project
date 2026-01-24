from pymycobot import MyCobot280
import time
from pymycobot import __version__
print(__version__)

# Initialize robot arm connection (modify serial port according to actual situation)
#mc = MyCobot320('/dev/ttyAMA0', 115200, debug=False)
mc = MyCobot280('/dev/ttyACM0', 115200, debug=True) #If the return value is -1 or None, open this line of code to run
print(mc.get_basic_version())
print(mc.get_system_version())
print(mc.get_system_version())

mc.set_encoder(7,2048,40)
time.sleep(3)
mc.set_encoder(7,1500,40)
time.sleep(3)
print("gripper_value: ",mc.get_gripper_value(1))

print("Current position before zero-position correction: ", mc.get_encoder(7))
time.sleep(0.1)
mc.set_gripper_calibration()
time.sleep(0.1)
print("Current position after zero-position correction (the gripper will lock when correction is successful, and the position will be close to 100):", mc.get_encoder(7))
time.sleep(0.1)
print("Start updating gripper parameters...")
# datas = [10, 0, 1, 150]
# datas = [25, 25, 0, 140]
# address = [21, 22, 23, 16]
# current_datas = []
# new_datas = []
# for addr in address:
#     current_datas.append(mc.get_servo_data(7, addr))
#     time.sleep(0.1)
# print("The current gripper parameters are:", current_datas)
# for addr in range(len(address)):
#     mc.set_servo_data(7, address[addr], datas[addr])
#     time.sleep(0.1)
# for addr in address:
#     new_datas.append(mc.get_servo_data(7, addr))
#     time.sleep(0.1)
# print("The updated gripper parameters are as follows: ", new_datas)