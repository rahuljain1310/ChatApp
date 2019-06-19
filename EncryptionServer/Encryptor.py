import os, random, struct
from Crypto.Cipher import AES, Blowfish
from des import DesKey
from hashlib import sha256

class Generate:
	@staticmethod
	def generateRandomKey(size = 16):
		return ''.join(chr(random.randint(0x28, 0x64)) for i in range(size))

	@staticmethod
	def generateByteString (size = 16):
		string = Generate.generateRandomKey(size)
		return string.encode()

class AES_Encryptor:	
	def __init__(self, key, log=None, textbox=None):
		self.key = key
		self.log = log
		self.textbox = textbox
		self.keyhash = sha256(key.encode()).digest()
		print("KeyHash is"+str(self.keyhash))
		self.iv = Generate.generateByteString(16)
		print(self.iv)

	def encrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		encryptor = AES.new(self.keyhash, AES.MODE_CBC, self.iv)
		if not out_filename:
			out_filename = in_filename + '.enc'
		filesize = os.path.getsize(in_filename)
		self.log("AES Encryption Started. Size of file: "+str(filesize)+" bytes")
		with open(in_filename, 'rb') as infile:
			with open(out_filename, 'wb') as outfile:
				outfile.write(struct.pack('Q', filesize))
				outfile.write(self.iv)
				while True:
					chunk = infile.read(chunksize)
					if len(chunk) == 0:
						break
					if len(chunk) % 16 != 0:
						chunk += (' ' * (16 - len(chunk)%16)).encode()
					encryptedText = encryptor.encrypt(chunk)
					self.textbox.setText(str(encryptedText))
					outfile.write(encryptedText)
			outfile.close()
		infile.close()

	def decrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = os.path.splitext(in_filename)[0]
			print(out_filename)
		with open(in_filename, 'rb') as infile:
			origsize = struct.unpack('Q', infile.read(struct.calcsize('Q')))[0]
			self.log("Decryption Started. Size of file: "+str(origsize)+" bytes")
			iv = infile.read(16)
			decryptor = AES.new(self.keyhash, AES.MODE_CBC, iv)
			with open(out_filename, 'wb') as outfile:
				while True:
					chunk = infile.read(chunksize)
					if len(chunk) == 0:
						break
					outfile.write(decryptor.decrypt(chunk))
				outfile.truncate(origsize)

class Blowfish_Encryptor:	
	def __init__(self, key, log=None, textbox=None):
		self.key = key.encode()
		self.log = log
		self.textbox = textbox
		print("Key is"+str(self.key))
		self.iv = Generate.generateByteString(Blowfish.block_size)
		print(self.iv)

	def encrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		cipher = Blowfish.new(self.key,Blowfish.MODE_CBC,self.iv)
		bs = Blowfish.block_size
		if not out_filename:
			out_filename = in_filename + '.blf'
		filesize = os.path.getsize(in_filename)
		self.log("Blowfish Encryption Started. Size of file: "+str(filesize)+" bytes")
		with open(in_filename, 'rb') as infile:
			with open(out_filename, 'wb') as outfile:
				outfile.write(struct.pack('Q', filesize))
				outfile.write(self.iv)
				while True:
					chunk = infile.read(chunksize)
					if len(chunk) == 0:
						break
					if len(chunk) % bs != 0:
						chunk += (' ' * (bs - len(chunk)%bs)).encode()
					encryptedText = cipher.encrypt(chunk)
					self.textbox.setText(str(encryptedText))
					outfile.write(encryptedText)
			outfile.close()
		infile.close()
		self.log("Blowfish Encryption Completed.")

	def decrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = os.path.splitext(in_filename)[0]
			print(out_filename)
		with open(in_filename, 'rb') as infile:
			origsize = struct.unpack('Q', infile.read(struct.calcsize('Q')))[0]
			self.log("Decryption Started. Size of file: "+str(origsize)+" bytes")
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
			self.log("Decryption Completed.")

class DES_Encryptor:
	def __init__(self, key, log=None, textbox=None):
		self.key = key.encode()
		self.log = log
		self.textbox = textbox
		self.log("Key is "+str(self.key))
		self.iv = Generate.generateByteString(8)
		self.block_size = 8

	def encrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = in_filename + '.des'
		filesize = os.path.getsize(in_filename)

		if not len(self.key)%8==0:
			self.log("Key Should be of length 8,16 or 24 bytes.")
			return

		self.log("DES Encryption Started. Size of file: "+str(filesize)+" bytes")
		cipher = DesKey(self.key)
		bs = self.block_size
		with open(in_filename, 'rb') as infile:
			with open(out_filename, 'wb') as outfile:
				outfile.write(struct.pack('Q', filesize))
				outfile.write(self.iv)
				while True:
					chunk = infile.read(chunksize)
					if len(chunk) == 0:
						break
					if len(chunk) % bs != 0:
						chunk += (' ' * (bs - len(chunk)%bs)).encode()
					encryptedText = cipher.encrypt(chunk,initial=self.iv)
					self.textbox.setText(str(encryptedText))
					outfile.write(encryptedText)
			outfile.close()
		infile.close()
		self.log("DES Encryption Completed.")

	def decrypt_file(self, in_filename,out_filename=None,chunksize=64*1024):
		if not out_filename:
			out_filename = os.path.splitext(in_filename)[0]
			print(out_filename)
		with open(in_filename, 'rb') as infile:
			origsize = struct.unpack('Q', infile.read(struct.calcsize('Q')))[0]
			self.log("DES Decryption Started. Size of file: "+str(origsize)+" bytes")
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
			self.log("DES Decryption Completed.")
