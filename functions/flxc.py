import lxc
from config import *

### LISTS

def get_lxc_list():
    full_ct=lxc.list_containers()
    full_ct = list(full_ct)
    return full_ct

def get_lxc_activ():
    activ_ct = []
    for ct_name in get_lxc_list():
       ct_state=lxc.Container(ct_name)
       if ( ct_state.state == "RUNNING"):
          activ_ct.append(ct_name)
    return activ_ct

def get_lxc_inactiv():
    inactiv_ct = []
    for ct_name in get_lxc_list():
       ct_state=lxc.Container(ct_name)
       if ( ct_state.state != "RUNNING"):
          inactiv_ct.append(ct_name)
    return inactiv_ct

### ACTIONS

def start_lxc(lxc_name):
    mount_pts()
    container=lxc.Container(lxc_name)
    container.start()
    container.wait("RUNNING", 3)

def stop_lxc(lxc_name):
    mount_pts()
    container=lxc.Container(lxc_name)
    container.stop()
    container.wait("STOPPED", 3)

def get_lxc_ip(lxc_name):
    ct_state=lxc.Container(lxc_name)
    lxc_ip = str(ct_state.get_ips()).replace('(', '').replace(')', '').replace(',', '').replace('\'', '')
    return lxc_ip

## CREATE
def create_lxc(lxc_name,lxc_os):
    mount_pts()
    container=lxc.Container(lxc_name)
    resultats=container.create(lxc_os)

def set_lxc_ip(lxc_ip):
    file_object = open('/var/lib/lxc/'+lxc_name+'/config', 'a')
    file_object.write('lxc.net.0.ipv4.address = '+lxc_ip+'\n')
    file_object.write('lxc.net.0.ipv4.gateway = auto')
    file_object.close()

## DESTROY

def destroy_lxc(lxc_name):
    container=lxc.Container(lxc_name)
    container.destroy()

## RESSOURCES

def get_lxc_ressources(lxc_name):
    container=lxc.Container(lxc_name)
    mem_max = container.get_config_item('lxc.cgroup2.memory.max')
    mem = container.get_config_item('lxc.cgroup2.memory.high')
    swap_max = container.get_config_item('lxc.cgroup2.memory.swap.max')
    vcpu = container.get_config_item('lxc.cgroup2.cpuset.cpus')
    return vcpu, mem, mem_max, swap_max

def set_lxc_ressources(lxc_name,lxc_item,val):
    container=lxc.Container(lxc_name)
    container.set_config_item(lxc_item,val)
    container.save_config()




