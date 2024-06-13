# Documentation

 This is more a techincal documentation that how to use this tool.

# Install

Please refer to the README file, all install steps are described.

## Pipx

Not refered in the install, but you can pipx for you install.

# Networking

Hype use OpenvSwicth for interface and network creation. Common ovs command use in case of debgug.
DNSMask, provided by LXC, is used to create DHCP for Interface configuration.


# Storage

The server storage are in *{HYPE}/storage/*
You will find a folder *win* for the virtio image, *disks* for the VM images (qcow2) and iso for iso install images.

You can change these storage in *config.py* file.

For the *disks*,if you prefer to use the default libvirt pool storage (*/var/lib/libvirt/images*)
You can modify :

*--disk path='+str(disk_path)+str(nom)+'.qcow2,size='+str(disk)+',bus=virtio*

by

*--disk pool=default,size='+str(disk)+',bus=virtio,format=qcow2*

# Virtual Server Creation

## Linux

For the moment, no issue with tested distribution:
  - Archlinux
  - Debian/ubuntu
  - Centos/Fedora/Redhat
  - FreeBSD
  - TinyCore

## Other install

Tested succeffully :
  - Pfsense,Dynfi,Opnsense

## Windows

Windows OS will need some extra-drivers to run on virtualized server.

For this during the install, the VM will need a virtIO-win iso with all drivers.
The VirtIO iso is already mounted as a CD-ROM on VM creation. Load the drivers according to you OS install.

### VirtIO

VirtIO is a QEMU drivers for Windows OS (please read : https://developer.ibm.com/articles/l-virtio/)

VirtIO can be found here :
https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/archive-virtio/?C=M;O=D

Take care of the version, some virtio are not compatible with some Windows version.

This iso is on ./storage/win/ and configured in **config.py** for upgrade.

### Tested Windows Installation (tested with Virtio 0.1.229):

Validate for :
  - Windows 8, 8,1 10 11
  - Windows Server 2019, 2022

Failed with :
  - Windows 98, Windows XP

Never Tested :
  - Win 7 and Vista

#OTHER

Please report your bugs to improve this dev.

#SOURCES

https://libvirt.gitlab.io/libvirt-appdev-guide-python/index.html
https://libvirt-python.readthedocs.io/
https://linuxcontainers.org/lxc/documentation/


# ERROR and SOLUTION

You may incounter some error in specific case, please report them if they are not in the list,
They will be consider on nexts releases.

ERROR: Error destroying Requested operation is not valid: cannot undefine domain with nvram :

SOLUTION (on CLI): virsh undefine --nvram VM_NAME


ERROR: Error stoping NOM_VM:Requested operation is not valid: domain is not running

SOLUTION 1 (on CLI): virsh reset VM_NAME

SOLUTION 2 (on CLI): virsh destroy VM_NAME (destroy the VM)



ERROR: libvirt: Storage Driver error : Requested operation is not valid: storage pool 'iso' is not active

SOLUTION (on CLI): pool = conn.storagePoolLookupByName('iso')
		   pool.undefine()
