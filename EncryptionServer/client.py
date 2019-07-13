import json
import os
import random
import sys
import threading
import time
import pickle
import base64
import numpy

import cv2
import requests
import socketio
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from serial import Serial
from Crypto.Cipher import AES, Blowfish

import rsa
from Encryptor import (AES_Encryptor, Blowfish_Encryptor, DES_Encryptor, Generate, UIFunctions)
from SerialComm import get_serial_ports

##=====================================================================================================================
## Initializations 
##=====================================================================================================================

class UserDetails():
	Username = 'Username'
	UserID = -1
	UserState = 'Logged_Off'
	EnableLocalStreaming = False
	EnableRemoteStreaming = False

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

class RSACommunication():
	PrivateKey = None
	PublicKey = None
	
	@staticmethod
	def generatePairs():
		(pubkey, privkey) = rsa.newkeys(512)
		RSACommunication.PrivateKey = privkey
		RSACommunication.PublicKey = pubkey

	@staticmethod
	def encrypt_message(message,user):
		rsa_public_key = RSACommunication.getUserPublicKey(user)
		message_bytes = message.encode('utf-8')
		encrypted_message = rsa.encrypt(message_bytes, rsa_public_key)
		return encrypted_message

	@staticmethod
	def decrypt_message(message_bytes):
		return rsa.decrypt(message_bytes, RSACommunication.PrivateKey)

	@staticmethod
	def getUserPublicKey(user):
		UIFunctions.log("Fetching Public Key For User: "+ user)
		URL = "http://localhost:5000/publicKey"
		r = requests.get(url = URL, params = {'user': user} ) 
		x = json.loads(r.content)
		bytes_key = x['key'].encode()
		publicKey = pickle.loads(bytes_key)
		UIFunctions.log('Public Key Received For User: '+user)
		return publicKey

##=====================================================================================================================
## Local Stream Thread 
##=====================================================================================================================

class LocalStream(threading.Thread):
	def __init__(self, camID, videoframe, encBox, socket):
		threading.Thread.__init__(self)
		self.camID = camID
		self.videoFrame = videoframe
		self.encryptBox = encBox
		self.socket = socket
	
	def run(self):
		UIFunctions.log("Starting Local Stream")
		camera=cv2.VideoCapture(self.camID)
		while UserDetails.EnableLocalStreaming:
			retval,im = camera.read()
			imgencode = cv2.imencode('.jpg',im)[1]
			# self.socket.emit('sendframe',{'frame': imgencode.tolist(),'user': UserDetails.Username})
			# stringData=imgencode.tostring()
			pixmap = QtGui.QPixmap()
			pixmap.loadFromData(imgencode,'JPG')
			self.videoFrame.setPixmap(pixmap)
			if not UserDetails.EnableLocalStreaming:
				break
		camera.release()
		UIFunctions.log('Stream Stopped.')		
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

##=====================================================================================================================
## MainWindow 
##=====================================================================================================================

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self, socket ,parent=None):
		super(MainWindow, self).__init__(parent)
		self.ui = uic.loadUi('UI.ui', self)
		self.socket = socket
		self.camera = None
	
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

		@socket.on('frame_server')
		def set_frame(data):
			# print('received_frame')
			encrpt = AES.new(self.ui.InputKey.text().encode(),AES.MODE_ECB)
			encodeframe = encrpt.decrypt(data['frame'])
			encodeframe = encodeframe[0:data['length']]
			pixmap = QtGui.QPixmap()
			pixmap.loadFromData(encodeframe,'JPG')
			self.ui.LocalVideoStream.setPixmap(pixmap)
			if UserDetails.EnableRemoteStreaming == True:
				_,im = self.camera.read()
				imgencode = cv2.imencode('.jpg',im)[1].tostring()
				origsize = len(imgencode)
				encrpt = AES.new(self.ui.InputKey.text().encode(),AES.MODE_ECB)
				imgencode += (' '*(16-origsize%16)).encode()
				encodeframe = encrpt.encrypt(imgencode)
				self.socket.emit('sendframe',{'frame': encodeframe,'length': origsize})
				
		@socket.on('RSAencryptedKey')
		def RSAEcnryptedKey(data):
			print(data)
			if(data['user']==UserDetails.getUsername()):
				self.logMessage('Received Json From User: '+data['from'])
				keyEncoded = bytes.fromhex(data['key'])
				decryptedKey = RSACommunication.decrypt_message(keyEncoded)
				self.ui.InputKey.setText(decryptedKey.decode())
				self.logMessage('Received Encryption Key From User: '+data['from'])

		socket.connect('http://localhost:5000')

		self.setupSignal()

	def __del__(self):
		print("Window Closed. Closed All Connections.")

	def setupSignal(self):
		self.setRandomKey()
		self.setUserName(UserDetails.getUsername())

		## Set Up RSA And Send Public Key To Server
		RSACommunication.generatePairs()
		key = pickle.dumps(RSACommunication.PublicKey,0)
		keyuser = {'key': key.decode(), 'user': UserDetails.Username}
		# self.logMessage(str(keyuser))
		self.logMessage('Public Key Generated And Send To The Server.')
		self.socket.emit('public_key',keyuser)

		## Global Gui Widgets
		UIFunctions.log = self.logMessage
		UIFunctions.encryptTextBox = self.ui.EncryptedText

		## Set COM Ports for Connection
		ports = get_serial_ports()
		for port in ports:
			self.ui.PortsCombo.addItem(port)
		if len(ports)==0:
			self.ui.PortsCombo.addItem('None')
		
		## Connect
		#-- drop downs
		self.ui.PortsCombo.activated[str].connect(self.setPort)
		self.ui.BaudRateCombo.activated[str].connect(self.setBaudRate)
		#-- clicks
		self.ui.SendStream.clicked.connect(self.startSendFrame)
		self.ui.EndStream.clicked.connect(self.stopSendFrame)
		self.ui.SendKeyButton.clicked.connect(self.sendKeyThroughRSA)
		self.ui.GenerateKeyButton.clicked.connect(self.setRandomKey)
		self.ui.EncryptFileButton.clicked.connect(self.encryptFile)
		self.ui.SendFileButton.clicked.connect(self.sendFile)
		self.ui.PingButton.clicked.connect(self.pingUsers)
		self.ui.ReceiveFileButton.clicked.connect(self.receiveFile)
		self.ui.DecryptFileButton.clicked.connect(self.decryptFile)
		self.ui.ReadFPGA.clicked.connect(self.readKeyFPGA)
		self.ui.StopLocalStream.clicked.connect(self.stopLocalStream)
		self.ui.StartLocalStream.clicked.connect(self.startLocalStream)

	def startSendFrame(self):
		UserDetails.EnableLocalStreaming = False
		UserDetails.EnableRemoteStreaming = True
		self.camera = cv2.VideoCapture(0)
		self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
		self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
		_,im = self.camera.read()
		imgencode = cv2.imencode('.jpg',im)[1].tostring()
		origsize = len(imgencode)
		imgencode += (' '*(16-origsize%16)).encode()
		encrpt = AES.new(self.ui.InputKey.text().encode(),AES.MODE_ECB)
		encodeframe = encrpt.encrypt(imgencode)
		self.socket.emit('sendframe',{'frame': encodeframe,'length': origsize})
		
	def stopSendFrame(self):
		UserDetails.EnableRemoteStreaming = False
		self.camera.release()

	def stopLocalStream(self):
		self.logMessage('Attempting End Call ...')
		UserDetails.EnableLocalStreaming = False
		print(UserDetails.EnableLocalStreaming)

	def startLocalStream(self):
		self.logMessage('Attempting Start Call ...')
		UserDetails.EnableLocalStreaming = True
		self.localStream = LocalStream(0,self.ui.LocalVideoStream,self.ui.EncryptedFrame, self.socket)
		self.localStream.start()

	def sendKeyThroughRSA(self):
		key = self.ui.InputKey.text()
		user = self.ui.KeySendUser.text()
		if user == '' or key == '':
			self.logMessage('User or Key is Empty or not defined.')
			return
		bytestring = RSACommunication.encrypt_message(key,user)
		data = {'key': bytestring.hex(), 'user': user, 'from': UserDetails.getUsername()}
		self.socket.emit('encryptKey',data)
		self.logMessage('Key Sent To The User.') 

	def setRandomKey(self):
		self.ui.InputKey.setText(Generate.generateRandomKey())

	def logMessage(self,message):
		self.ui.LogsView.append(message)
		print(message)

	def setPort(self,port):
		FPGADetails.PORT = port
		self.logMessage('Serial Port Changed To '+FPGADetails.PORT)

	def setBaudRate(self,bdr):
		FPGADetails.BaudRate = bdr
		self.logMessage('Baud Rate Changed To '+FPGADetails.BaudRate)

	def showConnectivityStatus(self):
		pass 
		## Show in label if connection is made or not

	def CheckExtension(self,f,ext):
		if f.lower().endswith(ext):
			return True
		self.logMessage("Selected file is not "+ext+" file type.")
		return False

	def readKeyFPGA(self):
		self.logMessage('Reading Key from FPGA ...')
		ser = Serial(FPGADetails.PORT, FPGADetails.BaudRate, timeout=2)
		time.sleep(2)
		ser.write(b'A')
		key = ser.read(100)
		ser.close()
		if (type(key)==bytes and len(key)>0):
			print(key)
			print(len(key))
			keytrun = Generate.truncAndConcat(key)
			print(keytrun)
			print(len(keytrun))
			self.ui.InputKey.setText(keytrun.decode())
			self.logMessage('Key Reading From FPGA Completed.')
		else:
			print(key)
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
		FileToSend = QtWidgets.QFileDialog.getOpenFileName(None, 'Send File', 'c:\\', 'All files (*.*)')
		if(FileToSend[0]):
			with open(FileToSend[0], 'rb') as f:
				r = requests.post('http://localhost:5000/upload', files={'file': f})
				self.logMessage(r.text)
				self.socket.emit('offer_file',{'type':'file_send','filename':FileToSend[0]})

	def receiveFile(self):
		FileToReceive = self.ui.FileInput.text()
		NewFileName = self.ui.NewFileInput.text()
		if NewFileName == '':
			NewFileName = FileToReceive
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
