"""Send short test inputs to the focused Unreal playtest through Linux uinput."""
import sys,time,subprocess,json
from evdev import UInput,ecodes as e
keys=[e.KEY_ENTER,e.KEY_ESC,e.KEY_W,e.KEY_A,e.KEY_S,e.KEY_D,e.KEY_1,e.KEY_2,e.KEY_3,e.KEY_4,e.KEY_G,e.KEY_R,e.KEY_E,e.KEY_Q,e.KEY_TAB,e.KEY_LEFTSHIFT,e.KEY_SPACE,e.KEY_C,e.BTN_LEFT,e.BTN_RIGHT]
with UInput({e.EV_KEY:keys,e.EV_REL:[e.REL_X,e.REL_Y,e.REL_WHEEL]},name='IronFront playtest input') as device:
 time.sleep(1)
 for arg in sys.argv[1:]:
  if arg.startswith('wait:'): time.sleep(float(arg.split(':')[1])); continue
  if arg.startswith('move:'):
   x,y=map(int,arg.split(':')[1].split(',')); device.write(e.EV_REL,e.REL_X,x); device.write(e.EV_REL,e.REL_Y,y); device.syn(); time.sleep(.2); continue
  key,duration=(arg.split(':')+[ '.12'])[:2]; code=getattr(e,'BTN_'+key.upper()) if key.lower() in ('left','right') else getattr(e,'KEY_'+key.upper())
  device.write(e.EV_KEY,code,1); device.syn(); time.sleep(float(duration)); device.write(e.EV_KEY,code,0); device.syn(); time.sleep(.25)
