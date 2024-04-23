import os
import json
import requests
import subprocess
from flask import Flask , redirect , render_template, request, Response, stream_with_context, url_for, make_response, flash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager , UserMixin , login_required ,login_user, logout_user,current_user
from werkzeug.security import generate_password_hash, check_password_hash

from config import *
from functions.fhost import *
from functions.flxc import *
from functions.fiso import *
from functions.fvm import *
from functions.fvnc import *
from functions.fbackup import *
from functions.fpool import *
from functions.fedit import *
from functions.fdisks import *
from functions.fnet import *

app = Flask(__name__,static_url_path='',static_folder='static',template_folder='templates')

###########################
##       DROPZONE        ##
###########################
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.iso']
app.config['UPLOAD_PATH'] = iso_path

############################
##         LOGIN          ##
############################

#Database (see base.sql for creation user table)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(path,'db.db')
app.config['SECRET_KEY']='619619'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=True
db = SQLAlchemy(app)

#Login init (login_view => default login page)
login_manager = LoginManager()
login_manager.login_view = "/login"
login_manager.init_app(app)

#Database search
class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    username = db.Column(db.String(200))
    email = db.Column(db.String(200))
    password = db.Column(db.String(200))

@login_manager.user_loader
def get(id):
    return User.query.get(id)

#Pass encrypt
def encrypt(password):
  hashed_pass=generate_password_hash(password)
  return hashed_pass

#Page for login
@app.route('/login',methods=['GET'])
def get_login():
    return render_template('login.html')

#Page for user creation (secured)
@app.route('/signup',methods=['GET'])
@login_required
def get_signup():
    return render_template('signup.html')

#Page for login, adding user and logout
@app.route('/login',methods=['POST'])
def login_post():
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
      login_user(user)
      return redirect('/')
    return redirect('/')

@app.route('/signup',methods=['POST'])
@login_required
def signup_post():
    username = request.form['username']
    email = request.form['email']
    password = encrypt(request.form['password'])
    user = User(username=username,email=email,password=password)
    try:
        db.session.add(user)
        db.session.commit()
        flash(user+' added', category='success')
    except Exception as e:
        flash('Error on adding user :'+str(e), category='danger')
    return redirect('param')

@app.route('/logout',methods=['GET'])
def logout():
    logout_user()
    return redirect('/login')

############################
##         INDEX          ##
############################

@app.route('/',methods=['GET'])
@login_required
def get_home():
    vlxc, vlibvirt, vhype = get_version()
    lxc_up = len(get_lxc_activ())
    lxc_down = len(get_lxc_inactiv())
    vm_up = len(get_vm_activ())
    vm_down = len(get_vm_inactiv())
    full = get_host_full()
    return render_template('index.html', host=Host(), full = full, lxc_up=lxc_up, lxc_down=lxc_down, vm_up=vm_up, vm_down=vm_down,vlxc=vlxc, vlibvirt=vlibvirt, vhype=vhype)

def get_ressources():
    while True:
       full = get_host_full()
       json_data = json.dumps(
           {
              "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "cpu_percent": full['cpu']['percent'],
              "mem_percent": full['mem']['percent'],
              "swap_percent": full['swap']['percent'],
              "cpu_time_user": full['cpu']['time_user'],
              "cpu_time_nice": full['cpu']['time_nice'],
              "cpu_time_system": full['cpu']['time_system'],
              "cpu_time_idle": full['cpu']['time_idle'],
              "cpu_time_iowait": full['cpu']['time_iowait'],
              "cpu_time_irq": full['cpu']['time_irq'],
              "cpu_time_softirq": full['cpu']['time_softirq'],
              "cpu_time_steal": full['cpu']['time_steal'],
              "cpu_time_guest": full['cpu']['time_guest'],
              "cpu_time_guest_nice": full['cpu']['time_nice'],
              "mem_total": full['mem']['total'],
              "mem_available": full['mem']['available'],
              "mem_used": full['mem']['used'],
              "mem_free": full['mem']['free'],
              "mem_active": full['mem']['active'],
              "mem_inactive": full['mem']['inactive'],
              "mem_buffers": full['mem']['buffers'],
              "mem_cached": full['mem']['cached'],
              "mem_shared": full['mem']['shared'],
              "mem_slab": full['mem']['slab'],
              "swap_total": full['swap']['total'],
              "swap_used": full['swap']['used'],
              "swap_free": full['swap']['free'],
              "swap_sin": full['swap']['sin'],
              "swap_sout": full['swap']['sout'],
           }
       )
       yield f"data:{json_data}\n\n"
       time.sleep(1)

@app.route('/chart-ressources/')
def chart_data() -> Response:
    response = Response(stream_with_context(get_ressources()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

############################
##         POOL           ##
############################

@app.route('/pool',methods=['GET'])
@login_required
def get_pool():
    return render_template('pool.html',list_pool_full = get_full_pool())

@app.route('/del_volume',methods=['POST'])
@login_required
def delvol():
    pool_name = request.form['pool_name']
    volume_name = request.form['volume_name']
    try:
        del_pool_vol(pool_name,volume_name)
        flash(volume_name+' deleted', category='success')
    except Exception as e:
        flash('Error on deleting '+volume_name+':'+str(e), category='danger')
    return redirect(url_for('get_pool'))

############################
##         NETWORK        ##
############################
@app.route('/network',methods=['GET'])
@login_required
def network():
  net_tree,net_na = get_virt_int()
  return render_template('network.html', net_hard_int = conn.listInterfaces(), net_tree=net_tree, net_na=net_na)

@app.route('/delnetvm',methods=['POST'])
@login_required
def delnetvm():
   vm_name = request.form['vm_name']
   net_name = request.form['del_net_vm']
   net_mac = request.form['del_mac_vm']
   net_int = request.form['del_net_int']
   try:
     detach_net(vm_name, net_name, net_mac, net_int)
     flash(net_name+' detached from '+vm_name, category='success')
   except Exception as e:
     flash('Error deleting '+net_name+' from '+vm_name+': '+str(e), category='danger')
   return redirect(url_for('network'))


@app.route('/createnet',methods=['GET'])
@login_required
def createnet():
  return render_template('createnet.html')

@app.route('/delnet',methods=['POST'])
@login_required
def delnet():
   net_name = request.form['net_del']
   net_int = get_int(net_name)
   try:
     delete_network(net_name,net_int)
     flash(net_name+' deleted', category='success')
   except Exception as e:
     flash('Error on deleting '+net_name+':'+str(e), category='danger')
   return redirect(url_for('network'))

@app.route('/createint',methods=['POST'])
@login_required
def createint():
    net_name = request.form['net_name']
    net_int = request.form['net_int']
    ip_int = request.form['ip_int']
    mask_int = request.form['mask_int']
    min_dhcp = request.form['min_dhcp']
    max_dhcp = request.form['max_dhcp']
    nb_ip = diff_net(min_dhcp,max_dhcp)
    try:
       create_network(net_name,net_int)
    except Exception as e:
       flash('Error creating '+net_name+':'+str(e), category='danger')
       delete_network(net_name,net_int)
       return redirect(url_for('network'))
    try:
       cmd="ifconfig "+str(net_int)+" "+str(ip_int)+" netmask "+str(mask_int)+" up"
       subprocess.call(cmd, shell=True)
    except Exception as e:
       flash('Error starting '+net_name+':'+str(e), category='danger')
       delete_network(net_name,net_int)
       return redirect(url_for('network'))
    try:
       cmd2="dnsmasq --interface="+str(net_int)+" --bind-interfaces --dhcp-range "+str(min_dhcp)+","+str(max_dhcp)+" --dhcp-lease-max="+str(nb_ip)+" --dhcp-authoritative --pid-file=/run/dhypecp_"+net_int+".pid"
       subprocess.call(cmd2, shell=True)
    except Exception as e:
       flash("Error on DHCP for "+net_name,category='danger')
       delete_network(net_name,net_int)
       return redirect(url_for('network'))
    flash(net_name+' had been created', category='success')
    return redirect(url_for('network'))

############################
##        DISKS           ##
############################

@app.route('/editdisks',methods=['POST'])
@login_required
def editdisks():
   disk_id = request.form['disk_id']
   disk_file = request.form['diskfile']
   disk_name = os.path.basename(disk_file)
   actual_size = request.form['actual_size']
   new_size = request.form['new_size']
   vm_name = request.form['vm_name']
   is_active(vm_name)
   try:
     resize_disk(disk_file,actual_size,new_size,vm_name,disk_id)
     flash(disk_name+' had been resized to '+str(new_size)+'G', category='success')
   except Exception as e:
     flash('Error resizing '+disk_name+':'+str(e), category='danger')
   return redirect(url_for('state'))

@app.route('/adddisk',methods=['POST'])
@login_required
def adddisk():
  disk_name = request.form['disk_name']
  vm_name = request.form['vm_name']
  disk_size = request.form['disk_size']
  disk_id = request.form['disk_id']
  is_active(vm_name)
  try:
     create_attached_disk(vm_name,disk_name,disk_size,disk_id)
     flash(disk_name+' had been created and attached', category='success')
  except Exception as e:
     flash('Error creating '+disk_name+':'+str(e), category='danger')
  return redirect(url_for('state'))

@app.route('/detachdisk',methods=['POST'])
@login_required
def detachdisk():
  diskfile = request.form['diskfile']
  disk_name = os.path.basename(diskfile)
  vm_name = request.form['vm_name']
  is_active(vm_name)
  try:
     detach_disk(vm_name,diskfile)
     flash(disk_name+' had been dettached', category='success')
  except Exception as e:
     flash('Error Detaching '+disk_name+' on '+vm_name+':'+str(e), category='danger')
  return redirect(url_for('state'))


############################
##        VNC             ##
############################

@app.route('/vnc',methods=['GET','POST',"DELETE"])
@login_required
def vnc_connect():
    if request.method=='GET':
        resp = requests.get('http://localhost:6080/vnc.html')
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in  resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    elif request.method=='POST':
        resp = requests.post('http://localhost:6080/vnc.html',json=request.get_json())
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    elif request.method=='DELETE':
        resp = requests.delete('http://localhost:6080/vnc.html').content
        response = Response(resp.content, resp.status_code, headers)
        return response

@app.route('/console_lxc',methods=['GET','POST','DELETE'])
@login_required
def consolelxc():
    lxc_name = request.form['lxc_name']
    try:
        pyxterm_connect(path,lxc_name)
        time.sleep(2)
        return render_template('terminal.html')
    except Exception as e:
        flash('Error starting Terminal :'+str(e), category='danger')
        return redirect(url_for('state'))

@app.route('/ter',methods=['GET','POST',"DELETE"])
@login_required
def ter_connect():
    if request.method=='GET':
        resp = requests.get('http://localhost:5008/')
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in  resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    elif request.method=='POST':
        resp = requests.post('http://localhost:5008/',json=request.get_json())
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    elif request.method=='DELETE':
        resp = requests.delete('http://localhost:5008/').content
        response = Response(resp.content, resp.status_code, headers)
        return response

@app.route('/console_vm',methods=['POST'])
@login_required
def consolevm():
    vm_name = request.form['vm_name']
    is_active(vm_name)
    try:
        socket_connect(vm_name)
        return render_template('vnc.html')
    except Exception as e:
        flash('Error starting VNC :'+str(e), category='danger')
        return redirect(url_for('state'))

############################
##       PARAMETERS       ##
############################
def get_users():
    users = User.query.all()
    list_users=[]
    for uni in users:
        single=[]
        single.append(uni.username)
        single.append(uni.email)
        list_users.append(single)
    return list_users

@app.route('/param',methods=['GET'])
@login_required
def param():
    return render_template('param.html',users_list = get_users())

@app.route('/deluser',methods=['POST'])
@login_required
def deluser():
    username = request.form['username']
    email = request.form['email']
    try:
        User.query.filter_by(username=username,email=email).delete()
        db.session.commit()
        flash(username+' deleted', category='success')
    except Exception as e:
        flash('Error on deleting '+username+':'+str(e), category='danger')
    return redirect('param')


############################
##         EDIT           ##
############################

@app.route('/editlxc',methods=['POST'])
@login_required
def editlxc():
    lxc_name = request.form['edit']
    vcpu, mem, mem_max, swap_max = get_lxc_ressources(lxc_name)
    return render_template('edit_lxc.html', lxc_name=str(lxc_name), max_Mermory=str(' '.join(mem_max)),max_vCPU=str(' '.join(vcpu)), max_swap=str(' '.join(swap_max)), actual_ram=str(' '.join(mem)))

@app.route('/editressourceslxc',methods=['POST'])
@login_required
def editressourceslxc():
    lxc_name = str(request.form['lxc_name'])
    vcpu, mem, mem_max, swap_max = get_lxc_ressources(lxc_name)
    new_max_swap = request.form['new_max_swap']
    new_max_mem = request.form['new_max_mem']
    new_mem = request.form['new_mem']
    new_cpu = request.form['new_cpu']
    if new_max_swap != ' '.join(swap_max):
      try:
        lxc_item = 'lxc.cgroup2.memory.swap.max'
        set_lxc_ressources(lxc_name,lxc_item,new_max_swap)
      except Exception as e:
        flash('Error editing Swap for '+lxc_name+': '+str(e), category='danger')
    if new_max_mem != ' '.join(mem_max):
      try:
        lxc_item = 'lxc.cgroup2.memory.max'
        set_lxc_ressources(lxc_name,lxc_item,new_max_mem)
      except Exception as e:
        flash('Error editing Max Memory for '+lxc_name+': '+str(e), category='danger')
    if new_mem != ' '.join(mem):
      try:
        lxc_item = 'lxc.cgroup2.memory.high'
        set_lxc_ressources(lxc_name,lxc_item,new_mem)
      except Exception as e:
        flash('Error editing Memory for '+lxc_name+': '+str(e), category='danger')
    if new_cpu  != ' '.join(vcpu):
      try:
        lxc_item = 'lxc.cgroup2.cpuset.cpus'
        set_lxc_ressources(lxc_name,lxc_item,new_cpu)
      except Exception as e:
        flash('Error editing CPU for '+lxc_name+': '+str(e), category='danger')
    return redirect(url_for('state'))

@app.route('/editvm',methods=['POST'])
@login_required
def edit():
    vm_name = request.form['edit']
    state, maxmem, mem, cpus, cput = get_info_vm(vm_name)
    try:
      screen_64=get_screenshot(vm_name).decode('ASCII')
    except:
      screen_64="/9j/4AAQSkZJRgABAQEAeAB4AAD/2wBDAAIBAQIBAQICAgICAgICAwUDAwMDAwYEBAMFBwYHBwcGBwcICQsJCAgKCAcHCg0KCgsMDAwMBwkODw0MDgsMDAz/2wBDAQICAgMDAwYDAwYMCAcIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAz/wAARCAMABAADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDLooor8XP4DCiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooA/9k="
#    return render_template('edit.html', vm_name=vm_name, max_Mermory=conn.getInfo()[1],max_vCPU= conn.getMaxVcpus(None),actual_vCPU=cpus, actual_ram=int(mem/1024),screen_64=screen_64,actual_autostart=get_autostart(vm_name),disks=get_disks_info(vm_name),list_net=conn.listNetworks(),vm_info=get_vm_infos(vm_name))
    return render_template('edit.html', vm_name=vm_name, max_Mermory=conn.getInfo()[1],max_vCPU= conn.getMaxVcpus(None),actual_vCPU=cpus, actual_ram=int(mem/1024),screen_64=screen_64,actual_autostart=get_autostart(vm_name),disks=get_disks_info(vm_name),list_net=conn.listNetworks())

@app.route('/addnetvm',methods=['POST'])
@login_required
def addnetvm():
   vm_name = request.form['vm_name']
   new_net_vm = request.form['new_net_vm']
   try:
     attach_net(vm_name,new_net_vm)
     flash(new_net_vm+' attached to '+vm_name, category='success')
   except Exception as e:
     flash('Error adding '+new_net_vm+' to '+vm_name+': '+str(e), category='danger')
   return redirect(url_for('state'))

@app.route('/editressources',methods=['POST'])
@login_required
def editressources():
    vm_name = request.form['vm_name']
    state, maxmem, mem, cpus, cput = get_info_vm(vm_name)
    new_ram = int(request.form['new_mem'])
    new_autostart = request.form.get('new_autostart')
    new_cpu = int(request.form['new_cpu'])
    if new_cpu != cpus:
      try:
          set_vcpu(vm_name,new_cpu)
      except Exception as e:
          flash('Error editing CPU for '+vm_name+': '+str(e), category='danger')
    if new_ram != int(mem/1024):
      try:
          set_memory(vm_name,int(new_ram*1024))
      except Exception as e:
          flash('Error editing Memory for '+vm_name+': '+str(e), category='danger')
    if request.form.get('new_autostart')=='auto_check':
      try:
          set_autostart(vm_name)
      except Exception as e:
          flash('Error editing Autostart for '+vm_name+': '+str(e), category='danger')
    else:
      try:
          unset_autostart(vm_name)
      except Exception as e:
          flash('Error editing Autostart for '+vm_name+': '+str(e), category='danger')
    return redirect(url_for('state'))

############################
##         ISO           ##
############################

@app.route('/iso',methods=['GET'])
@login_required
def iso():
    return render_template('iso.html', list_iso = get_iso_list(), list_vm = get_vm_list(), list_iso_mount = get_iso_list())

@app.route('/deliso',methods=['POST'])
@login_required
def delete_iso():
    file=request.form['fichier']
    path=os.path.join(iso_path, file)
    try:
        os.remove(path)
        flash(file+' deleted', category='success')
    except Exception as e:
        flash('Error on deleting '+file+':'+str(e), category='danger')
    return render_template('iso.html', list_iso = get_iso_list(), list_vm = get_vm_list(), list_iso_mount = get_iso_list())

@app.route('/mountiso', methods=['POST'])
@login_required
def mountiso():
    vm_name=request.form['vm']
    if request.form['iso'] == '':
        iso_name = ''
    else:
        iso_name=iso_path+request.form['iso']
    try:
        mount_iso(vm_name,iso_name)
        flash(iso_name+' mounted', category='success')
    except Exception as e:
        flash('Error on mounting '+iso_name+':'+str(e), category='danger')
    return redirect(url_for('state'))

@app.route('/ejectiso', methods = ['POST'])
@login_required
def eject_iso():
    vm_name=request.form['ejectisovm']
    state = check_iso_is_mounted(vm_name)
    while state != 0:
        iso_file='';
        mount_iso(vm_name,iso_name)
        state = check_iso_is_mounted(vm_name)

@app.route('/iso', methods=['POST'])
@login_required
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            return "Invalid image", 400
        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    return '', 204

############################
##         BACKUP         ##
############################

@app.route('/backup')
@login_required
def backup():
    full_snap_lxc=[]
    full_snap_vm=[]
    for lxc_name in get_lxc_list():
        if get_snap_list_lxc(lxc_name):
           full_snap_lxc.append(get_snap_list_lxc(lxc_name))
        else:
           full_snap_lxc.append('')
    for vm_name in get_vm_list():
        if get_snap_list_vm(vm_name):
           full_snap_vm.append(get_snap_list_vm(vm_name))
        else:
           full_snap_vm.append('')
    list_snap_lxc = zip(get_lxc_list(), full_snap_lxc)
    list_snap_vm = zip(get_vm_list(), full_snap_vm)
    return render_template('backup.html',list_snap_lxc=list_snap_lxc,list_snap_vm=list_snap_vm)

@app.route('/snaplxc', methods = ['POST'])
@login_required
def snaplxc():
   lxc_name=request.form['snap']
   try:
       create_snap_lxc(lxc_name)
       flash('Snapshot '+lxc_name+' done', category='success')
   except Exception as e:
       flash('Error on snapshoting '+lxc_name+':'+str(e), category='danger')
   return redirect(url_for('backup'))

@app.route('/del_snap_lxc', methods = ['POST'])
@login_required
def delsnaplxc():
    lxc_name=request.form['lxc_name']
    item=request.form['item']
    try:
        del_snap_lxc(lxc_name,item)
        flash(item+' deleted', category='success')
    except Exception as e:
        flash('Error on deleting '+item+':'+str(e), category='danger')
    return redirect(url_for('backup'))

@app.route('/rest_snap_lxc', methods = ['POST'])
@login_required
def restsnap_lxc():
    lxc_name=request.form['lxc_name']
    item=request.form['item']
    try:
        rest_snap_lxc(lxc_name,item)
        flash('Restore '+item+' done', category='success')
    except Exception as e:
        flash('Error restoring '+item+':'+str(e), category='danger')
    return redirect(url_for('backup'))

@app.route('/snapvm', methods = ['POST'])
@login_required
def snapvm():
   vm_name=request.form['snap']
   try:
       create_snap_vm(vm_name)
       flash('Snapshot '+vm_name+' done', category='success')
   except Exception as e:
       flash('Error on snapshoting '+vm_name+':'+str(e), category='danger')
   return redirect(url_for('backup'))

@app.route('/del_snap_vm', methods = ['POST'])
@login_required
def delsnapvm():
    vm_name=request.form['vm_name']
    item=request.form['item']
    try:
        del_snap_vm(vm_name,item)
        flash(item+' deleted', category='success')
    except Exception as e:
        flash('Error on deleting '+item+':'+str(e), category='danger')
    return redirect(url_for('backup'))

@app.route('/rest_snap_vm', methods = ['POST'])
@login_required
def restsnap_vm():
    vm_name=request.form['lxc_name']
    item=request.form['item']
    try:
        rest_snap_vm(vm_name,item)
        flash('Restore '+item+' done', category='success')
    except Exception as e:
        flash('Error restoring '+item+':'+str(e), category='danger')
    return redirect(url_for('backup'))

############################
##         BUILD          ##
############################

@app.route('/build',methods=['GET'])
@login_required
def build_lxc():
    return render_template('build.html', list_lxc_os=list_distrib(), list_profiles=get_os_profile_list(), list_net=conn.listNetworks(),list_iso = get_iso_list())

@app.route("/creation", methods=['POST'])
@login_required
def create_ct():
   lxc_ip = request.form['ip']
   try:
       create_lxc(request.form['nom'],request.form['os'])
       flash(request.form['nom']+' created', category='success')
   except Exception as e:
       flash('Error on creating '+request.form['nom']+':'+str(e), category='danger')
   if lxc_ip:
      set_lxc_ip(lxc_ip)
   return redirect(url_for('state'))

@app.route('/creationvm', methods=['POST'])
@login_required
def create_VM():
#VNC Version
    nom = request.form['vm_name']
    ram = request.form['ram']
    cpu = request.form['cpu']
    ose = request.form['os']
    iso = request.form['iso']
    iso = iso_path+iso
    net = request.form['net']
    disk = request.form['disk']
    opt = ''
    ostype = 'linux'

####################################
##         WINDOWS                ##
####################################
    if ose.startswith('win'):
        try:
            cmd = "qemu-img create -f qcow2 "+str(disk_path)+str(nom)+".qcow2 "+str(disk)+"G"
            subprocess.call(cmd, shell=True)
        except Exception as e:
            flash('Error on creating '+str(nom)+':'+str(e),category='danger')
            return redirect(url_for('state'))
        opt = " --disk path="+virtuo_path+virtuo_file+",device=cdrom"
        ostype = 'windows'
        creationcmd='--name '+str(nom)+' --ram '+str(ram)+' --disk path='+str(disk_path)+str(nom)+'.qcow2,bus=virtio,format=qcow2 --vcpus '+str(cpu)+' --os-type '+str(ostype)+' --os-variant '+str(ose)+' --network network:'+str(net)+' --graphics vnc,listen=0.0.0.0 --noautoconsole --console pty,target_type=serial '+opt+' --cdrom '+str(iso)+' --force --debug '
    else:
        creationcmd='--name '+str(nom)+' --ram '+str(ram)+' --disk path='+str(disk_path)+str(nom)+'.qcow2,size='+str(disk)+',bus=virtio --vcpus '+str(cpu)+' --os-type '+str(ostype)+' --os-variant '+str(ose)+' --network network:'+str(net)+' --graphics vnc,listen=0.0.0.0 --noautoconsole --console pty,target_type=serial '+opt+' --cdrom '+str(iso)+' --force --debug '
    try:
        os.system('virt-install '+creationcmd+' ')
        flash(str(nom)+' created', category='success')
    except Exception as e:
        flash('Error on creating '+str(nom)+':'+str(e),category='danger')
    return redirect(url_for('state'))


############################
##         STATE            ##
############################
@app.route('/state',methods=['GET'])
@login_required
def state():
    ips_lxc=[]
    for lxc_name in get_lxc_activ():
        ips_lxc.append(get_lxc_ip(lxc_name))
    activ_lxc=zip(get_lxc_activ(),ips_lxc)
    state_act_vm = []
    ips_vm = []
    for vm_name in get_vm_activ():
       state_act_vm.append(check_iso_is_mounted(vm_name))
       ips_vm.append(get_vm_ips(vm_name))
    activ_vm=zip(get_vm_activ(),state_act_vm,ips_vm)
    state_inact_vm = []
    for vm_name in get_vm_inactiv():
       state_inact_vm.append(check_iso_is_mounted(vm_name))
    inactiv_vm=zip(get_vm_inactiv(),state_inact_vm)
    return render_template('state.html', activ_vm=activ_vm, inactiv_vm=inactiv_vm,activ_lxc=activ_lxc,inactiv_lxc=get_lxc_inactiv())

############################
##         LXC            ##
############################
@app.route('/start_lxc',methods=['POST'])
@login_required
def startct():
    lxc_name = request.form['start']
    try:
        start_lxc(lxc_name)
        flash(lxc_name+' started', category='success')
    except Exception as e:
        flash('Error starting '+lxc_name+':'+str(e), category='danger')
    return redirect(url_for('state'))

@app.route('/stop_lxc',methods=['POST'])
@login_required
def stopct():
    lxc_name = request.form['stop']
    try:
        stop_lxc(lxc_name)
        flash(lxc_name+' stoped', category='success')
    except Exception as e:
        flash('Error stoping '+lxc_name+':'+str(e), category='danger')
    return redirect(url_for('state'))

@app.route('/destroy_lxc',methods=['POST'])
@login_required
def destroyct():
    lxc_name = request.form['destroy']
    try:
        destroy_lxc(lxc_name)
        flash(lxc_name+' destroyed', category='success')
    except Exception as e:
        flash('Error destroying '+lxc_name+':'+str(e), category='danger')
    return redirect(url_for('state'))

############################
##         VM             ##
############################
@app.route('/start_vm',methods=['POST'])
@login_required
def startvm():
    vm_name = request.form['start']
    try:
        start_vm(vm_name)
        flash(vm_name+' started', category='success')
    except Exception as e:
        flash('Error starting '+vm_name+':'+str(e), category='danger')
    return redirect(url_for('state'))

@app.route('/stop_vm',methods=['POST'])
@login_required
def stopvm():
    vm_name = request.form['stop']
    try:
        stop_vm(vm_name)
        flash(vm_name+' stoped', category='success')
    except Exception as e:
        flash('Error stoping '+vm_name+':'+str(e), category='danger')
    return redirect(url_for('state'))

@app.route('/destroy_vm',methods=['POST'])
@login_required
def destroyvm():
    vm_name = request.form['destroy']
    try:
        destroy_vm(vm_name)
        flash(vm_name+' destroyed', category='success')
    except Exception as e:
        flash('Error destroying '+vm_name+':'+str(e), category='danger')
    return redirect(url_for('state'))

############################
##         LOGIN          ##
############################
#Self certificate page
if __name__=='__main__':
#    atexit.register(cleanup)
    app.run(host=flask_config.host, port=flask_config.port, threaded=flask_config.thread, debug=flask_config.debug, ssl_context='adhoc')
