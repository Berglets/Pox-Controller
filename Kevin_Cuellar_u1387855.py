# Import some POX stuff
from pox.core import core                     # Main POX object
import pox.openflow.libopenflow_01 as of      # OpenFlow 1.0 library
import pox.lib.packet as pkt                  # Packet parsing/construction
from pox.lib.addresses import EthAddr, IPAddr # Address types
import pox.lib.util as poxutil                # Various util functions
import pox.lib.revent as revent               # Event library
import pox.lib.recoco as recoco               # Multitasking library
from pox.lib.packet.arp import arp            # ARP 
from pox.lib.packet.ethernet import ethernet  # Ethernet

# Create a logger for this component
log = core.getLogger()

# Connection object for s1
connection = None

# Globals
h5_is_next_server = True
mac_h5 = EthAddr("00:00:00:00:00:05")
mac_h6 = EthAddr("00:00:00:00:00:06")
ip_h5 = IPAddr("10.0.0.5")
ip_h6 = IPAddr("10.0.0.6")

# Called by POX in command line
@poxutil.eval_args
def launch ():
  core.registerNew(ArpComponent)
  
  
class ArpComponent (object):
  def __init__ (self):
    core.openflow.addListeners(self)  # automatically subscribe to events

  # Called when swiches get recognized
  def _handle_ConnectionUp (self, event):
    log.debug("The switch has come up: " + str(event.connection.dpid))
    global connection 
    connection = event.connection

  # inport = port the packet came into switch
  # a = arp request packet
  def client_to_server(inport, a):
    global connection
    global h5_is_next_server
    global mac_h5
    global mac_h6
    global ip_h5
    global ip_h6
    
    # Assign correct server host (round robin)
    outport = None # relative to s1; outport to 10.0.0.10 for this host
    dst_real_addr = None
    dst_mac_addr = None
    
    if h5_is_next_server:
      dst_mac_addr = mac_h5
      h5_is_next_server = False
      outport = 5
      dst_real_addr = IPAddr("10.0.0.5")
    else:
      dst_mac_addr = mac_h6
      h5_is_next_server = True
      outport = 6
      dst_real_addr = IPAddr("10.0.0.6")
    
    # Push rules for client to server
    msg = of.ofp_flow_mod()
    msg.match.dl_type = 0x800
    msg.match.nw_dst = IPAddr("10.0.0.10")
    msg.match.in_port = inport
    msg.actions.append(of.ofp_action_nw_addr.set_dst(dst_real_addr))
    msg.actions.append(of.ofp_action_output(port = outport))
    connection.send(msg)
    
    # Push rules for server to client
    msg = of.ofp_flow_mod()
    msg.match.dl_type = 0x800
    msg.match.nw_dst = a.protosrc
    msg.match.nw_src = dst_real_addr
    msg.match.in_port = outport
    msg.actions.append(of.ofp_action_nw_addr.set_src(IPAddr("10.0.0.10"))) # remove if no worky should allow server to ping directly
    msg.actions.append(of.ofp_action_output(port = inport))
    connection.send(msg)
    
    # Create arp reply
    r = arp()
    r.opcode = arp.REPLY
    r.protodst = a.protosrc
    r.protosrc = a.protodst
    r.hwdst = a.hwsrc 
    r.hwsrc = dst_mac_addr
    
    ether = ethernet()
    ether.type = ethernet.ARP_TYPE
    ether.dst = a.hwsrc
    ether.src = r.hwsrc
    ether.set_payload(r)
    
    # Send arp reply to host who wants mac  
    msg = of.ofp_packet_out()
    msg.data = ether.pack()
    msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
    msg.in_port = inport
    connection.send(msg)

  # inport = port the packet came into switch
  # a = arp request packet
  def server_to_client(inport, a):
    global connection
    
    # Create reply
    r = arp()
    r.opcode = arp.REPLY
    r.protodst = a.protosrc
    r.protosrc = a.protodst
    r.hwdst = a.hwsrc 
    
    # Choose correct mac based on host  
    if str(a.protodst) == '10.0.0.1':
      r.hwsrc = EthAddr("00:00:00:00:00:01")
    elif str(a.protodst) == '10.0.0.2':
      r.hwsrc = EthAddr("00:00:00:00:00:02")  
    elif str(a.protodst) == '10.0.0.3':
      r.hwsrc = EthAddr("00:00:00:00:00:03")  
    elif str(a.protodst) == '10.0.0.4':
      r.hwsrc = EthAddr("00:00:00:00:00:04")  
    else: 
      return

    ether = ethernet()
    ether.type = ethernet.ARP_TYPE
    ether.dst = a.hwsrc
    ether.src = r.hwsrc
    ether.set_payload(r)
    
    # send message to server who wants mac  
    msg = of.ofp_packet_out()
    msg.data = ether.pack()
    msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
    msg.in_port = inport
    connection.send(msg)

  # ARP requests
  def _handle_PacketIn (self, event):
    inport = event.port
    packet = event.parsed
    
    if not packet.parsed:
      log.warning("Ignoring unparsed packet")
      return
  
    log.debug("Got packet: " + str(packet))

    # return if not an arp request
    if packet.type != packet.ARP_TYPE: 
      return
    if packet.payload.opcode != arp.REQUEST: 
      return
  
    a = packet.find('arp')
    
    log.debug("%s ARP %s %s => %s", 1,
      {arp.REQUEST:"request",arp.REPLY:"reply"}.get(a.opcode,
      'op:%i' % (a.opcode,)), str(a.protosrc), str(a.protodst))
      
    if(str(a.protodst) == "10.0.0.10"):
      client_to_server(inport, a)
    else: # server wants to know client mac
      server_to_client(inport, a)
    
    
