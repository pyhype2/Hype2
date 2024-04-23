from config import *
from xml.etree import ElementTree as ET
from flask import request, Response
import subprocess
import os

def get_vnc_port(vm_name):
    dom = conn.lookupByName(vm_name)
    vm_xml = dom.XMLDesc(0)
    et_xml = ET.fromstring(vm_xml)
    graphics = et_xml.find('./devices/graphics')
    vnc_port = graphics.get('port')
    return vnc_port

def kill_consoles():
    subprocess.run("pkill -9 -f 'websockify'", shell=True)
    subprocess.run("for i in $(pgrep -f 'pyxterm'); do kill -9 $i; done", shell=True)

def socket_connect(vm_name):
    kill_consoles()
    vm_port = get_vnc_port(vm_name)
    subprocess.run(['websockify', '-D', '--web=/usr/share/novnc/', '6080', 'localhost:' + vm_port])

def pyxterm_connect(path,lxc_name):
    kill_consoles()
    cmd = ['python3', f'{path}/pyxterm.py', '--command', 'lxc-attach', '--cmd-args', lxc_name]
    pyx_process = subprocess.Popen(cmd)
