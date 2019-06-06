import sys
import cv2
import os
import threading

from contextlib import closing
from passlib.hash import pbkdf2_sha256

from flask import Flask,render_template,Response, request, session, abort, flash, redirect,send_file
from flask_socketio import SocketIO
from flask_socketio import join_room, leave_room
from flaskext.mysql import MySQL

app = Flask(__name__)
# app = Flask(__name__, static_folder="./chatapphome/build/static", template_folder="./chatapphome/build")
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
app.config['PORT'] = 5000
app.config['THREADED'] = True
app.config['ssl_context'] = 'adhoc'
app.config['DEBUG']=True 

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'Work'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
conn = mysql.connect()

hasher = pbkdf2_sha256.using(rounds=12856)

socketio = SocketIO(app)
clients = {}


## Use better measures for checking Usernames
def checkUsername(x):
    x = x.strip()
    if(x.find(';')!=-1 or x==''):
        x = "Error"
    return x

## Mark Down Functions
def MarkUserSessionLogin(x):
    session['username'] = x
    session['logged_in'] = True
    log = "Username: "+x+" logged in."
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO LOGS(record) VALUES (%s)',log)
        conn.commit()
        print(log)
    except:
        print("User login unsuccessful.")
    finally:
        cur.close()

def MarkUserSignup(x):
    session['username'] = x
    session['logged_in'] = True
    log = "Username: "+x+" signed in."
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO LOGS(record) VALUES (%s)',log)
        conn.commit()
        print(log)
    except:
        print("User signup unsuccessful.")
    finally:
        cur.close()

def MarkUserlogout(x):
    session['username'] = ''
    session['logged_in'] = False
    log = "Username: "+x+" logged out."
    print(log)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO LOGS(record) VALUES (%s)',log)
    conn.commit()
    cursor.close()

## Route User Login,Sign-up,Logout URL

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

## User Login/Signup API's
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
    print(hasher.verify(y,records[2]))
    try:
        print(records)
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
        except:
            print("Signup failed.")
        finally:
            curr.close()
        MarkUserSignup(x)
        return redirect('/')

# Url for Download
@app.route('/download')
def download_files():
    return render_template("download.html")

@app.route('/files/<filename>')
def downloadFile(filename):
    path = 'Download/'+filename
    folder = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(folder, path)
    return send_file(path, attachment_filename=filename,as_attachment=True)

## Convenience Functions
def log(arguments):
    array = ['Message from server:']
    array.append(array, arguments)
    socketio.emit('log', array)

## Socket Communication
@socketio.on('connect')
def connect():
    print("Client Connected")
    # socketio.emit('log',"Another Client Connected To The Server")

@socketio.on('message')
def message(json):
    print("Client said: "+str(json))
    socketio.emit('message', json, include_self=False)

@socketio.on('create or join')
def create_or_join(room):
    print('Received request to create or join room '+str(room))
    numClients = 0
    try:
        room_clients = clients[room]
        numClients = len(room_clients)
    except:
        numClients = 0
    if(numClients==0):
        join_room(room)
        clients[room] = [request.sid] 
        print("NEW ROOM: "+str(request.sid)+" Created room: "+str(room))
        socketio.emit('created',room,room=room)
    elif (numClients==1 or numClients==2):
        join_room(room)
        clients[room].append(request.sid)
        socketio.emit('join',{'room':room, 'numClients': numClients+1}, room=room,include_self=False)
        print("EXISTING ROOM: "+str(request.sid)+ "Joined room: "+str(room))
        socketio.emit('joined',{'room':room, 'roomid': numClients+1,'numClients': numClients+1},room=room)
    else:
        socketio.emit('full',room)
    print(clients)

@socketio.on('bye')
def bye():
    print("Receieved Bye from Client")

if __name__ == '__main__':    
   socketio.run(app,host='0.0.0.0')