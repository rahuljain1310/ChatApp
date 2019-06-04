import socketio
import asyncio
import cv2
sio = socketio.Client()
camera = None
active = False

@sio.on('connect')
def on_connect():
    print('connection established')

@sio.on('start sending video')
def start_sending_video():
    active = True
    camera = cv2.VideoCapture(0)

@sio.on('stop sending video')
def stop_sending_video():
    active = False
    camera = None


@sio.on('Send Frame')
def send_frame():
    retval,im = camera.read()
    imgencode = cv2.imencode('.jpg',im)[1]
    stringData=imgencode.tostring()
    return stringData

@sio.on('my message')
def on_message(data):
    print('message received with ', data)
    sio.emit('my response', {'response': 'my response'})
  
@sio.on('disconnect')
def on_disconnect():
    print('disconnected from server')
  
# def connectClient():
sio.connect('http://localhost:5000')
sio.emit('test message',{'hello':'hi'})
# print('my sid is', sio.sid)
# sio.wait()

# @sio.on('connect')
# def on_connect():
#     print('I\'m connected!')

# @sio.on('start_video')
# async def start_video():
#     camera = cv2.VideoCapture(0)
#     retval,im = camera.read()
#     imgencode = cv2.imencode('.jpg',im)[1]
#     stringData=imgencode.tostring()
#     sio.emit('frame',{frame: stringData})

# @sio.on('send_frame')
# async def send_frame():
#     retval,im = camera.read()
#     imgencode = cv2.imencode('.jpg',im)[1]
#     stringData=imgencode.tostring()
#     sio.emit('frame',{frame: stringData})

# from socketIO_client import SocketIO, LoggingNamespace

# def on_aaa_response(args):
#     print('on_aaa_response', args['data'])

# socketIO = SocketIO('0.0.0.0', 5000, LoggingNamespace)
# socketIO.on('aaa_response', on_aaa_response)
# socketIO.emit('aaa')
# socketIO.wait(seconds=1)

# from socketio_client.manager import Manager
# from gevent import monkey
# monkey.patch_socket()

# io = Manager('0.0.0.0', 5000)
# chat = io.socket('/chat')

# @chat.on_connect()
# def chat_connect():
#     chat.emit("Hello")

# @chat.on('welcome')
# def chat_welcome():
#     chat.emit("Thanks!")

# io.connect()
# gevent.wait()



