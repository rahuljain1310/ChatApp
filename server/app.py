import sys
from flask import Flask,render_template
from flask_socketio import SocketIO
from flaskext.mysql import MySQL


PORT = 5000
ROOT_URL = 'http://localhost:{}'.format(PORT)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
app.config['PORT']=5000
# =============================================================================
# app.config['DEBUG']=True
# =============================================================================
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'Work'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
conn = mysql.connect()
cursor =conn.cursor()

socketio = SocketIO(app)

@app.route('/')
def sessions():
    return render_template('index.html')

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    log = 'received message: ' + str(json)
    print(log)
    cursor.execute('INSERT INTO log VALUES (%s)',log)
    conn.commit()
    socketio.emit('my response', json, callback=messageReceived)

# =============================================================================
# class Example(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.initUI()    
#     def initUI(self):               
#         qbtn = QPushButton('Quit', self)
#         qbtn.clicked.connect(QApplication.instance().quit)
#         qbtn.resize(qbtn.sizeHint())
#         qbtn.move(50, 50)       
#         self.setGeometry(300, 300, 250, 150)
#         self.setWindowTitle('Quit button')    
#         self.show()
#     
# =============================================================================

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
    
# =============================================================================
# def provide_GUI_for(application):
#     qtapp = QApplication(sys.argv)
#     webapp = FlaskThread(application)
#     webapp.start()
#     qtapp.aboutToQuit.connect(webapp.terminate)
#     webview = QWebEngineView()
#     webview.load(QUrl(ROOT_URL))
#     webview.show()
#     return qtapp.exec_()
# =============================================================================
        
if __name__ == '__main__':    
    socketio.run(app)
# =============================================================================
#     webapp = FlaskThread(app)
#     webapp.start()
#     qtapp.aboutToQuit.connect(webapp.terminate)
# =============================================================================
# =============================================================================
#     webview = QWebEngineView()
#     webview.load(QUrl(ROOT_URL))
#     webview.show()
#     sys.exit(qtapp.exec_())
# 
# =============================================================================
