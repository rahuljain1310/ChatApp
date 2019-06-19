import os, random, struct
from Crypto.Cipher import AES, Blowfish
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
	def __init__(self,key,log):
		self.key = key
		self.log = log
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
					outfile.write(encryptor.encrypt(chunk))
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
	def __init__(self,key,log):
		self.key = key.encode()
		self.log = log
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
