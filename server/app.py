import sys
import cv2
from flask import Flask,render_template,Response, request, session, abort, flash,redirect
from flask_socketio import SocketIO
from flaskext.mysql import MySQL
from camera import Camera
import threading
import pickle
import json as js

# PORT = 5000
# ROOT_URL = 'http://0.0.0.0:{}'.format(PORT)
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

camera=cv2.VideoCapture(0)

@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect('/login')
    else:
        return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login_user', methods=['POST','GET'])
def check_login():
    x = request.form['username']
    cursor.execute('select * from users where username = %(username)s',{'username':x})
    records = cursor.fetchall()
    pair = records[0]
    if request.form['password'] == pair[0]:
        session['username'] = x
        session['logged_in'] = True
    else:
        flash('wrong password!')
    return redirect('/')

@app.route('/signup_user', methods=['POST','GET'])
def do_user_signup():
    x = request.form['username']
    y = request.form['password']
    cursor.execute('INSERT INTO USERS VALUES (%s,%s)',(x,y))
    conn.commit()
    session['logged_in'] = True
    return redirect('/login')

@app.route('/logout', methods=['POST'])
def do_user_logout():
    session['logged_in'] = False
    return redirect('/login')

@app.route('/stream')
def stream():
    return render_template("stream.html")

@app.route('/streamuser')
def stream_user():
    return render_template("streamuser.html")

# def gen(camera):
#     while True:
#         frame = camera.get_frame()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def get_frame():
    camera_port=0
    # ramp_frames=100
    camera=cv2.VideoCapture(camera_port)
    while True:
        retval, im = camera.read()
        imgencode=cv2.imencode('.jpg',im)[1]
        data = pickle.dumps(imgencode, 0)
        size = len(data)
        stringData=imgencode.tostring()
        yield (b'--frame\r\n'
            b'Content-Type: text/plain\r\n\r\n'+stringData+b'\r\n')
    camera.release()
    del(camera)

def send_frame(camera):
    retval,im = camera.read()
    imgencode = cv2.imencode('.jpg',im)[1]
    stringData=imgencode.tostring()
    return stringData
   
@app.route('/video_feed')
def video_feed():
    return Response(get_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    log = 'received message:'+str(json)
    print(log)
    cursor.execute('INSERT INTO log VALUES (%s)',log)
    conn.commit()
    socketio.emit('my response', json, callback=messageReceived)

@socketio.on("send frame bundle")
def send_video(json, methods=['GET', 'POST']):
    log = 'Recording Started'
    print(log)
    cursor.execute('INSERT INTO log VALUES (%s)',log)
    conn.commit()
    socketio.emit('fr', {'data': send_frame(camera)})

@socketio.on("send each frame")
def send_each_frame(json, methods=['GET','POST']):
    socketio.emit('fr', {'data': send_frame(camera)},broadcast=True)
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
   socketio.run(app,host='0.0.0.0')
   # app.run()