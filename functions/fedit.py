from config import *
from functions.fnet import *
import base64
import time
import lxc

def get_version():
  vlxc = lxc.version
  vlibvirt = str(libvirt.getVersion()/1000000) #1000000 * major + 1000 * minor + release
  vhype = hype_version
  return vlxc, vlibvirt, vhype

def get_vm_infos(vm_name):
  dom = conn.lookupByName(vm_name)
  vm_info = dom.guestInfo()
  vm_infos=[]
  vm_infos=[vm_info['os.id'],vm_info['os.pretty-name'],vm_info['os.kernel-release']]
  return vm_infos


def set_memory(vm_name,memory_new):
  dom = conn.lookupByName(vm_name)
  dom.shutdown()
  time.sleep(3)
  alive=0
  while alive < 5:
      if dom.isActive():
          time.sleep(3)
          alive+=1
      else:
          alive=6
  if dom.isActive():
      dom.destroy()
  dom.setMaxMemory(memory_new)
  dom.setMemoryFlags(memory_new)
  dom.create()
  time.sleep(3)
  alive=0
  while alive < 3:
      if dom.isActive():
          alive=4
      else:
          time.sleep(3)
          alive+=1

def set_vcpu(vm_name,vcpu_new):
  dom = conn.lookupByName(vm_name)
  dom.shutdown()
  time.sleep(3)
  alive=0
  while alive < 5:
      if dom.isActive():
          time.sleep(3)
          alive+=1
      else:
          alive=6
  if dom.isActive():
      dom.destroy()
  dom.setVcpusFlags(vcpu_new,libvirt.VIR_DOMAIN_AFFECT_CONFIG | libvirt.VIR_DOMAIN_VCPU_MAXIMUM)
  dom.setVcpusFlags(vcpu_new,libvirt.VIR_DOMAIN_AFFECT_CONFIG | libvirt.VIR_DOMAIN_VCPU_CURRENT)
  dom.create()
  time.sleep(3)
  alive=0
  while alive < 3:
      if dom.isActive():
          alive=4
      else:
          time.sleep(3)
          alive+=1

def get_info_vm(vm_name):
  dom = conn.lookupByName(vm_name)
  state, maxmem, mem, cpus, cput = dom.info()
  return state, maxmem, mem, cpus, cput

def attach_net(vm_name,net_name):
  dom = conn.lookupByName(vm_name)
  network_xml = f'<interface type="network"><source network="{net_name}"/><model type="virtio"/></interface>'
  dom.attachDeviceFlags(network_xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG | libvirt.VIR_DOMAIN_AFFECT_LIVE)

def detach_net(vm_name, net_name, net_mac,net_int):
  dom = conn.lookupByName(vm_name)
#  network_xml = f'<interface type="network"><mac address="{net_mac}"/><source network="{net_name}"/><model type="virtio"/></interface>'
  network_xml = f'<interface type="bridge"><mac address="{net_mac}"/><source network="{net_name}" bridge="{net_int}"/></interface>'
  print(network_xml)
  dom.detachDeviceFlags(network_xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG | libvirt.VIR_DOMAIN_AFFECT_LIVE)

def get_screenshot(vm_name):
  dom = conn.lookupByName(vm_name)
  stream = conn.newStream()
  imageType = dom.screenshot(stream,0)
  file = "tmp_screen_" + dom.name()
  fileHandler = open(file, 'wb')
  streamBytes = stream.recv(262120)
  while streamBytes != b'':
    fileHandler.write(streamBytes)
    streamBytes = stream.recv(262120)
  fileHandler.close()
  stream.finish()
  with open(file, "rb") as f:
    data = base64.b64encode(f.read())
  os.remove(file)
  return data

def get_autostart(vm_name):
  dom = conn.lookupByName(vm_name)
  return dom.autostart()

def set_autostart(vm_name):
  dom = conn.lookupByName(vm_name)
  dom.setAutostart(1)

def unset_autostart(vm_name):
  dom = conn.lookupByName(vm_name)
  dom.setAutostart(0)

"""
def get_net_vm(vm_name):
  netws, nu2 = get_virt_int()
  vm_net_list=[]
  for net in netws:
     if vm_name in net[1][0]:
        vm_net_list.append(net[0][0][0])
  return vm_net_list
"""
