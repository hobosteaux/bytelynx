import os
import sys
import hashlib
# DEPENDENCY: python3-bitarray
from bitarray import bitarray
import struct

class Chunk():
	Hash = None
	Slices = None
	Offset = 0
	File = None
	SliceCt = 0
	SlicesLeft = 0
	ChunkSize = 0
	SliceSize = 65000

	def __init__(self, offset, chunksize, fileName, cHash = None):
		self.SliceCt = int(chunksize / self.SliceSize) + 1
		self.Slices = bitarray(self.SliceCt)
		self.ChunkSize = chunksize
		# could also load info files
		self.Offset = offset
		self.File = fileName
		if cHash == None:
			self.Slices.setall(True)
			self.SlicesLeft = 0
			#print("CHUNK - Offset: ", self.Offset, "  SliceCt: ", self.SliceCt, "   Hash: ", self.Hash)
		else:
			self.Slices.setall(False)
			self.SlicesLeft = self.SliceCt
			self.Hash = cHash


	def UpdateSlice(self, sliceNo, data):
		self.Slices[sliceNo] = True
		with open(self.File, 'r+b') as f:
			f.seek(sliceNo * self.SliceSize + self.Offset)
			f.write(data)
		
		self.SlicesLeft -= 1
		if (self.SlicesLeft == 0):
			self.Hash = self.HashChunk()

	def HashChunk(self):
		SHA1Hash = hashlib.sha1()
		with open(self.File, 'rb') as f:
			f.seek(self.Offset)
			#print("READING: ", self.ChunkSize)
			buf = f.read(self.ChunkSize)
			SHA1Hash.update(buf)

		SHA1HashBase16 = SHA1Hash.hexdigest()
		self.Hash = SHA1HashBase16
		return buf

	def ReadSlice(self, sliceNo):
		with open(self.File, 'rb') as f:
			f.seek(self.Offset + (self.SliceSize * sliceNo))
			rSize = self.SliceSize if sliceNo != self.SliceCt - 1 \
				else self.ChunkSize % self.SliceSize
			return f.read(rSize)

class File():
	ChunkSize = 20971520
	Hash = None
	Path = None
	Name = None
	Chunks = []
	Size = 0

	def __init__(self, path, name, size = None, cHashes = None, fhash = None):
		self.Name = name
		self.Path = path
		jPath = os.path.join(self.Path, self.Name)
		if os.path.isfile(jPath):
			self._initFile(jPath)
		else:
			self.Hash = fhash
			self.Size = size
			sizeLeft = self.Size
			i = 0
			for cHash in cHashes:
				if sizeLeft < self.ChunkSize:
					currentCkSz = sizeLeft
				else:
					currentCkSz = self.ChunkSize
				self.Chunks.append(Chunk(i * self.ChunkSize, currentCkSz, jPath, cHash))
				sizeLeft -= self.ChunkSize
				i += 1


	def _initFile(self, jPath):
		"""Inits the chunks and uses the data segments from them to make to total hash"""
		self.Size = os.path.getsize(jPath)
		sizeLeft = self.Size
		SHA1Hash = hashlib.sha1()
		for i in range(0, (int)(self.Size / self.ChunkSize) + 1):
			if sizeLeft < self.ChunkSize:
				currentCkSz = sizeLeft
			else:
				currentCkSz = self.ChunkSize
			chunk = Chunk(i * self.ChunkSize, currentCkSz, jPath)
			sizeLeft -= self.ChunkSize
			self.Chunks.append(chunk)

			cData = chunk.HashChunk()
			SHA1Hash.update(cData)
		self.Hash = SHA1Hash.hexdigest()
		print(jPath, ": ", self.Hash)
			

class Directory():
	# Files = {hash : file}
	Files = None
	DirPath = None

	def __init__(self, dirPath):
		self.Files = {}
		self.DirPath = dirPath
		#load an index (fPath + hash)
		self.RecurseLoad(dirPath)
		

	def RecurseLoad(self, dirPath):
		#should be cached locally
		for path,dirs,files in os.walk(dirPath):
			for fn in files:
				fo = File(path, fn)
				self.Files[fo.Hash] = fo
			for dn in dirs:
				self.RecurseLoad(os.path.join(path, dn))

	def GetChunkHashes(self, fHash):
		f = self.Files(fHash)
		b = b''
		for chunk in f.Chunks:
			b += struct.pack('>16s', chunk.Hash)
		return b

	def Create(self, fhash, name, size, cHashes):
		self.Files[fhash] = File(self.DirPath, name, size, cHashes, fhash)

