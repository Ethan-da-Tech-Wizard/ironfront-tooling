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

# How this file fits the project
# ------------------------------
# ironfront-tooling holds the helper tooling for the IronFront game project. This is its one script: a
# test driver that plays a game by typing keys and moving the mouse the way a person would, but from a
# command line. Because it feeds the operating system's own input layer (not the game's code), it works
# with any game or window and needs no support from the game, which suits automated, repeatable
# "playtest" runs on a Linux machine. Nothing else in this repository imports it.
#
# Inputs : positional command-line "actions", executed left to right (grammar in run_playtest below).
#          Example: python3 playtest_input.py wait:2 w:1.5 move:40,-10 left enter
# Outputs: none on stdout; the effect is the key and mouse events the game receives.
# Needs  : Linux, the python-evdev package, and permission to open /dev/uinput (typically root or a
#          udev rule that grants the user access). On other systems the script only prints a notice.
# Limits : only the keys listed in `keys` below can be pressed; there are no tests, no error handling for
#          malformed actions (a bad action raises and stops the run, releasing the virtual device), and
#          `subprocess` and `json` are imported but not used.

import sys
import time
import subprocess
import json

# evdev is Linux-only. Importing inside try/except lets the file be syntax-checked and imported on
# macOS/Windows or CI without the package.
try:
    from evdev import UInput, ecodes as e
except ImportError:
    # Fall back to None markers; run_playtest() checks them and explains the problem instead of crashing.
    UInput = None
    e = None

# Hardware key codes registered to the virtual uinput device
# These ecodes define the input capability bitmask advertised to the Linux kernel.
# The kernel creates a virtual character device (/dev/input/eventX) matching these specs.
#
# The list is the game's complete control set: Enter/Esc for menus, WASD for movement, number keys,
# G/R/E/Q/C/Tab/Shift/Space for in-game actions, and the left/right mouse buttons. A key that is not
# registered here cannot be sent later, because the kernel rejects events the device never declared.
# Add a code to this list before using a new key in an action.
if e:
    keys = [
        e.KEY_ENTER, e.KEY_ESC, e.KEY_W, e.KEY_A, e.KEY_S, e.KEY_D,
        e.KEY_1, e.KEY_2, e.KEY_3, e.KEY_4, e.KEY_G, e.KEY_R, e.KEY_E,
        e.KEY_Q, e.KEY_TAB, e.KEY_LEFTSHIFT, e.KEY_SPACE, e.KEY_C,
        e.BTN_LEFT, e.BTN_RIGHT
    ]
else:
    # Without evdev there are no ecodes; an empty list keeps the module importable.
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

    Reads sys.argv[1:] directly (one action per argument). Key names are the suffix of the evdev
    constant, case-insensitive: "w", "space", "leftshift", "tab"; "left" and "right" mean the mouse
    buttons BTN_LEFT / BTN_RIGHT. Durations are seconds (default 0.12 s, a short tap).

    Side effects:
        Creates a virtual input device for the lifetime of the call (it disappears on exit) and sends real
        input to whichever window currently has focus, so only run it with the game in front.

    Raises:
        AttributeError: for an unknown key name (no matching evdev constant).
        ValueError: for a malformed number in a wait:/move:/duration field.
    """
    # Guard for machines without python-evdev: report and return, so the script never half-runs.
    if not UInput or not e:
        print("evdev module required for live hardware input injection (Linux uinput environment).")
        return

    # Initialize the virtual hardware device with keyboard and relative mouse capabilities.
    # The context manager guarantees the device is destroyed on exit, even after an exception, so no
    # stale virtual keyboard stays registered with the kernel.
    with UInput({e.EV_KEY: keys, e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL]}, name='IronFront playtest input') as device:
        # Initial stabilization pause to let game window acquire OS focus. It also gives the desktop time to
        # notice the new device; events sent in the first moments after creation are often dropped.
        time.sleep(1)
        for arg in sys.argv[1:]:
            # Command 1: 'wait:<seconds>' - sleep pause. Used to let animations, loading or movement
            # finish before the next input, which keeps runs repeatable.
            if arg.startswith('wait:'):
                time.sleep(float(arg.split(':')[1]))
                continue

            # Command 2: 'move:<x>,<y>' - relative mouse look/aim movement
            if arg.startswith('move:'):
                # Values are relative mouse "counts" (not pixels); positive x turns right, positive y moves
                # down. Integers only, because the kernel's relative axes take whole numbers.
                x, y = map(int, arg.split(':')[1].split(','))
                device.write(e.EV_REL, e.REL_X, x)
                device.write(e.EV_REL, e.REL_Y, y)

                # One SYN_REPORT after both axes so the game sees a single diagonal movement rather than
                # an X step followed by a Y step. The 0.2 s pause lets the camera settle before the next action.
                device.syn()
                time.sleep(0.2)
                continue

            # Command 3: '<key>[:<duration>]' - key press or mouse button click
            # Padding the split list with the default "0.12" means a bare "w" works as well as "w:2".
            key, duration = (arg.split(':') + ['0.12'])[:2]

            # Translate the friendly name to the evdev constant: mouse buttons are BTN_*, everything else KEY_*.
            code = getattr(e, 'BTN_' + key.upper()) if key.lower() in ('left', 'right') else getattr(e, 'KEY_' + key.upper())
            # Press key down (value 1) and sync hardware event queue. The game must see the key held for
            # `duration` seconds, which is what makes "w:2" walk forward for two seconds.
            device.write(e.EV_KEY, code, 1)
            device.syn()
            time.sleep(float(duration))
            # Release key up (value 0) and sync. Always paired with the press above so no key is left stuck down.
            device.write(e.EV_KEY, code, 0)
            device.syn()

            # Fixed gap between actions: a short debounce so consecutive presses are not merged or dropped
            # by games that poll input once per frame.
            time.sleep(0.25)


# Entry point; the module can still be imported (for example to check `keys`) without sending any input.
if __name__ == "__main__":
    run_playtest()
