# ==============================================================================
# Program: playtest_input.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Headless automated gameplay testing input driver for Unreal Engine.
#          Creates a virtual Linux uinput hardware device using python-evdev,
#          translates command-line input script commands (wait, move, key press,
#          mouse buttons) into hardware input events, and synchronizes events
#          with the running game process for repeatable regression testing.
# ==============================================================================

import sys
import time
import subprocess
import json

try:
    from evdev import UInput, ecodes as e
except ImportError:
    # Allows syntax checking and non-Linux test inspection without crashing
    UInput = None
    e = None

# Hardware key codes registered to the virtual uinput device
# These ecodes define the input capability bitmask advertised to the Linux kernel.
# The kernel creates a virtual character device (/dev/input/eventX) matching these specs.
if e:
    keys = [
        e.KEY_ENTER, e.KEY_ESC, e.KEY_W, e.KEY_A, e.KEY_S, e.KEY_D,
        e.KEY_1, e.KEY_2, e.KEY_3, e.KEY_4, e.KEY_G, e.KEY_R, e.KEY_E,
        e.KEY_Q, e.KEY_TAB, e.KEY_LEFTSHIFT, e.KEY_SPACE, e.KEY_C,
        e.BTN_LEFT, e.BTN_RIGHT
    ]
else:
    keys = []

def run_playtest():
    """
    Parses command-line action arguments and delivers hardware inputs to the uinput device.
    
    Architecture & Kernel Invariants:
      1. Virtual Device Initialization:
         Registers an unprivileged user-space input device with EV_KEY (keys/buttons)
         and EV_REL (relative axes: X, Y, WHEEL) capabilities.
      2. Event Synchronization (SYN_REPORT):
         Linux input devices batch changes. Emitting EV_KEY or EV_REL alone does not
         deliver events to consumers until device.syn() generates an EV_SYN packet.
         This guarantees that multi-axis movements or chorded key strokes arrive
         in a single atomic input frame in the game engine loop.
      3. Action Grammar:
         - 'wait:<seconds>'    : Sleep pause between sequential test steps.
         - 'move:<x>,<y>'      : Relative mouse delta injection for aim/camera control.
         - '<key>[:<duration>]': Keydown -> wait -> keyup state cycle with hardware debounce.
    """
    if not UInput or not e:
        print("evdev module required for live hardware input injection (Linux uinput environment).")
        return

    # Initialize the virtual hardware device with keyboard and relative mouse capabilities
    with UInput({e.EV_KEY: keys, e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL]}, name='IronFront playtest input') as device:
        # Initial stabilization pause to let game window acquire OS focus
        time.sleep(1)
        for arg in sys.argv[1:]:
            # Command 1: 'wait:<seconds>' - sleep pause
            if arg.startswith('wait:'):
                time.sleep(float(arg.split(':')[1]))
                continue

            # Command 2: 'move:<x>,<y>' - relative mouse look/aim movement
            if arg.startswith('move:'):
                x, y = map(int, arg.split(':')[1].split(','))
                device.write(e.EV_REL, e.REL_X, x)
                device.write(e.EV_REL, e.REL_Y, y)
                device.syn()
                time.sleep(0.2)
                continue

            # Command 3: '<key>[:<duration>]' - key press or mouse button click
            key, duration = (arg.split(':') + ['0.12'])[:2]
            code = getattr(e, 'BTN_' + key.upper()) if key.lower() in ('left', 'right') else getattr(e, 'KEY_' + key.upper())
            # Press key down (value 1) and sync hardware event queue
            device.write(e.EV_KEY, code, 1)
            device.syn()
            time.sleep(float(duration))
            # Release key up (value 0) and sync
            device.write(e.EV_KEY, code, 0)
            device.syn()
            time.sleep(0.25)

if __name__ == "__main__":
    run_playtest()
