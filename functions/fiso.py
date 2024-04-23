import os
from config import *
from xml.dom import minidom

def get_xml(vm_name):
  dom=conn.lookupByName(vm_name)
  raw_xml = dom.XMLDesc()
  xml = minidom.parseString(raw_xml)
  return xml

def get_iso_list():
    list_iso_path= []
    list_iso_size= []
    for file in os.listdir(iso_path):
       if file.endswith(".iso"):
           size=os.path.getsize(iso_path+file)
           size=human_size(size)
           list_iso_size.append(str(size))
           list_iso_path.append(str(file))
    list_iso=zip(list_iso_path, list_iso_size)
    return list_iso

def get_cdrom_attribut(vm_name):
  xml = get_xml(vm_name)
  diskTypes = xml.getElementsByTagName('disk')
  for disk_xml in diskTypes:
    if disk_xml.getAttribute('device') == 'cdrom':
      target_tag = disk_xml.getElementsByTagName('target')
      address_tag = disk_xml.getElementsByTagName('address')
      target_dev = target_tag[0].getAttribute('dev')
      target_bus = target_tag[0].getAttribute('bus')
      address_type = address_tag[0].getAttribute('type')
      address_controller = address_tag[0].getAttribute('controller')
      address_bus = address_tag[0].getAttribute('bus')
      address_target = address_tag[0].getAttribute('target')
      address_unit = address_tag[0].getAttribute('unit')
      return target_dev, target_bus, address_type, address_controller, address_bus, address_target, address_unit


def mount_iso(vm_name,iso_name):
  dom = conn.lookupByName(vm_name)
  target_dev, target_bus, address_type, address_controller, address_bus, address_target, address_unit = get_cdrom_attribut(vm_name)
  diskFile = iso_name
  diskXML = """    <disk type='file' device='cdrom'>
        <driver name='qemu' type='raw'/>
        <source file='""" + diskFile + """'/>
        <target dev='""" + target_dev + """' bus='""" + target_bus  + """'/>
        <address type='""" + address_type + """' controller='""" + address_controller + """' bus='""" + address_bus + """' target='""" + address_target + """' unit='""" + address_unit + """'/>
        </disk>"""
  dom.updateDeviceFlags(diskXML, 0)

def check_iso_is_mounted(vm_name):
  dom = conn.lookupByName(vm_name)
  raw_xml = dom.XMLDesc()
  xml = minidom.parseString(raw_xml)
  diskTypes = xml.getElementsByTagName('disk')
  for disk_xml in diskTypes:
     disk = None
     source = disk_xml.getElementsByTagName('source')
     if disk_xml.getAttribute('device') == 'cdrom':
        try:
          gotdata= source[0].getAttribute('file')
          if source[0].getAttribute('file'):
            state = 1
          else:
            state = 0
        except IndexError:
          state = 0
#Return 1 if mounted or 0 if not mounted
  return state

