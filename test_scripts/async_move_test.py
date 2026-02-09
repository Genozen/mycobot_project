from pymycobot.mycobot280 import MyCobot280
from pymycobot import PI_PORT, PI_BAUD # When using the Raspberry Pi version of mycobot, you can reference these two variables to initialize MyCobot
import time
from pynput import keyboard
import threading

# Initialize a MyCobot280 object
mc = MyCobot280(PI_PORT, PI_BAUD)
# MyCobot280 class initialization requires two parameters: serial and buad rate

if mc.get_fresh_mode() != 1:
  mc.set_fresh_mode(1)

# Track which keys are pressed
keys_pressed = set()

def on_press(key):
    try:
        keys_pressed.add(key.char)
    except AttributeError:
        pass

def on_release(key):
    try:
        keys_pressed.discard(key.char)
        if key.char == 'x':
            return False  # Stop listener
    except AttributeError:
        pass

def test_jog_move_with_pynput():
    """Non-blocking keyboard control using pynput"""
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    
    INCREMENT = 20
    SPEED = 50
    
    print("\n=== Keyboard Control (pynput) ===")
    print("Hold keys for continuous movement")
    print("Press 'x' to exit\n")
    
    while True:
        if 'q' in keys_pressed:
            mc.jog_increment_angle(1, -INCREMENT, SPEED, _async=True)
        if 'w' in keys_pressed:
            mc.jog_increment_angle(1, INCREMENT, SPEED, _async=True)
        # ... add other joints
        if 'x' in keys_pressed:
            break
        
        time.sleep(0.001)

if __name__ == "__main__":
    test_jog_move_with_pynput()