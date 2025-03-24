
"""
A skeleton POX component

Rename this file to whatever you like, .e.g., mycomponent.py.  You can
then invoke it with "./pox.py mycomponent" if you leave it in the
ext/ directory.

Implement a launch() function (as shown below) which accepts commandline
arguments and starts off your component (e.g., by listening to events).

"""

# Import some POX stuff
from pox.core import core                     # Main POX object
import pox.openflow.libopenflow_01 as of      # OpenFlow 1.0 library
import pox.lib.packet as pkt                  # Packet parsing/construction
from pox.lib.addresses import EthAddr, IPAddr # Address types
import pox.lib.util as poxutil                # Various util functions
import pox.lib.revent as revent               # Event library
import pox.lib.recoco as recoco               # Multitasking library

# Create a logger for this component
log = core.getLogger()

# Connection for s1
connection = None

def _go_up (event):
  log.info("Up Event: Skeleton application ready (to do nothing).")

# called by POX in command line
@poxutil.eval_args
def launch ():
  core.addListenerByName("UpEvent", _go_up)
  core.registerNew(MyComponent)
  
class MyComponent (object):
  def __init__ (self):
    core.openflow.addListeners(self)

  def _handle_ConnectionUp (self, event):
    log.debug("Switch has come up " + str(event.connection.dpid))
    global connection 
    connection = event.connection
    
  
