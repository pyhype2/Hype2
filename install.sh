#!/bin/bash
#
# Hype² installation script
# Tested on Debian 11 and Debian 12
#
# 1.0 by Pierre Porcheret
#
#
clear
echo "Requirements packages"
apt-get update -y -qq
apt-get install git lxc lxcfs lxc-templates qemu qemu-utils qemu-kvm virtinst bridge-utils virt-manager libvirt-daemon libvirt-daemon-system virt-viewer libvirt-clients libosinfo-bin websockify sqlite3 novnc
apt-get python3-openssl
echo "Openswitch install"
apt-get install openvswitch-switch openvswitch-common
echo "Python libs install"
apt-get install python3 python3-flask python3-flask-login python3-flask-sqlalchemy python3-requests python3-lxc python3-libvirt python3-psutil python3-werkzeug python3-websockify python3-novnc python3-flask-socketio
echo "Enabling Libvirt"
systemctl --quiet enable --now libvirtd
systemctl --quiet  start libvirtd
echo "Bridged interface installation"
cp ./bridged.xml /usr/share/libvirt/networks/
virsh net-define bridged.xml
virsh net-start bridged
virsh net-autostart bridged
echo "Copy default database"
cp db.db.admin_example db.db
clear
echo "Installation Done"
echo "Please follow the Qemu modification according to README.md"
