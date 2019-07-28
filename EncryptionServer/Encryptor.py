import os, random, struct
from Crypto.Cipher import AES, Blowfish
from des import DesKey
from hashlib import sha256
import numpy
from PyQt5.QtWidgets import QTextBrowser

sizeQ = struct.calcsize('Q')

class UserKeyStore():
	def __init__(self, KeyFile):
		blockSize = 16
		self.keyArr = []
		self.KeyAvailabeIndex = 0
		self.isConsumed = False
		with open(KeyFile,'rb') as kf:
			while True:
				chunk = kf.read(16)
				if (len(chunk)==0):
					break
				if(len(chunk)!=16):
					chunk += (' ' * (blockSize - len(chunk)%blockSize)).encode()
				self.keyArr.append(chunk)
		self.keyArr = numpy.array(self.keyArr)
		self.totalKeys = self.keyArr.size
		self.boolkeyArr = numpy.repeat([True], self.totalKeys)

	def findNextAvailableKey(self):
		while (self.boolkeyArr[self.KeyAvailabeIndex]==False):
			self.KeyAvailabeIndex += 1
			if(self.KeyAvailabeIndex==self.totalKeys):
				self.isConsumed = True
				UIFunctions.log("KeyConsumed")
				break

	def getEncryptionKey(self):
		self.findNextAvailableKey()
		if (self.isConsumed == True):
			UIFunctions.log("Cannot XOR as Key is entirely consumed.")
			return bytes(16)
		return self.keyArr[self.KeyAvailabeIndex], self.KeyAvailabeIndex

	def getDecryptionKey(self,i):
		if(i<self.totalKeys):
			self.boolkeyArr[i] = False
			return self.keyArr[i]
		else:
			UIFunctions.log("Wrong Index for User Key")

class UIFunctions:
	log = print
	encryptTextBox = QTextBrowser

def XORKey(bytearray1, bytearray2):
	# if not (type(bytearray1) == bytes and type(bytearray2)==bytes):
	# 	UIFunctions.log("XOR Not Done Due to Type InMatching. Bytes Expected.")
	# 	return None
	if(len(bytearray1)!=len(bytearray2)):
		UIFunctions.log("Byte Array Length for XORing not equal.")
		return None
	l = [a^b for a,b in zip(bytearray1,bytearray2)]
	return bytes(l)

class Generate:
	@staticmethod
	def generateRandomKey(size = 16):
		return ''.join(chr(random.randint(0x28, 0x64)) for i in range(size))

	@staticmethod
	def generateByteString (size = 16):
		string = Generate.generateRandomKey(size)
		return string.encode()
	
	@staticmethod
	def keyGenerator(bs,key):
		info = [key[i:i+bs] for i in range(0, len(key), bs)]
		while True:
			for c in info:
				yield(c)

	@staticmethod
	def truncAndConcat(data):
		l = len(data)
		x = data[l-9:l-1]
		return x+x

class FileCrypto:
	@staticmethod
	def encrypt_CBC(index, encryptFunc, iv, blockSize, in_filename,out_filename,chunksize):
		filesize = os.path.getsize(in_filename)
		UIFunctions.log("Size of file: "+str(filesize)+" bytes")
		UIFunctions.log('File Selected: '+str(in_filename))
		with open(in_filename, 'rb') as infile:
			with open(out_filename, 'wb') as outfile:
				outfile.write(struct.pack('Q', index))
				outfile.write(struct.pack('Q', filesize))
				outfile.write(iv)
				while True:
					chunk = infile.read(chunksize)
					if len(chunk) == 0:
						break
					if len(chunk) % blockSize != 0:
						chunk += (' ' * (blockSize - len(chunk)%blockSize)).encode()
					encryptedText = encryptFunc(chunk)
					UIFunctions.encryptTextBox.setText(str(encryptedText))
					outfile.write(encryptedText)
		UIFunctions.log("Encryption Completed")

	@staticmethod
	def encrypt_CBC_LongKey(key, index, encryptFunc, iv, blockSize, in_filename, out_filename,chunksize):
		filesize = os.path.getsize(in_filename)
		UIFunctions.log("Size of file: "+str(filesize)+" bytes")
		UIFunctions.log('File Selected: '+str(in_filename))
		keyGen = Generate.keyGenerator(blockSize,key)
		with open(in_filename, 'rb') as infile:
			with open(out_filename, 'wb') as outfile:
				outfile.write(struct.pack('Q', index))
				outfile.write(struct.pack('Q', filesize))
				outfile.write(iv)
				while True:
					chunk = infile.read(chunksize)
					if len(chunk) == 0:
						break
					if len(chunk) % blockSize != 0:
						chunk += (' ' * (blockSize - len(chunk)%blockSize)).encode()
					blockKey = keyGen.__next__()
					encryptedText = encryptFunc(blockKey,chunk)
					UIFunctions.encryptTextBox.setText(str(encryptedText))
					outfile.write(encryptedText)
		UIFunctions.log("Encryption Completed")

	# @staticmethod
	# def decrypt_file_CBC(decryptFunc,origsize, blockSize, in_filename, out_filename,chunksize):
	# 	with open(in_filename, 'rb') as infile:
	# 		with open(out_filename, 'wb') as outfile:
	# 			while True:
	# 				chunk = infile.read(chunksize)
	# 				if len(chunk) == 0:
	# 					break
	# 				outfile.write(decryptFunc(chunk))
	# 			outfile.truncate(origsize)
	# 		UIFunctions.log("Decryption Completed")

class AES_Encryptor:	
	def __init__(self, key, userKey):
		self.key = key
		self.userKey = userKey
	
	## ENCRYPTION
	def encrypt_file(self, in_filename, out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = in_filename + '.aes'

		iv = Generate.generateByteString(16)
		userkey,index = self.userKey.getEncryptionKey()
		encryptionKey = XORKey(self.key,userkey)
		
		UIFunctions.log("AES Encryption Started.")
		## For Short Key
		encryptor = AES.new(encryptionKey, AES.MODE_CBC, iv)
		FileCrypto.encrypt_CBC(index, encryptor.encrypt, iv, 16, in_filename, out_filename, chunksize) 

		## For Long Key
		# def AES_EncryptFunc(blockSizeKey,chunk):
		# 	encryptor = AES.new(blockSizeKey,AES.MODE_CBC,iv)
		# 	return encryptor.encrypt(chunk)
		# FileCrypto.encrypt_CBC_LongKey(self.key, self.index, AES_EncryptFunc, iv, self.blockSize, in_filename, out_filename, chunksize)

	## DECRYPTION 
	def decrypt_file(self, in_filename, out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = os.path.splitext(in_filename)[0]
		with open(in_filename, 'rb') as infile:
			index = struct.unpack('Q', infile.read(sizeQ))[0]
			origsize = struct.unpack('Q', infile.read(sizeQ))[0]
			iv = infile.read(16)
			uk = self.userKey.getDecryptionKey(index)
			decryptionKey = XORKey(self.key,uk) 

			UIFunctions.log("AES Decryption Started.")
			UIFunctions.log("Size of file: "+str(origsize)+" bytes")

			## Short Key
			decryptor = AES.new(decryptionKey,AES.MODE_CBC,iv)

			## Long Key
			# keyGen = Generate.keyGenerator(self.blockSize,self.key)
			# def AES_DecryptFunc(blockSizeKey,chunk):
			# 	decryptor = AES.new(blockSizeKey,AES.MODE_CBC,iv)
			# 	return decryptor.decrypt(chunk)

			with open(out_filename, 'wb') as outfile:
				while True:
					chunk = infile.read(chunksize)
					if len(chunk) == 0:
						break
					## For Long Key
					# blockKey = keyGen.__next__()  
					# blockKey = XORKey(uk,self.key)
					# plainText = AES_DecryptFunc(blockKey,chunk)
					## Short Key
					plainText = decryptor.decrypt(chunk)
					outfile.write(plainText)
				outfile.truncate(origsize)

			UIFunctions.log("Decryption Completed")

class Blowfish_Encryptor:	
	def __init__(self, key, userkey):
		self.key = key
		self.userKey = userkey

	## ENCRYPTION
	def encrypt_file(self, in_filename, out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = in_filename + '.blf'
		iv = Generate.generateByteString(Blowfish.block_size)
		userkey,index = self.userKey.getEncryptionKey()
		encryptionKey = XORKey(self.key,userkey)
		cipher = Blowfish.new(encryptionKey,Blowfish.MODE_CBC,iv)
		UIFunctions.log("Blowfish Encryption Started.")
		FileCrypto.encrypt_CBC(index, cipher.encrypt, iv, Blowfish.block_size, in_filename,out_filename, chunksize)

	## DECRYPTION
	def decrypt_file(self, in_filename ,out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = os.path.splitext(in_filename)[0]
		with open(in_filename, 'rb') as infile:
			index = struct.unpack('Q', infile.read(sizeQ))[0]
			origsize = struct.unpack('Q', infile.read(sizeQ))[0]
			iv = infile.read(Blowfish.block_size)
			uk = self.userKey.getDecryptionKey(index)
			decryptionKey = XORKey(self.key,uk) 
			cipher = Blowfish.new(decryptionKey,Blowfish.MODE_CBC,iv)

			UIFunctions.log("Decryption Started. Size of file: "+str(origsize)+" bytes")
			with open(out_filename, 'wb') as outfile:
				while True:
					chunk = infile.read(chunksize)
					if len(chunk) == 0:
						break
					decryptedText = cipher.decrypt(chunk)
					outfile.write(decryptedText)
				outfile.truncate(origsize)
			UIFunctions.log("Decryption Completed.")

class DES_Encryptor:
	def __init__(self, key, userkey):
		self.key = key
		self.userKey = userkey
		self.block_size = 8

	## ENCRYPTION
	def encrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = in_filename + '.des'
		iv = Generate.generateByteString(self.block_size)
		userkey,index = self.userKey.getEncryptionKey()
		encryptionKey = XORKey(self.key,userkey)
		cipher = DesKey(encryptionKey)
		cipherFunc = lambda x: cipher.encrypt(x, initial = iv)
		UIFunctions.log("DES Encryption Started")
		FileCrypto.encrypt_CBC(index, cipherFunc, iv, self.block_size, in_filename, out_filename, chunksize)

	## DECRYPTION
	def decrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = os.path.splitext(in_filename)[0]
			print(out_filename)
		with open(in_filename, 'rb') as infile:
			index = struct.unpack('Q', infile.read(sizeQ))[0]
			origsize = struct.unpack('Q', infile.read(sizeQ))[0]
			iv = infile.read(self.block_size)
			uk = self.userKey.getDecryptionKey(index)
			decryptionKey = XORKey(self.key,uk) 

			UIFunctions.log("DES Decryption Started. Size of file: "+str(origsize)+" bytes")
			cipher = DesKey(decryptionKey)
			with open(out_filename, 'wb') as outfile:
				while True:
					chunk = infile.read(chunksize)
					if len(chunk) == 0:
						break
					decryptedText = cipher.decrypt(chunk,initial=iv)
					outfile.write(decryptedText)
				outfile.truncate(origsize)
			UIFunctions.log("DES Decryption Completed.")
