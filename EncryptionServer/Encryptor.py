import os, random, struct
from Crypto.Cipher import AES, Blowfish
from des import DesKey
from hashlib import sha256
from PyQt5.QtWidgets import QTextBrowser

class UIFunctions:
	log = print
	encryptTextBox = QTextBrowser

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
	def encrypt_CBC(encryptFunc, iv, blockSize, in_filename,out_filename,chunksize):
		filesize = os.path.getsize(in_filename)
		UIFunctions.log("Size of file: "+str(filesize)+" bytes")
		UIFunctions.log('File Selected: '+str(in_filename))
		with open(in_filename, 'rb') as infile:
			with open(out_filename, 'wb') as outfile:
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
	def encrypt_CBC_LongKey(key, encryptFunc, iv, blockSize, in_filename, out_filename,chunksize):
		filesize = os.path.getsize(in_filename)
		UIFunctions.log("Size of file: "+str(filesize)+" bytes")
		UIFunctions.log('File Selected: '+str(in_filename))
		keyGen = Generate.keyGenerator(blockSize,key)
		with open(in_filename, 'rb') as infile:
			with open(out_filename, 'wb') as outfile:
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
	def __init__(self, key):
		self.blockSize = 16
		self.key = key.encode()
	
	def encrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		iv = Generate.generateByteString(self.blockSize)

		def AES_EncryptFunc(blockSizeKey,chunk):
			encryptor = AES.new(blockSizeKey,AES.MODE_CBC,iv)
			return encryptor.encrypt(chunk)

		if not out_filename:
			out_filename = in_filename + '.aes'
			
		UIFunctions.log("AES Encryption Started.")
		FileCrypto.encrypt_CBC_LongKey(self.key, AES_EncryptFunc, iv, self.blockSize, in_filename, out_filename, chunksize)

	def decrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = os.path.splitext(in_filename)[0]
			print(out_filename)
		with open(in_filename, 'rb') as infile:
			origsize = struct.unpack('Q', infile.read(struct.calcsize('Q')))[0]
			UIFunctions.log("AES Decryption Started.")
			UIFunctions.log("Size of file: "+str(origsize)+" bytes")
			iv = infile.read(16)

			def AES_DecryptFunc(blockSizeKey,chunk):
				decryptor = AES.new(blockSizeKey,AES.MODE_CBC,iv)
				return decryptor.decrypt(chunk)

			keyGen = Generate.keyGenerator(self.blockSize,self.key)
			with open(out_filename, 'wb') as outfile:
				while True:
					chunk = infile.read(chunksize)
					if len(chunk) == 0:
						break
					blockKey = keyGen.__next__()
					plainText = AES_DecryptFunc(blockKey,chunk)
					outfile.write(plainText)
				outfile.truncate(origsize)
			UIFunctions.log("Decryption Completed")

class Blowfish_Encryptor:	
	def __init__(self, key):
		self.key = key.encode()
		print("Key is"+str(self.key))

	def encrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		iv = Generate.generateByteString(Blowfish.block_size)
		cipher = Blowfish.new(self.key,Blowfish.MODE_CBC,iv)
		if not out_filename:
			out_filename = in_filename + '.blf'
		UIFunctions.log("Blowfish Encryption Started.")
		FileCrypto.encrypt_CBC(cipher.encrypt, iv, Blowfish.block_size, in_filename,out_filename, chunksize)

	def decrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = os.path.splitext(in_filename)[0]
			print(out_filename)
		with open(in_filename, 'rb') as infile:
			origsize = struct.unpack('Q', infile.read(struct.calcsize('Q')))[0]
			UIFunctions.log("Decryption Started. Size of file: "+str(origsize)+" bytes")
			iv = infile.read(Blowfish.block_size)
			cipher = Blowfish.new(self.key,Blowfish.MODE_CBC,iv)

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
	def __init__(self, key):
		self.key = key.encode()
		UIFunctions.log("Key is "+str(self.key))
		self.block_size = 8

	def encrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		iv = Generate.generateByteString(8)
		if not out_filename:
			out_filename = in_filename + '.des'
		if not len(self.key)%8==0:
			UIFunctions.log("Key Should be of length 8,16 or 24 bytes.")
			return
		cipher = DesKey(self.key)
		def cipherWrapper(x):
			return cipher.encrypt(x,initial=iv)
		UIFunctions.log("DES Encryption Started")
		FileCrypto.encrypt_CBC(cipherWrapper, iv, self.block_size, in_filename, out_filename, chunksize)

	def decrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = os.path.splitext(in_filename)[0]
			print(out_filename)
		with open(in_filename, 'rb') as infile:
			origsize = struct.unpack('Q', infile.read(struct.calcsize('Q')))[0]
			UIFunctions.log("DES Decryption Started. Size of file: "+str(origsize)+" bytes")
			iv = infile.read(Blowfish.block_size)
			cipher = DesKey(self.key)
			with open(out_filename, 'wb') as outfile:
				while True:
					chunk = infile.read(chunksize)
					if len(chunk) == 0:
						break
					decryptedText = cipher.decrypt(chunk,initial=iv)
					outfile.write(decryptedText)
				outfile.truncate(origsize)
			UIFunctions.log("DES Decryption Completed.")
