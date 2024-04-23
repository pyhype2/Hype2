from config import *
import base64

def get_screenshot(vm_name):
  dom = conn.lookupByName(vm_name)
  stream = conn.newStream()
  imageType = dom.screenshot(stream,0)
  file = "tmp_screen_" + dom.name()
  fileHandler = open(file, 'wb')
  streamBytes = stream.recv(262120)
  while streamBytes != b'':
    fileHandler.write(streamBytes)
    streamBytes = stream.recv(262120)
  fileHandler.close()
  print('Screenshot saved as type: ' + imageType)
  stream.finish()
  with open(file, "rb") as f:
    data = base64.b64encode(f.read())
  os.remove(file)
  return data
