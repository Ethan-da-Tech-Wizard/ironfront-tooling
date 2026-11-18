# Program: ironfront-tooling - playtest_input.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Creates a virtual Linux keyboard/mouse (uinput) and replays key presses, mouse moves and waits given on the command line, so an Unreal playtest window can be driven automatically.
"""Send short test inputs to the focused Unreal playtest through Linux uinput."""

# ===== Imports =====
# sys gives us the command-line arguments, time lets us pause between inputs,
# subprocess and json are imported here but are not used anywhere below.
import sys,time,subprocess,json
# evdev lets Python create a fake input device on Linux; "ecodes as e" holds the key/button/axis numbers.
from evdev import UInput,ecodes as e

# ===== Which inputs the virtual device can send =====
# The device must announce every key it may press before it is created.
# This list is the keyboard keys and mouse buttons the playtest uses
# (Enter, Esc, WASD, number keys 1-4, G, R, E, Q, Tab, Shift, Space, C, left/right mouse buttons).
keys=[e.KEY_ENTER,e.KEY_ESC,e.KEY_W,e.KEY_A,e.KEY_S,e.KEY_D,e.KEY_1,e.KEY_2,e.KEY_3,e.KEY_4,e.KEY_G,e.KEY_R,e.KEY_E,e.KEY_Q,e.KEY_TAB,e.KEY_LEFTSHIFT,e.KEY_SPACE,e.KEY_C,e.BTN_LEFT,e.BTN_RIGHT]
# Create the virtual device. It declares the keys above plus relative mouse movement
# (X, Y and scroll wheel). "with" makes sure the device is closed when the script ends.
with UInput({e.EV_KEY:keys,e.EV_REL:[e.REL_X,e.REL_Y,e.REL_WHEEL]},name='IronFront playtest input') as device:
 # Give the operating system a moment to notice the new device before sending anything.
 time.sleep(1)
 # Each command-line argument (after the script name) is one action, handled in order.
 for arg in sys.argv[1:]:
  # "wait:N" means just pause for N seconds, then go on to the next argument.
  if arg.startswith('wait:'): time.sleep(float(arg.split(':')[1])); continue
  # "move:X,Y" moves the mouse by X and Y pixels (relative to where it is now).
  if arg.startswith('move:'):
   # Split "move:10,-5" into the two whole numbers x and y.
   x,y=map(int,arg.split(':')[1].split(',')); device.write(e.EV_REL,e.REL_X,x); device.write(e.EV_REL,e.REL_Y,y); device.syn(); time.sleep(.2); continue
  # Anything else is "KEY" or "KEY:seconds". If no duration is given, '.12' seconds is used.
  # "left"/"right" are mouse buttons (BTN_*); every other name is a keyboard key (KEY_*).
  key,duration=(arg.split(':')+[ '.12'])[:2]; code=getattr(e,'BTN_'+key.upper()) if key.lower() in ('left','right') else getattr(e,'KEY_'+key.upper())
  # Press the key (value 1), flush with syn(), hold it for the duration,
  # release it (value 0), flush again, then pause briefly before the next action.
  device.write(e.EV_KEY,code,1); device.syn(); time.sleep(float(duration)); device.write(e.EV_KEY,code,0); device.syn(); time.sleep(.25)
