import sys
import cv2
from flask import Flask,render_template,Response, request, session, abort, flash, redirect
from flask import send_file
from flask_socketio import SocketIO
from flaskext.mysql import MySQL
# from camera import Camera
import os
import threading
import random 
# import pickle
# import json as js

# PORT = 5000
# ROOT_URL = 'http://0.0.0.0:{}'.format(PORT)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
app.config['PORT']=5000
app.config['THREADED']=True
app.config['DEBUG']=True 
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
frames = [open(f + '.jpg', 'rb').read() for f in ['1', '2', '3']]

@app.route('/')
def home():
    if not session.get('logged_in'):
        print("Not Logged In. Redirecting ....")
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
    # y = request.form['player']
    cursor.execute('select distinct * from users where username = %(username)s',{'username':x})
    records = cursor.fetchall()
    pair = records[0]
    if request.form['password'] == pair[0]:
        session['username'] = x
        # session['player'] = y
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
    return redirect('/')

@app.route('/logout', methods=['POST'])
def do_user_logout():
    session['logged_in'] = False
    return redirect('/login') 

# Url for Download
@app.route('/download')
def download_files():
    return render_template("download.html")

# Api for Downloading Files
@app.route('/files/<filename>')
def downloadFile(filename):
    path = 'Download/'+filename
    folder = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(folder, path)
    return send_file(path, attachment_filename=filename,as_attachment=True)


@app.route('/stream')
def stream():
    if not session.get('logged_in'):
        return redirect('/login')
    return render_template("stream.html")

@app.route('/streamuser')
def stream_user():
    if not session.get('logged_in'):
        return redirect('/login')
    return render_template("streamuser.html")

# def gen(camera):
#     frame = camera.get_frame()
#     return frame

def camera_frame():
    return frames[random.randint(0,2)]

# def get_frame():
#     camera_port=0
#     # ramp_frames=100
#     camera=cv2.VideoCapture(camera_port)
#     while True:
#         retval, im = camera.read()
#         imgencode=cv2.imencode('.jpg',im)[1]
#         data = pickle.dumps(imgencode, 0)
#         size = len(data)
#         stringData=imgencode.tostring()
#         yield (b'--frame\r\n'
#             b'Content-Type: text/plain\r\n\r\n'+stringData+b'\r\n')
#     camera.release()
#     del(camera)

def send_frame():
    # camera=cv2.VideoCapture(0)
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
    for key, value in json.items():
        session['player'] = value
    player = session.get('player')
    log = 'Recording Started By Player: '+player
    print(log)
    cursor.execute('INSERT INTO log VALUES (%s)',log)
    conn.commit()
    print("Username of Player"+session.get('username'))
    if(player=='1'):
        socketio.emit('fr', {'user': player,'data': send_frame()},broadcast=True)
    if(player=='2'):
        # socketio.emit('fr', {'user': player,'data': gen(Camera())},broadcast=True)        
        socketio.emit('fr', {'user': player,'data': camera_frame()},broadcast=True)


@socketio.on("send each frame")
def send_each_frame(json, methods=['GET','POST']):
    player = session.get('player')
    try:
        print("Frame Broadcasted To the Client from Player: "+player)
    except:
        pass
    # print(player)
    if(player=='1'):
        socketio.emit('fr', {'user': player,'data': send_frame()},broadcast=True)
    if(player=='2'):
        ## TO send frame from Frame Array
        socketio.emit('fr', {'user': player,'data': camera_frame()},broadcast=True)  
        ## Use Send Frame to send frame from Camera
        # socketio.emit('fr', {'user': player,'data': send_frame()},broadcast=True)  

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