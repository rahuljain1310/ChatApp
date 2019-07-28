import json
import os
import random
import sys
import threading
import time
import pickle
import base64
import numpy
import struct

import cv2
import requests
import socketio
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from serial import Serial
from Crypto.Cipher import AES, Blowfish

import rsa
from Encryptor import (AES_Encryptor, Blowfish_Encryptor, DES_Encryptor, Generate, UIFunctions, XORKey, UserKeyStore)
from SerialComm import get_serial_ports, check_serial_status

##=====================================================================================================================
## Initializations 
##=====================================================================================================================

class UserDetails():
	Username = 'Username'
	UserID = -1
	UserState = 'Logged_Off'
	hostname = 'localhost'
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
	BaudRate = 128000
	PORT = 'None'

	@staticmethod
	def checkFPGAStatus(hardwareStatus, PortsCombo):
		threading.Timer(15.0, FPGADetails.checkFPGAStatus, [hardwareStatus, PortsCombo]).start()
		if (check_serial_status(FPGADetails.PORT)):
			hardwareStatus.setText('Hardware Connected.')
		else:
			hardwareStatus.setText('Hardware Disconnected.')
			PortsCombo.clear()
			ports = get_serial_ports()
			for port in ports:
				PortsCombo.addItem(port)
			if len(ports)==0:
				PortsCombo.addItem('None')
			else:
				if FPGADetails.PORT not in ports:
					FPGADetails.PORT = ports[0]
					hardwareStatus.setText('Hardware Connected')
					UIFunctions.log('Serial Port Changed To '+port)	

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
		URL = "http://"+UserDetails.hostname+":5000/publicKey"
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
	def __init__(self, camID, videoframe, socket):
		threading.Thread.__init__(self)
		self.camID = camID
		self.videoFrame = videoframe
		self.socket = socket
	
	def run(self):
		UIFunctions.log("Starting Local Stream")
		camera=cv2.VideoCapture(self.camID)
		while UserDetails.EnableLocalStreaming:
			retval,im = camera.read()
			imgencode = cv2.imencode('.jpg',im)[1]
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
		UserDetails.hostname = self.lui.hostname.text()
		print(UserDetails.hostname)
		r = requests.post('http://'+UserDetails.hostname+':5000/login_user_exe',json=form)
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
		self.userKey = None
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
			encrpt = AES.new(self.ui.InputKey.text().encode(),AES.MODE_ECB)
			encodeframe = encrpt.decrypt(data['frame'])
			encodeframe = encodeframe[0:data['length']]
			pixmap = QtGui.QPixmap()
			pixmap.loadFromData(encodeframe,'JPG')
			self.ui.LocalVideoStream.setPixmap(pixmap)
			if UserDetails.EnableRemoteStreaming == True:
				try:
					_,im = self.camera.read()
					imgencode = cv2.imencode('.jpg',im)[1].tostring()
					origsize = len(imgencode)
					encrpt = AES.new(self.ui.InputKey.text().encode(),AES.MODE_ECB)
					imgencode += (' '*(16-origsize%16)).encode()
					encodeframe = encrpt.encrypt(imgencode)
					self.socket.emit('sendframe',{'frame': encodeframe,'length': origsize})
				except:
					pass					
						
		@socket.on('RSAencryptedKey')
		def RSAEcnryptedKey(data):
			print(data)
			if(data['user']==UserDetails.getUsername()):
				self.logMessage('Received Json From User: '+data['from'])
				keyEncoded = bytes.fromhex(data['key'])
				decryptedKey = RSACommunication.decrypt_message(keyEncoded)
				self.ui.InputKey.setText(decryptedKey.decode())
				self.logMessage('Received Encryption Key From User: '+data['from'])

		print("Connected To Host "+ UserDetails.hostname)
		socket.connect('http://'+UserDetails.hostname+':5000')

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
		self.logMessage('Public Key Generated And Send To The Server.')
		self.socket.emit('public_key',keyuser)

		## Global Gui Widgets
		UIFunctions.log = self.logMessage
		UIFunctions.encryptTextBox = self.ui.EncryptedText

		FPGADetails.checkFPGAStatus(self.ui.HardWareStatus, self.ui.PortsCombo)
		
		## Connect
		#-- drop downs
		self.ui.PortsCombo.activated[str].connect(self.setPort)
		self.ui.BaudRateCombo.activated[str].connect(self.setBaudRate)
		#-- clicks
		self.ui.ReadUserKey.clicked.connect(self.readUserKey)
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

	def readUserKey(self):
		KeyFile = QtWidgets.QFileDialog.getOpenFileName(None, 'Open Image', 'c:\\', 'All Files (*.*)')[0]
		self.userKey = UserKeyStore(KeyFile)
					
	def startSendFrame(self):
		UserDetails.EnableLocalStreaming = False
		UserDetails.EnableRemoteStreaming = True
		self.camera = cv2.VideoCapture(0)
		self.logMessage('')
		self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
		self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
		try:
			_,im = self.camera.read()
			imgencode = cv2.imencode('.jpg',im)[1].tostring()
			origsize = len(imgencode)
			imgencode += (' '*(16-origsize%16)).encode()
			encrpt = AES.new(self.ui.InputKey.text().encode(),AES.MODE_ECB)
			encodeframe = encrpt.encrypt(imgencode)
			try:
				self.socket.emit('sendframe',{'frame': encodeframe,'length': origsize})
			except:
				self.logMessage('Sending Frame failed')
		except:
			self.logMessage("Camera Read failed.")
		
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
		self.localStream = LocalStream(0,self.ui.LocalVideoStream, self.socket)
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
		if FPGADetails.PORT == None or FPGADetails.PORT == 'None':
			self.logMessage('Port Not Selected')
			return
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
		if self.userKey == None:
			self.logMessage('No User Key Loaded.')
			return
		FileToEncrypt = QtWidgets.QFileDialog.getOpenFileName(None, 'Open Image', 'c:\\', 'All Files (*.*)')[0]
		if FileToEncrypt:
			keyGenerated = self.InputKey.text().encode()
			if(self.ui.AES_Radio.isChecked()):
				aes = AES_Encryptor(keyGenerated, self.userKey)
				aes.encrypt_file(FileToEncrypt)
			elif (self.ui.BLOWFISH_Radio.isChecked()):
				bf = Blowfish_Encryptor(keyGenerated,self.userKey)
				bf.encrypt_file(FileToEncrypt)
			elif (self.ui.DES_Radio.isChecked()):
				des = DES_Encryptor(keyGenerated,self.userKey)
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
				aes = AES_Encryptor(self.InputKey.text().encode(), self.userKey)
				aes.decrypt_file(FileToDecrypt)
			elif (self.ui.BLOWFISH_Radio.isChecked()):
				if not self.CheckExtension(FileToDecrypt,'.blf'):
					return
				bf = Blowfish_Encryptor(self.InputKey.text().encode(),self.userKey)
				bf.decrypt_file(FileToDecrypt)
			elif (self.ui.DES_Radio.isChecked()):
				if not self.CheckExtension(FileToDecrypt,'.des'):
					return
				des = DES_Encryptor(self.InputKey.text().encode(), self.userKey)
				des.decrypt_file(FileToDecrypt)
			else:
				self.logMessage("No Method for Decryption Selected.")
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
				r = requests.post('http://'+UserDetails.hostname+':5000/upload', files={'file': f})
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
				r = requests.get('http://'+UserDetails.hostname+':5000/download/'+FileToReceive)
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