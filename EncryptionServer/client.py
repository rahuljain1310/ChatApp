from PyQt5 import QtCore, QtGui, QtWidgets, uic
from Encryptor import AES_Encryptor, Generate, Blowfish_Encryptor
import sys,random,cv2,os,requests
import socketio

#==========================================================================

# camera = None
camera = cv2.VideoCapture(0)
sio = socketio.Client()

# ==========================================================================

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self, socket ,parent=None):
		super(MainWindow, self).__init__(parent)
		self.ui = uic.loadUi('UI.ui', self)
		self.socket = socket
		self.username = ''
		self.setupSignal()

		@socket.on('connect')
		def on_connect():
			self.logMessage('connection established')

		@socket.on('disconnect')
		def on_disconnect():
			self.logMessage('connection terminated')

		@socket.on('get_frame')
		def get_frame():
			retval,im = camera.read()
			imgencode = cv2.imencode('.jpg',im)[1]
			stringData=imgencode.tostring()
			return stringData

		@socket.on('ping_by_user')
		def ping_by_user(json):
			print(json['message'])
			self.logMessage("Pinged By Another User.")

		socket.connect('http://localhost:5000')

	def __del__(self):
		print("Window Closed. Closed All Connections.")

	def setupSignal(self):
		self.setRandomKey()
		self.setUserName("User"+''.join(chr(random.randint(0x41, 0x50)) for i in range(4)))
		self.ui.UsernameInput.setText(self.username)

		## Connect
		self.ui.LoginButton.clicked.connect(self.login)
		self.ui.GenerateKeyButton.clicked.connect(self.setRandomKey)
		self.ui.EncryptFileButton.clicked.connect(self.encryptFile)
		self.ui.SendFileButton.clicked.connect(self.sendFile)
		self.ui.PingButton.clicked.connect(self.pingUsers)
		self.ui.ReceiveFileButton.clicked.connect(self.receiveFile)
		self.ui.DecryptFileButton.clicked.connect(self.decryptFile)
		self.ui.LoginButton.clicked.connect(self.login)

	def login(self):
		username = self.ui.UsernameInput.text()
		password = self.ui.PasswordInput.text()
		form = {'username': username, 'password': password}

	def logMessage(self,message):
		self.ui.LogsView.append(message)
		print(message)

	def setRandomKey(self):
		self.key = Generate.generateRandomKey()
		self.ui.InputKey.setText(Generate.generateRandomKey())

	def encryptFile(self):
		FileToEncrypt = QtWidgets.QFileDialog.getOpenFileName(None, 'Open Image', 'c:\\', 'Image files (*.jpg,*.gif, *.jpeg)')[0]
		if FileToEncrypt:
			if(self.ui.AES_Radio.isChecked()):
				aes = AES_Encryptor(self.InputKey.text(),self.logMessage)
				aes.encrypt_file(FileToEncrypt)
			elif (self.ui.BLOWFISH_Radio.isChecked()):
				bf = Blowfish_Encryptor(self.InputKey.text(),self.logMessage)
				bf.encrypt_file(FileToEncrypt)
			elif (self.ui.DES_Radio.isChecked()):
				pass
				# des = DES_Encryptor(self.InputKey.text())
				# des.encrypt_file(FileToEncrypt)
		else:
			self.logMessage("No File For Encryption Selected.")
			
	def decryptFile(self):
		FileToDecrypt = QtWidgets.QFileDialog.getOpenFileName(None, 'Open Encrypted File', 'c:\\', 'All Files (*)')[0]
		if FileToDecrypt:
			if(self.ui.AES_Radio.isChecked()):
				aes = AES_Encryptor(self.InputKey.text(),self.logMessage)
				aes.decrypt_file(FileToDecrypt[0])
			elif (self.ui.BLOWFISH_Radio.isChecked()):
				bf = Blowfish_Encryptor(self.InputKey.text(),self.logMessage)
				bf.decrypt_file(FileToDecrypt)
			elif (self.ui.DES_Radio.isChecked()):
				pass
				# des = DES_Encryptor(self.InputKey.text())
				# des.encrypt_file(FileToEncrypt)
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
		FileToReceive = 'trial1.jpeg'
		if(FileToReceive):
			with open(FileToReceive, 'wb') as f:
				r = requests.get('http://localhost:5000/download/trial.jpeg')
				f.write(r.content)
				f.close()
					
if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	window = MainWindow(sio)
	window.show()
	while app.exec_()==None:
		pass
	sio.disconnect()
	sys.exit()
	# sys.exit(app.exec_())
