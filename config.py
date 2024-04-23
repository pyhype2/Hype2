import os
import libvirt
import math

hype_version = '1.0'
#Flask config
class flask_config:
  port=5007
  host='0.0.0.0'
  thread=True
  debug=False

#Path
path = os.path.abspath(os.path.dirname(__file__))
iso_path= path+'/storage/iso/'
disk_path = path+'/storage/disks/'
virtuo_path= path+'/storage/win/'
virtuo_file='virtio-win-0.1.229.iso'
#Qemu connection
try:
  conn = libvirt.open("qemu:///system")
except:
  exit(1)

#Convert
units_map = [
    (1<<50, ' PB'),
    (1<<40, ' TB'),
    (1<<30, ' GB'),
    (1<<20, ' MB'),
    (1<<10, ' KB'),
    (1, (' byte', ' bytes')),
]

def human_size(bytes, units=units_map):
    for factor, suffix in units:
        if bytes >= factor:
            break
    amount = int(bytes / factor)
    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return str(amount) + suffix

#Debug for Ct actions
def mount_pts():
    os.system('mount -o remount,rw /dev/pts')

#LXC Os list
def list_distrib():
    link_list = ['debian','ubuntu','centos','busybox','ubuntu-cloud','cirros','sabayon']
    name_list = ['Debian','Ubuntu','Centos','Busybox','Ubuntu-cloud','Cirros','Sabayon']
    listd = zip(name_list, link_list)
    return listd

#VM Os list
def get_os_profile_list():
    list_profile=[]
    for profile in os.popen("osinfo-query os | awk '{ print $1 }' | awk 'NR > 2 { print }'"):
       list_profile.append(str(profile))
    return list_profile
