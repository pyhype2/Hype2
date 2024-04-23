import lxc
from datetime import datetime
from config import *

## LXC

def create_snap_lxc(lxc_name):
    cont=lxc.Container(lxc_name)
    cont.snapshot()

def get_snap_list_lxc(lxc_name):
   dom=lxc.Container(lxc_name)
   list_snap_lxc = dom.snapshot_list()
   out=[]
   for snap in list_snap_lxc:
      nom_snap=snap[0]
      date_snap=datetime.strptime(snap[2], '%Y:%m:%d %H:%M:%S')
      date_snap=date_snap.strftime("%d%m%Y%H%M")
      concat_name=dom.name+"_"+date_snap+"_"+nom_snap
      out.append(concat_name)
   return out

def del_snap_lxc(lxc_name,item):
    conn=lxc.Container(lxc_name)
    item=item.split('_')[2]
    conn.snapshot_destroy(item)

def rest_snap_lxc(lxc_name,item):
    conn=lxc.Container(lxc_name)
    item=item.split('_')[2]
    conn.snapshot_restore(item)

## VM

def create_snap_vm(vm_name):
    dom=conn.lookupByName(vm_name)
    actual_date=datetime.now()
    actual_date=actual_date.strftime("%d%m%Y%H%M")
    snapshot_name= dom.name()+"_"+actual_date+"_snap"
    SNAPSHOT_XML_TEMPLATE = """<domainsnapshot>
                                 <name>{snapshot_name}</name>
                               </domainsnapshot>"""
    dom.snapshotCreateXML(SNAPSHOT_XML_TEMPLATE.format(snapshot_name=snapshot_name),libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_ATOMIC)

def get_snap_list_vm(vm_name):
   dom=conn.lookupByName(vm_name)
   list_snap_vm=dom.snapshotListNames()
   list_snap_vm.reverse()
   out=[]
   for snap in list_snap_vm:
      out.append(snap)
   return out

def del_snap_vm(vm_name,item):
   dom=conn.lookupByName(vm_name)
   snap_del=dom.snapshotLookupByName(item)
   snap_del.delete()

def rest_snap_vm(vm_name,item):
   dom=conn.lookupByName(vm_name)
   snaps = dom.listAllSnapshots()
   for snap in snaps:
      if snap.getName() == item:
          dom.revertToSnapshot(snap)

