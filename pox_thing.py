
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
from pox.lib.packet.arp import arp            # ARP 
from pox.lib.util import dpid_to_str, str_to_bool


# Create a logger for this component
log = core.getLogger()

# Connection for s1
connection = None
h5_is_next_server = True

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
    log.info("Switch has come up " + str(event.connection.dpid))
    global connection 
    connection = event.connection

  # ARP requests
  def _handle_PacketIn (self, event):
    inport = event.port
    packet = event.parsed
    if not packet.parsed:
      log.warning("Ignoring unparsed packet")
      return
  
    log.debug("Got packet: " + str(packet))

    if packet.type != packet.ARP_TYPE: return
    if packet.payload.opcode != arp.REQUEST: return
    a = packet.find('arp')

    log.debug("%s ARP %s %s => %s", dpid_to_str(dpid),
      {arp.REQUEST:"request",arp.REPLY:"reply"}.get(a.opcode,
      'op:%i' % (a.opcode,)), str(a.protosrc), str(a.protodst))


    
    """
    # One thing at a time...
msg = of.ofp_flow_mod()
msg.priority = 42
msg.match.dl_type = 0x800
msg.match.nw_dst = IPAddr("192.168.101.101")
msg.match.tp_dst = 80
msg.actions.append(of.ofp_action_output(port = 4))
self.connection.send(msg)
    
  """
