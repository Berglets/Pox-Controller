
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
import pox.lib.revent.
import pox.lib.recoco as recoco               # Multitasking library
from pox.lib.packet.arp import arp            # ARP 
from pox.lib.util import dpid_to_str, str_to_bool
from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST


# Create a logger for this component
log = core.getLogger()

# Connection for s1
connection = None
h5_is_next_server = True
mac_h5 = "00:00:00:00:00:05"
mac_h6 = "00:00:00:00:00:06"

def _go_up (event):
  log.info("Up Event: Skeleton application ready (to do nothing).")

# called by POX in command line
@poxutil.eval_args
def launch ():
  core.addListenerByName("UpEvent", _go_up)
  core.registerNew(MyComponent)
  
  ip_to_lookup = "10.0.0.1"
  mac_address = get_mac_of_ip(ip_to_lookup)
  if mac_address:
    log.info(f"The MAC address for IP {ip_to_lookup} is {mac_address}")
  else:
    log.info(f"Could not find MAC address for IP {ip_to_lookup}")
  
class MyComponent (object):
  def __init__ (self):
    core.openflow.addListeners(self)

  def _handle_ConnectionUp (self, event):
    log.info("Switch has come up " + str(event.connection.dpid))
    global connection 
    connection = event.connection
    
def get_mac_of_ip(ip_address):
    """Retrieve the MAC address of a host from its IP address using the discovery component."""
    discovery = core.getComponent('discovery')
    # Use the discovery component's 'get_host_mac' method to get the MAC address.
    host_mac = discovery.get_host_mac(IPAddr(ip_address))
    if host_mac:
        return EthAddr(host_mac)
    else:
        log.error("MAC address not found for IP %s", ip_address)
        return None
    

  # ARP requests
  def _handle_PacketIn (self, event):
    global connection
    global h5_is_next_server
    global mac_h5
    global mac_h6
      
    inport = event.port
    packet = event.parsed
    if not packet.parsed:
      log.warning("Ignoring unparsed packet")
      return
  
    log.info("Got packet: " + str(packet))

    if packet.type != packet.ARP_TYPE: return
    if packet.payload.opcode != arp.REQUEST: return
    a = packet.find('arp')

    log.info("%s ARP %s %s => %s", 1,
      {arp.REQUEST:"request",arp.REPLY:"reply"}.get(a.opcode,
      'op:%i' % (a.opcode,)), str(a.protosrc), str(a.protodst))
      
    if(str(a.protodst) != "10.0.0.10"): return
    
    r = arp()
    r.opcode = arp.REPLY
    r.protodst = a.protosrc
    r.protosrc = a.protodst
    r.hwdst = a.hwsrc # where reply is going
    # Give requested mac address (round robin)
    if h5_is_next_server:
        r.hwsrc = mac_h5
        h5_is_next_server = False
    else:
        r.hwsrc = mac_h6
        h5_is_next_server = True
    
    ether = ethernet()
    ether.type = ethernet.ARP_TYPE
    ether.dst = a.hwsrc
    ether.src = r.hwsrc
    ether.set_payload(r)
    
    # send message to host who wants mac  
    msg = of.ofp_packet_out()
    msg.data = ether.pack()
    msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
    msg.in_port = inport
    connection.send(msg)
    

    
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
