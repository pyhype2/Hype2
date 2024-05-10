from config import *
import time

def get_vm_activ():
    list_run_id=conn.listDomainsID()
    activ_vm=[]
    for id in list_run_id:
       dom=conn.lookupByID(id)
       activ_vm.append(dom.name())
    return activ_vm

#Set a VM as active
def is_active(vm_name):
  dom = conn.lookupByName(vm_name)
  try:
    dom.resume()
  except:
    pass

def get_vm_inactiv():
    inactiv_vm=conn.listDefinedDomains()
    return inactiv_vm

def get_vm_list():
    full_vm = get_vm_activ() + get_vm_inactiv()
    return full_vm

def start_vm(vm_name):
    dom = conn.lookupByName(vm_name)
    dom.create()
    time.sleep(3)
    alive=0
    while alive < 3:
        if dom.isActive():
            alive=4
        else:
            time.sleep(3)
            alive+=1

def stop_vm(vm_name):
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

def get_vm_ips(vm_name):
    dom=conn.lookupByName(vm_name)
    if not dom:
        raise SystemExit("Failed to connect to Dom")
    try:
       ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT)
    except:
       ifaces = None
    result="--.--.--.--"
    if ifaces is None:
        result="--.--.--.--"
    else:
      for (name, val) in ifaces.items():
        if val['addrs']:
            for addr in val['addrs']:
              if addr['addr']:
                result=str(addr['addr'])+"/"+str(addr['prefix'])
              break
        else:
            result="-"
    return result

def destroy_vm(vm_name):
    dom=conn.lookupByName(vm_name)
    dom.undefine()
    dom.undefineFlags(libvirt.VIR_DOMAIN_UNDEFINE_NVRAM)

def enable_emulated_tpm(vm_name):
    dom = conn.lookupByName(vm_name)
    tpm_xml = """
    <tpm model='tpm-tis'>
      <backend type='emulator' version='2.0'/>
    </tpm>
    """
    flags = (libvirt.VIR_DOMAIN_AFFECT_CONFIG | libvirt.VIR_DOMAIN_AFFECT_LIVE | libvirt.VIR_DOMAIN_AFFECT_CURRENT)
    dom.updateDeviceFlags(tpm_xml, flags )

