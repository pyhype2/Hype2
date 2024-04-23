from config import *
import re
import os
import psutil
from datetime import datetime

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

class Host:
    def __init__(self):
        self.hostname = psutil.os.uname().nodename
        self.cpu_number = psutil.cpu_count(logical=False)
        self.vcpu = psutil.cpu_count()
        self.mem_max = human_size(psutil.virtual_memory().total)
        self.boot_time = datetime.fromtimestamp(psutil.boot_time() - 60)
        self.cpu_usage = psutil.cpu_percent(interval=0.0, percpu=False)
        self.mem_usage = psutil.virtual_memory().percent
        self.swap_usage = psutil.swap_memory().percent


class ENV:
    def __init__(self):
        self.hostname = psutil.os.uname().nodename
        self.cpu_number = psutil.cpu_count(logical=False)
        self.vcpu = psutil.cpu_count()
        self.mem_max = human_size(psutil.virtual_memory().total)
        self.boot_time = psutil.boot_time()

class CPU:
    def __init__(self):
        self.cpu = {}
        self.cpu['percent'] = psutil.cpu_percent(interval=0.0, percpu=False)
        self.cpu['time_user'] = psutil.cpu_times_percent().user
        self.cpu['time_nice'] = psutil.cpu_times_percent().nice
        self.cpu['time_system'] = psutil.cpu_times_percent().system
        self.cpu['time_idle'] = psutil.cpu_times_percent().idle
        self.cpu['time_iowait'] = psutil.cpu_times_percent().iowait
        self.cpu['time_irq'] = psutil.cpu_times_percent().irq
        self.cpu['time_softirq'] = psutil.cpu_times_percent().softirq
        self.cpu['time_steal'] = psutil.cpu_times_percent().steal
        self.cpu['time_guest'] = psutil.cpu_times_percent().guest
        self.cpu['time_guest_nice'] = psutil.cpu_times_percent().guest_nice

class Memory:
   def __init__(self):

        self.mem = {}
        self.mem['total'] = human_size(psutil.virtual_memory().total)
        self.mem['available'] = human_size(psutil.virtual_memory().available)
        self.mem['percent'] = psutil.virtual_memory().percent
        self.mem['used'] = human_size(psutil.virtual_memory().used)
        self.mem['free'] = human_size(psutil.virtual_memory().free)
        self.mem['active'] = human_size(psutil.virtual_memory().active)
        self.mem['inactive'] = human_size(psutil.virtual_memory().inactive)
        self.mem['buffers'] = human_size(psutil.virtual_memory().buffers)
        self.mem['cached'] = human_size(psutil.virtual_memory().cached)
        self.mem['shared'] = human_size(psutil.virtual_memory().shared)
        self.mem['slab'] = human_size(psutil.virtual_memory().slab)

class Swap:
    def __init__(self):
        self.swap = {}
        self.swap['total'] = human_size(psutil.swap_memory().total)
        self.swap['used'] = human_size(psutil.swap_memory().used)
        self.swap['free'] = human_size(psutil.swap_memory().free)
        self.swap['percent'] = psutil.swap_memory().percent
        self.swap['sin'] = human_size(psutil.swap_memory().sin)
        self.swap['sout'] = human_size(psutil.swap_memory().sout)

class Disks:
    def __init__(self):
        num=0
        for i in psutil.disk_partitions():
            exec("self.disk_"+str(num)+" = {}")
            exec("self.disk_"+str(num)+"['device'] = '"+str(i.device)+"'")
            exec("self.disk_"+str(num)+"['mountpoint'] = '"+str(i.mountpoint)+"'")
            exec("self.disk_"+str(num)+"['fstype'] = '"+str(i.fstype)+"'")
            exec("self.disk_"+str(num)+"['opts'] = '"+str(i.opts)+"'")
            exec("self.disk_"+str(num)+"['maxfile'] = '"+str(i.maxfile)+"'")
            exec("self.disk_"+str(num)+"['maxpath'] = '"+str(i.maxpath)+"'")
            exec("self.disk_"+str(num)+"['size_total'] = '"+str(human_size(psutil.disk_usage(i.mountpoint).total))+"'")
            exec("self.disk_"+str(num)+"['size_used'] = '"+str(human_size(psutil.disk_usage(i.mountpoint).used))+"'")
            exec("self.disk_"+str(num)+"['size_free'] = '"+str(human_size(psutil.disk_usage(i.mountpoint).free))+"'")
            exec("self.disk_"+str(num)+"['size_percent'] = '"+str(psutil.disk_usage(i.mountpoint).percent)+"'")
            num+=1

class Network:
    def __init__(self):
        num=0
        for interface in psutil.net_if_addrs():
            exec("self.net_"+str(num)+" = {}")
            interface_usage = psutil.net_io_counters(pernic=True)
            for detail in psutil.net_if_addrs()[interface]:
                exec("self.net_"+str(num)+"['name'] = '"+str(interface)+"'")
                exec("self.net_"+str(num)+"['bytes_sent'] = '"+str(human_size(interface_usage[interface].bytes_sent))+"'")
                exec("self.net_"+str(num)+"['bytes_recv'] = '"+str(human_size(interface_usage[interface].bytes_recv))+"'")
                ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
                if ip_pattern.match(detail.address):
                    exec("self.net_"+str(num)+"['address_v4'] = '"+str(detail.address)+"'")
                else:
                    exec("self.net_"+str(num)+"['address_v6'] = '"+str(detail.address)+"'")
                if detail.netmask:
                    if ip_pattern.match(detail.netmask):
                        exec("self.net_"+str(num)+"['netmask_v4'] = '"+str(detail.netmask)+"'")
                    else:
                        exec("self.net_"+str(num)+"['netmask_v6'] = '"+str(detail.netmask)+"'")
            num+=1

class Monit:
    def __init__(self):
        self.env = ENV()
        self.cpu = CPU()
        self.mem = Memory()
        self.swap = Swap()
        self.disks = Disks()
        self.network = Network()

def get_host_full():
    Localhost = Monit()
    host_full = {}
    host_full.update(vars(Localhost.env))
    host_full.update(vars(Localhost.cpu))
    host_full.update(vars(Localhost.mem))
    host_full.update(vars(Localhost.swap))
    host_full.update(vars(Localhost.disks))
    host_full.update(vars(Localhost.network))
    return host_full
