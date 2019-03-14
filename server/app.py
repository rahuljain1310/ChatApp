import sys
import cv2
from flask import Flask,render_template,Response
from flask_socketio import SocketIO
from flaskext.mysql import MySQL
from camera import Camera
import threading
import pickle

PORT = 5000
ROOT_URL = 'http://localhost:{}'.format(PORT)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
app.config['PORT']=5000
# app.config['DEBUG']=True
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'Work'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
conn = mysql.connect()
cursor =conn.cursor()
socketio = SocketIO(app)

im = 0

@app.route('/')
def sessions():
    return render_template('index.html')

# @app.route('/agora')
# def agora():
#     return render_template("agora.html")

@app.route('/stream')
def stream():
    return render_template("stream.html")

# def gen(camera):
#     while True:
#         frame = camera.get_frame()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def get_frame():
    camera_port=0
    # ramp_frames=100
    camera=cv2.VideoCapture(camera_port)
    i=1
    while True:
        retval, im = camera.read()
        imgencode=cv2.imencode('.jpg',im)[1]
        # print(imgencode)
        data = pickle.dumps(imgencode, 0)
        # print(data)
        size = len(data)
        stringData=imgencode.tostring()
        print(stringData)
        yield (b'--frame\r\n'
            b'Content-Type: text/plain\r\n\r\n'+stringData+b'\r\n')
    camera.release()
    del(camera)


# def copy_frame():
#     while True:
#         imgencode=cv2.imencode('.jpg',im)[1]
#         stringData=imgencode.tostring()
#         yield (b'--frame\r\n'
#             b'Content-Type: text/plain\r\n\r\n'+stringData+b'\r\n')

def send_frame():
    camera=cv2.VideoCapture(0)
    i = 1
    while(i<=100):
        retval,im = camera.read()
        imgencode = cv2.imencode('.jpg',im)[1]
        stringData=imgencode.tostring()
        yield(stringData)
        i = i+1
    camera.release()
    del (camera)

@app.route('/video_feed')
def video_feed():
    for video_frame in send_frame():
        socketio.emit('my_video_frame', {'data': video_frame})
    # return Response(get_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route('/video_feed/<int:usr>')
# def video_feed_usr(usr):
#     return Response(copy_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')
    # if(usr==1):
        # return Response(get_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')
    # if(usr==2):
        # return Response(gen(Camera()),mimetype='multipart/x-mixed-replace; boundary=frame')


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    log = 'received message: ' + str(json)
    print(log)
    cursor.execute('INSERT INTO log VALUES (%s)',log)
    conn.commit()
    socketio.emit('my response', json, callback=messageReceived)

@socketio.on("send frame bundle")
def handke_user_connect(json, methods=['GET', 'POST']):
    log = 'Start Recording: '
    print(log)
    cursor.execute('INSERT INTO log VALUES (%s)',log)
    conn.commit()
    for video_frame in send_frame():
        print(video_frame)
        socketio.emit('fr', {'data': video_frame})

# =============================================================================
# class FlaskThread(QThread):
#     def __init__(self, application):
#         QThread.__init__(self)
#         self.application = application
#     def __del__(self):
#         self.wait()
#     def run(self):
#         socketio.run(self.application)
# =============================================================================
        
if __name__ == '__main__':    
    socketio.run(app)
    # app.run()
