import sys, json
from threading import Thread

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QThread

from flask import Flask,render_template,Response, request, session, abort, flash, redirect,jsonify
from flask import send_file
from flaskext.mysql import MySQL

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
app.config['PORT']=5000
app.config['THREADED']=True
# app.config['DEBUG']=True 

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'rasberrydb'
app.config['MYSQL_DATABASE_HOST'] = '10.194.54.153:3306'
mysql.init_app(app)
conn = mysql.connect()

# class FlaskThread(QThread):
# 	def __init__(self, application, log):
# 		QThread.__init__(self)
# 		self.application = application
# 		self.log = log
				
# 		@app.route('/')
# 		def message():
# 			return 'OK'

# 	def __del__(self):
# 		self.wait()

# 	def run(self):
# 		self.log("Starting Flask Server....")
# 		self.application.run()

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self ,parent=None):
		super(MainWindow, self).__init__(parent)
		self.ui = uic.loadUi('serverGUI.ui', self)

		@app.route('/')
		def index():
			self.logMessage('Connected To Root.')
			return 'OK'

		@app.route('/send_message',methods=['POST'])
		def message():
			resp = {'status': 'OK'}
			try:
				cursor = conn.cursor()
				form = json.loads(request.data)
				print(form)
				cursor.execute('INSERT INTO clientmessages (Client, Message) VALUES (%(client)s,%(message)s)',form)
				conn.commit()
				self.clientMessage('Client: '+form['client']+", Message: "+form['message'])
			except:
				self.logMessage("Insertion Into Database Failed.")
				resp['status'] = 'FAIL'
			finally:
				cursor.close()
			return jsonify(resp)

	def __del__(self):
		print("Window Closed. Closed All Connections.")

	def logMessage(self,message):
		self.ui.LogsView.append(message)
		print(message)
	
	def clientMessage(self,message):
		self.ui.ClientMessages.append(message)

class GUIThread(QThread):
	def __init__(self):
		QThread.__init__(self)
	
	def run(self):
		app_q = QtWidgets.QApplication(sys.argv)
		window = MainWindow()
		window.show()
		sys.exit(app_q.exec_())

if __name__ == "__main__":
	print("Starting GUI Thread....")
	gui = GUIThread()
	gui.start()
	print("Starting Flask Server....")
	app.run(host='0.0.0.0')
	# sys.exit(app_q.exec_())