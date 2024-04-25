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
apt-get install git lxc lxcfs lxc-templates qemu qemu-utils qemu-kvm virtinst bridge-utils virt-manager libvirt-daemon libvirt-daemon-system virt-viewer libvirt-clients libosinfo-bin websockify sqlite3 novnc python3-openssl openvswitch-switch openvswitch-common nginx -y
echo "Python libs install"
apt-get install python3 python3-flask python3-flask-login python3-flask-sqlalchemy python3-requests python3-lxc python3-libvirt python3-psutil python3-werkzeug python3-websockify python3-novnc python3-flask-socketio -y
echo "Enabling Libvirt"
systemctl --quiet enable --now libvirtd
systemctl --quiet  start libvirtd
echo "Bridged interface installation"
cp ./install/bridged.xml /usr/share/libvirt/networks/
virsh net-define bridged.xml
virsh net-start bridged
virsh net-autostart bridged
echo "Copy default database"
cp ./install/db.db.admin_example ./db.db
echo "Save default nginx configuration"
cp /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.original
echo "Copy Nginx configuration"
cp ./install/nginx_default /etc/nginx/sites-enabled/default
echo "Create self-signed certificate"
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 3650 -nodes -subj "/C=XX/ST=StateName/L=CityName/O=CompanyName/OU=CompanySectionName/CN=CommonNameOrHostname"
mkdir /etc/ssl/certs/hype2
mv key.pem cert.pem /etc/ssl/certs/hype2/
echo "Restarting Nginx"
systemctl restart nginx
echo "Copy noVNC files to static"
cp -R /usr/share/novnc/* /root/Hype2/static/
echo "Configure Qemu for root usage"
mv /etc/libvirt/qemu.conf /etc/libvirt/qemu.conf.original
echo 'vnc_listen = "0.0.0.0"' >> /etc/libvirt/qemu.conf
echo 'user = "root"' >> /etc/libvirt/qemu.conf
echo 'group = "root"' >> /etc/libvirt/qemu.conf
clear
echo "Installation Done"
echo "You should reboot before first usage"
