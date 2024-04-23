import os
from config import *
from xml.dom import minidom
import subprocess
from functions.fpool import *


def get_volume_disk(disk_path):
   refresh_pool()
   vol_disk = conn.storageVolLookupByPath(disk_path)
   vol_size = vol_disk.info()[1]
   vol_size_G = vol_size / (1024*1024*1024)
   return vol_size_G

def get_disks_info(vm_name):
    disks = []
    dom = conn.lookupByName(vm_name)
    raw_xml = dom.XMLDesc(0)
    xml = minidom.parseString(raw_xml)
    diskTypes = xml.getElementsByTagName('disk')
    for diskType in diskTypes:
        if diskType.getAttribute('device') == 'disk':
            disk_unit = []
            disk_id = 'Unknown'
            diskNodes = diskType.childNodes
            for diskNode in diskNodes:
                if diskNode.nodeName == 'target':
                     for attr in diskNode.attributes.keys():
                       if diskNode.attributes[attr].name == 'dev':
                          disk_id = diskNode.attributes[attr].value
                if diskNode.nodeName == 'source':
                    for attr in diskNode.attributes.keys():
                        if diskNode.attributes[attr].name == 'file':
                            blkinf = dom.blockInfo(diskNode.attributes[attr].value)
                            vol_size = os.path.getsize(diskNode.attributes[attr].value)
                            diskname = os.path.basename(diskNode.attributes[attr].value)
                            volsize = get_volume_disk(diskNode.attributes[attr].value)
                            disksize = round(blkinf[0] / 1024**3)
                            diskused = round(blkinf[1] / 1024**3)
                            if disksize > 0:
                              diskpercent = (diskused*100 / disksize)
                            else:
                              diskpercent = 0
                            disk_unit = [diskNode.attributes[attr].value,disksize,diskused,diskpercent,diskname,int(volsize)]
                if diskNode.nodeName == 'target':
                     for attr in diskNode.attributes.keys():
                       if diskNode.attributes[attr].name == 'dev':
                          disk_id = diskNode.attributes[attr].value
                          disk_unit.append(disk_id)
            disks.append(disk_unit)
    return disks

def create_attached_disk(vm_name,disk_name,disk_size,disk_id):
  pool = conn.storagePoolLookupByName('disks')
  disk_full = disk_path+disk_name+".qcow2"
  xml_desc = f"""
      <volume>
          <name>{disk_name}.qcow2</name>
          <capacity unit="G">{disk_size}</capacity>
          <allocation unit="G">{disk_size}</allocation>
          <target>
              <format type="qcow2"/>
              <path>{disk_full}</path>
          </target>
      </volume>
    """
  pool.createXML(xml_desc, 0)

  dom = conn.lookupByName(vm_name)
  try:
    dom.resume
  except:
    pass
  disk_full = disk_path+disk_name+".qcow2"
  flags = (libvirt.VIR_DOMAIN_AFFECT_CONFIG |
           libvirt.VIR_DOMAIN_AFFECT_LIVE |
           libvirt.VIR_DOMAIN_AFFECT_CURRENT)
  disk_xml = """
      <disk type='file' device='disk'>
          <driver name='qemu' type='qcow2'/>
          <source file='{source}'/>
          <target dev='{target}'/>
      </disk>
  """.format(source=disk_full, target=disk_id)
  dom.attachDeviceFlags(disk_xml, flags)
  refresh_pool()

def resize_disk(disk_file,actual_size,new_size,vm_name,disk_id):
  dom = conn.lookupByName(vm_name)
  flags = (libvirt.VIR_DOMAIN_AFFECT_CONFIG |
         libvirt.VIR_DOMAIN_AFFECT_LIVE |
         libvirt.VIR_DOMAIN_AFFECT_CURRENT)
  disk_xml = """
      <disk type='file' device='disk'>
          <driver name='qemu' type='qcow2'/>
          <source file='{source}'/>
          <target dev='{target}'/>
      </disk>
  """.format(source=disk_file, target=disk_id)
  cmd = "virsh detach-disk '"+vm_name+"' "+disk_file+" --persistent --config --live"
  subprocess.call(cmd, shell=True)
  if int(actual_size) < int(new_size):
         cmd = "qemu-img resize -f qcow2 "+str(disk_file)+" "+str(new_size)+"G"
         subprocess.call(cmd, shell=True)
  else:
         cmd = "qemu-img resize -f qcow2 --shrink "+str(disk_file)+" "+str(new_size)+"G"
         subprocess.call(cmd, shell=True)
  dom.attachDeviceFlags(disk_xml, flags)
  refresh_pool()

def detach_disk(vm_name,diskfile):
  cmd = "virsh detach-disk '"+str(vm_name)+"' "+str(diskfile)+" --persistent --config --live"
  subprocess.call(cmd, shell=True)
  refresh_pool()

