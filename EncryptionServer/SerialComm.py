import sys, glob
import serial

def get_serial_ports():
  if sys.platform.startswith('win'):
    ports = ['COM%s' % (i + 1) for i in range(256)]
  elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
    ports = glob.glob('/dev/tty[A-Za-z]*')  # this excludes your current terminal "/dev/tty"
  elif sys.platform.startswith('darwin'):
    ports = glob.glob('/dev/tty.*')
  else:
    raise EnvironmentError('Unsupported platform')

  result = []
  for port in ports:
    try:
      s = serial.Serial(port)
      s.close()
      result.append(port)
    except (OSError, serial.SerialException):
      pass
  return result

def check_serial_status(port):
  if port == None or port == 'None':
    return False
  try:
    s = serial.Serial(port)
    s.close()
    return True
  except:
    return False