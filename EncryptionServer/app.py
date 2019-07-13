import sys
import cv2
import os
import threading
import random 
import json
import rsa, pickle
from werkzeug.utils import secure_filename

from passlib.hash import pbkdf2_sha256
hasher = pbkdf2_sha256.using(rounds=12856)

from flask import Flask,render_template,Response, request, session, abort, flash, redirect,jsonify
from flask import send_file
from flask_socketio import SocketIO
from flaskext.mysql import MySQL

##----------------------------------------------------------------------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjk43534nfl1232#'
app.config['PORT']=5000
app.config['THREADED']=True
# app.config['DEBUG']=True 

##----------------------------------------------------------------------------------------

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'EncryptionWork'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
conn = mysql.connect()
cursor =conn.cursor()
socketio = SocketIO(app)

publicKeyDict = {}

##========================================================================================
## Utility Functions
##========================================================================================

def logRecord(log):
  cur = conn.cursor()
  try:
    cur.execute('INSERT INTO LOGS(record) VALUES (%s)',log)
    conn.commit()
    print(log)
  except:
    print("Log Unsuccessful: "+log)
  finally:
    cur.close()

def logAndResponse(log):
  logRecord(log)
  return "Response: "+log

##========================================================================================
## Mark Session Functions
##========================================================================================

def checkUsername(x):
    x = x.strip()
    if(x.find(';')!=-1 or x==''):
        x = "Error"
    return x

def MarkUserSessionLogin(x):
  session['username'] = x
  session['logged_in'] = True
  logRecord("Username: "+x+" logged in.")

def MarkUserSignup(x):
  session['username'] = x
  session['logged_in'] = True
  logRecord("Username: "+x+" signed in.")

def MarkUserlogout(x):
  session['username'] = ''
  session['logged_in'] = False
  logRecord("Username: "+x+" logged out.")


##========================================================================================
## Route User Login,Sign-up,Logout URL
##========================================================================================

@app.route('/')
def home():
  if not session.get('logged_in'):
    print("Not Logged In. Redirecting ....")
    return redirect('/login')
  else:
    return render_template('index.html')

@app.route('/signup')
def signup_page():
  return render_template('signup.html')

@app.route('/login')
def login_page():
  session['logged_in'] = False
  session['username'] = ''
  return render_template('login.html')

@app.route('/logout')
def do_user_logout():
  return redirect('/login') 

## User Login/Signup API's ----------------------
@app.route('/login_user', methods=['POST','GET'])
def do_user_login():
  x = request.form['username'].strip()
  y = request.form['password'].strip()
  x = checkUsername(x)
  if(x=="Error"):
    flash('Username Invalid!')
    redirect('/login') 
  cursor = conn.cursor()
  cursor.execute('SELECT * FROM UserLogin WHERE USERNAME = %(username)s',{'username':x})
  records = cursor.fetchone()
  cursor.close()
  try:
    if (hasher.verify(y,records[2])):
      MarkUserSessionLogin(x)
      return redirect('/')
    else:
      flash('wrong password!')
  except:
      print("User with username "+x+" does not exist.")
  return redirect('/login')

@app.route('/signup_user', methods=['POST','GET'])
def do_user_signup():
  form_elements = request.form.copy()
  x = form_elements['username'].strip()
  y = form_elements['password'].strip()
  x = checkUsername(x)
  if(x=="Error"):
    flash('Username Invalid!')
    return redirect('/signup')
  form_elements['password'] = hasher.hash(y)
  print(form_elements['password'])
  form_elements['username'] = x
  cursor = conn.cursor()
  cursor.execute('SELECT DISTINCT * FROM USERLOGIN WHERE username = (%s)',x)
  records = cursor.fetchall()
  cursor.close()
  if(len(records)>=1):
    redirect('/signup')
  else:
    curr = conn.cursor()
    try:
      curr.execute('INSERT INTO USERLOGIN (Username, Password, Firstname, Lastname, EmailId ) VALUES (%(username)s,%(password)s,%(firstname)s,%(lastname)s,%(email)s)',form_elements)
      conn.commit()
      curr.close()
      MarkUserSignup(x)
    except:
      print("Signup failed.")
    finally:
      curr.close()
      return redirect('/')

@app.route('/login_user_exe',methods=['POST'])
def exe_user_login():
  form = json.loads(request.data)
  x = form['username'].strip()
  y = form['password'].strip()
  x = checkUsername(x)
  if(x=="Error"):
    return jsonify({'status': logAndResponse("Username Invalid")})
  cursor = conn.cursor()
  cursor.execute('SELECT * FROM UserLogin WHERE USERNAME = %(username)s',{'username':x})
  records = cursor.fetchone()
  cursor.close()
  try:
    if (hasher.verify(y,records[2])):
      return jsonify({'status':'OK','code':200})
    else:
      return jsonify({'status': logAndResponse('Login Attempt Failed: User with username '+x+ 'does not exist.'),'code':404})
  except:
      return jsonify({'status': logAndResponse("Login Attempt Failed: User with username "+x+" does not exist."),'code':404})
  return jsonify({'status': logAndResponse('Login Attempt Failed.'),'code':404})

##========================================================================================
## Socket Functions
##========================================================================================

@socketio.on('connect')
def connect():
  logRecord("User Connected")

@socketio.on('disconnect')
def disconnect():
  logRecord("User Disconnected")

@socketio.on('ping')
def ping():
  logRecord("Ping Request By User. Emitting Ping.")
  socketio.emit('ping_by_user', {'message': 'Ping Request By Another User'} ,include_self=False)

@socketio.on('public_key')
def setPublicKey(data):
  key = data['key']
  user = data['user']
  publicKeyDict[user] = key
  # print(publicKeyDict)

@socketio.on('encryptKey')
def transferEncryptKey(data):
  print(data)
  socketio.emit('RSAencryptedKey',data,broadcast=True)

@socketio.on('sendframe')
def sendframe(data):
  # print('rec_frame')
  socketio.emit('frame_server',data)


@socketio.on('send_file_client')
def sendFileClient():
  pass

@socketio.on('receive_file_client')
def receiveFileClient():
  pass

##=======================================================================================
## API for UPLOAD / DOWNLOAD
##=======================================================================================

@app.route('/download/<filename>')
def receive_file(filename):
  folder = os.path.dirname(os.path.abspath(__file__))
  path = os.path.join(folder, filename)
  return send_file(path, attachment_filename='download.jpeg',as_attachment=True)

@app.route('/upload',methods=['POST'])
def upload_file():
  print(request.method)
  if request.method == 'POST':
    if 'file' in request.files:
      _file = request.files['file']
      if _file.filename!='':
        filename = _file.filename
        _file.save(secure_filename(filename))
        return logAndResponse("File: "+filename+" uploaded to server.")
      else:
        return logAndResponse("Upload Failed as fileName string empty.")
    else:
      return logAndResponse('Absent File Key in Json Data.')
  else:
    return logAndResponse("Not a 'POST' method.")

##=======================================================================================
## RSA Public Keys
##=======================================================================================

@app.route('/publicKey',methods=['GET'])
def publicKey():
  user = request.args['user']
  return jsonify({'key': publicKeyDict[user]})

##=======================================================================================
## Main Function
##=======================================================================================


@app.route('/')
def index():
  return 'Please Use Client Application To Use The File ..'

if __name__ == '__main__':    
  socketio.run(app,host='0.0.0.0')
