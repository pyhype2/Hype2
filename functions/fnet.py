from app import *
import ipaddress
from xml.dom import minidom


def ip_fom_mac(vm_name,net_mac):
    dom=conn.lookupByName(vm_name)
    mac_ip=[]
    try:
       ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT)
    except:
       ifaces = None
       result="---.---.---.---"

    if ifaces is None:
        result="---.---.---.---"
    else:
      for (name, val) in ifaces.items():
        if val['addrs']:
            for addr in val['addrs']:
              if addr['addr']:
                mac_ip.append([val['hwaddr'],addr['addr']])
              break
        else:
            result = "---.---.---.---"
    for int in mac_ip:
       if int[0] == net_mac:
          result=int[1]
       else:
          result = "---.---.---.---"
    return result


def diff_net(min_dhcp,max_dhcp):
    ip1 = ipaddress.IPv4Address(min_dhcp)
    ip2 = ipaddress.IPv4Address(max_dhcp)
    nb_ip = int(ip2) - int(ip1) + 1
    return nb_ip

def get_int(net_name):
  network = conn.networkLookupByName(net_name)
  net_int = network.bridgeName()
  return net_int

def create_vswitch_int(net_int):
  cmd="ovs-vsctl add-br "+net_int
  out = subprocess.call(cmd, shell=True)
  if out != 0:
      raise Exception("Error on creating interface")


def delete_network(net_name,net_int):
   cmd = "ovs-vsctl del-br "+net_int
   out = subprocess.call(cmd, shell=True)
   if out != 0:
      raise Exception("Error deleting interface")
   network = conn.networkLookupByName(net_name)
   network.destroy()
   network.undefine()
   cmd2="kill $(cat /run/dhypecp_"+net_int+".pid)"
   out2 = subprocess.call(cmd2, shell=True)
   if out2 != 0:
      raise Exception("Error on killing DHCP process")
   cmd3="rm -f /run/dhypecp_"+net_int+".pid"
   out3 = subprocess.call(cmd3, shell=True)
   if out3 != 0:
      raise Exception("Error on Deleting DHCP process")


def create_network(net_name,net_int):
    create_vswitch_int(net_int)
    xml = f"""
     <network>
       <name>{ net_name }</name>
       <forward mode='bridge'/>
       <bridge name='{ net_int }'/>
       <virtualport type='openvswitch'/>
     </network>
    """
    conn.networkDefineXML(xml)
    net_use = conn.networkLookupByName(net_name)
    net_use.create()
    net_use.setAutostart(True)

def get_mac_net(vm_name,net_name):
  dom = conn.lookupByName(vm_name)
  raw_xml = dom.XMLDesc()
  net_xml = minidom.parseString(raw_xml)
  VM_mac = []
  for device in net_xml.getElementsByTagName('devices'):
    ifaces = device.getElementsByTagName('interface')
    for iface in ifaces:
       sources = iface.getElementsByTagName('source')
       for source in sources:
         if source.getAttribute('network') == net_name:
            mac = iface.getElementsByTagName('mac')
            target = iface.getElementsByTagName('target')
            ip = ip_fom_mac(vm_name,str(mac[0].getAttribute('address')))
            VM_mac.append([target[0].getAttribute('dev'),mac[0].getAttribute('address'),ip])
  return VM_mac

def get_virt_int():
  net_na = []
  out=[]
  for network in conn.listAllNetworks():
    if network.isActive():
        int_name=[]
        int_mac = conn.interfaceLookupByName(network.bridgeName())
        int_name.append([network.name(),network.bridgeName(),int_mac.MACString()])
        net_detail = conn.networkLookupByName(network.name())
        net_vms = net_detail.listAllPorts()
        vm_name=[]
        for vm in net_vms:
          net_VM_info = []
          raw_xml = vm.XMLDesc()
          net_xml = minidom.parseString(raw_xml)
          net_element = net_xml.documentElement
          net_VM = net_element.getElementsByTagName("name")[0]
          net_VM_info = [net_VM.firstChild.data,get_mac_net(net_VM.firstChild.data,network.name())]
          if net_VM_info not in vm_name:
            vm_name.append(net_VM_info)
        out.append([int_name,vm_name])
    else:
        net_na.append(network.name())
  return out, net_na
