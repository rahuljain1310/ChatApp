from PyQt5 import QtCore, QtGui, QtWidgets, uic
from Encryptor import AES_Encryptor, Generate, Blowfish_Encryptor, DES_Encryptor, UIFunctions
import sys,random,cv2,os,requests
import socketio
import json
import threading
from serial import Serial
import time


##=====================================================================================================================
## Initializations 
##=====================================================================================================================

class UserDetails():
	Username = 'Username'
	UserID = -1
	UserState = 'Logged_Off'
	EnableLocalStreaming = True

	@staticmethod
	def getUsername():
		return UserDetails.Username
	
	@staticmethod
	def getUserID():
		return UserDetails.UserID
	
	@staticmethod
	def getUserState():
		return UserDetails.UserState
	
class FPGADetails():
	BaudRate = 9600
	PORT = 'COM3'
##=====================================================================================================================
## Local Stream Thread 
##=====================================================================================================================

class LocalStream(threading.Thread):
	def __init__(self, camID, videoframe, encBox):
		threading.Thread.__init__(self)
		self.camID = camID
		self.videoFrame = videoframe
		self.encryptBox = encBox
	def run(self):
		print("Starting Local Stream")
		camera=cv2.VideoCapture(self.camID)
		while True:
			retval,im = camera.read()
			imgencode = cv2.imencode('.jpg',im)[1]
			stringData=imgencode.tostring()
			# self.encryptBox.setText(str(stringData))
			pixmap = QtGui.QPixmap()
			pixmap.loadFromData(imgencode,'JPG')
			self.videoFrame.setPixmap(pixmap)
			if not UserDetails.EnableLocalStreaming:
				break
		return

##=====================================================================================================================
## Login Dialog Box
##=====================================================================================================================

class Login(QtWidgets.QDialog):
	def __init__(self, parent=None):
		super(Login, self).__init__(parent)
		self.lui = uic.loadUi('Login.ui', self)
		self.LoginButton.clicked.connect(self.handleLogin)

	def handleLogin(self):
		print('Login Successful')
		form = {
			'username': self.lui.UsernameInput.text(),
			'password': self.lui.PasswordInput.text(),
		}
		r = requests.post('http://localhost:5000/login_user_exe',json=form)
		result = json.loads(r.content)
		if(result['code']==200):
			UserDetails.Username = form['username']
			UserDetails.UserState = 'Logged_In'
			self.accept()
		else:
			QtWidgets.QMessageBox.warning(self, 'Error', 'Incorrect Username or Password.')

# class FPGAKey(QtWidgets.QDialog):
# 	def __init__(self, parent=None):
# 		super(FPGAKey, self).__init__(parent)
# 		self.fui = uic.loadUi(']FPGAKey.ui', self)
# 		self.fui.buttonBox.OK.clicked.connect(self.handleOK)

# 	def handleOK(self):
# 		self.accept()

##=====================================================================================================================
## MainWindow 
##=====================================================================================================================

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self, socket ,parent=None):
		super(MainWindow, self).__init__(parent)
		self.ui = uic.loadUi('UI.ui', self)
		self.socket = socket
		self.setupSignal()
		# self.localStream = LocalStream(0,self.ui.LocalVideoStream,self.ui.EncryptedFrame)
		# self.localStream.start()

		@socket.on('connect')
		def on_connect():
			self.logMessage('connection established')

		@socket.on('disconnect')
		def on_disconnect():
			self.logMessage('connection terminated')

		@socket.on('ping_by_user')
		def ping_by_user(json):
			print(json['message'])
			self.logMessage("Pinged By Another User.")

		socket.connect('http://localhost:5000')

	def __del__(self):
		print("Window Closed. Closed All Connections.")

	def setupSignal(self):
		self.setRandomKey()
		self.setUserName(UserDetails.getUsername())
		UIFunctions.log = self.logMessage
		UIFunctions.encryptTextBox = self.ui.EncryptedText

		## Connect
		self.ui.GenerateKeyButton.clicked.connect(self.setRandomKey)
		self.ui.EncryptFileButton.clicked.connect(self.encryptFile)
		self.ui.SendFileButton.clicked.connect(self.sendFile)
		self.ui.PingButton.clicked.connect(self.pingUsers)
		self.ui.ReceiveFileButton.clicked.connect(self.receiveFile)
		self.ui.DecryptFileButton.clicked.connect(self.decryptFile)
		self.ui.ReadFPGA.clicked.connect(self.readKeyFPGA)

	def setRandomKey(self):
		self.ui.InputKey.setText(Generate.generateRandomKey())
	
	def logMessage(self,message):
		self.ui.LogsView.append(message)
		print(message)

	def CheckExtension(self,f,ext):
		if f.lower().endswith(ext):
			return True
		self.logMessage("Selected file is not "+ext+" file type.")
		return False

	def readKeyFPGA(self):
		self.logMessage('Reading Key from FPGA ...')
		ser = Serial('COM7', 128000, timeout=2)
		time.sleep(2)
		ser.write(b'A')
		key = ser.read(100)
		ser.close()
		if (type(key)==bytes and len(key)>0):
			print(key)
			print(len(key))
			keytrun = Generate.truncateEnd(key)
			print(keytrun)
			print(len(keytrun))
			self.ui.InputKey.setText(keytrun.decode())
			self.logMessage('Key Reading From FPGA Completed.')
		else:
			self.logMessage('Reading Key from FPGA Failed')

	def encryptFile(self):
		FileToEncrypt = QtWidgets.QFileDialog.getOpenFileName(None, 'Open Image', 'c:\\', 'All Files (*.*)')[0]
		if FileToEncrypt:
			if(self.ui.AES_Radio.isChecked()):
				aes = AES_Encryptor(self.InputKey.text())
				aes.encrypt_file(FileToEncrypt)
			elif (self.ui.BLOWFISH_Radio.isChecked()):
				bf = Blowfish_Encryptor(self.InputKey.text())
				bf.encrypt_file(FileToEncrypt)
			elif (self.ui.DES_Radio.isChecked()):
				pass
				des = DES_Encryptor(self.InputKey.text())
				des.encrypt_file(FileToEncrypt)
			else:
				self.logMessage('No Method For Encryption Selected.')
		else:
			self.logMessage("No File For Encryption Selected.")
			
	def decryptFile(self):
		FileToDecrypt = QtWidgets.QFileDialog.getOpenFileName(None, 'Open Encrypted File', 'c:\\', 'All Files (*.*)')[0]
		if FileToDecrypt:
			if(self.ui.AES_Radio.isChecked()):
				if not self.CheckExtension(FileToDecrypt,'.aes'):
					return
				aes = AES_Encryptor(self.InputKey.text())
				aes.decrypt_file(FileToDecrypt)
			elif (self.ui.BLOWFISH_Radio.isChecked()):
				if not self.CheckExtension(FileToDecrypt,'.blf'):
					return
				bf = Blowfish_Encryptor(self.InputKey.text())
				bf.decrypt_file(FileToDecrypt)
			elif (self.ui.DES_Radio.isChecked()):
				if not self.CheckExtension(FileToDecrypt,'.des'):
					return
				des = DES_Encryptor(self.InputKey.text())
				des.decrypt_file(FileToDecrypt)
		else:
			self.logMessage("No File For Decryption Selected.")

	def setUserName(self,text):
		self.username = text
		self.ui.UsernameInput.setText(text)

	def sendMessageAndLog(self,message):
		self.logMessage('Message Sent To User: '+str(message))
		self.socket.emit('message',message)

	def pingUsers(self):
		self.logMessage("User Pinged To Other Users.")
		self.socket.emit('ping')

	def sendFile(self):
		FileToSend = QtWidgets.QFileDialog.getOpenFileName(None, 'Open Image', 'c:\\', 'Image files (*.jpg,*.gif, *.jpeg)')
		if(FileToSend[0]):
			with open(FileToSend[0], 'rb') as f:
				r = requests.post('http://localhost:5000/upload', files={'file': f})
				self.logMessage(r.text)
				self.socket.emit('offer_file',{'type':'file_send','filename':FileToSend[0]})

	def receiveFile(self):
		FileToReceive = self.ui.FileInput.text()
		NewFileName = self.ui.NewFileInput.text()
		self.logMessage("Receiving File: "+FileToReceive)
		if(FileToReceive):
			with open(NewFileName, 'wb') as f:
				r = requests.get('http://localhost:5000/download/'+FileToReceive)
				f.write(r.content)
				f.close()
			self.logMessage("File Received with name: "+NewFileName)
		else:
			self.logMessage("No input to the receive file field.")
##=====================================================================================================================
## Main Function 
##=====================================================================================================================

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	login = Login()
	if login.exec_() == QtWidgets.QDialog.Accepted:
		sio = socketio.Client()
		window = MainWindow(sio)
		window.show()
		while app.exec_()==None:
			pass
		sio.disconnect()
		UserDetails.EnableLocalStreaming = False
		sys.exit()
		# sys.exit(app.exec_())
