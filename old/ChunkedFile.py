import os
import sys
import hashlib
# DEPENDENCY: python3-bitarray
from bitarray import bitarray
import struct
import event

class Chunk():
	Hash = None			# string hash
	Slices = None		# bitarray
	Offset = 0			# byte offset from file start
	File = None			# string name
	SliceCt = 0
	SlicesLeft = 0
	ChunkSize = 0
	SliceSize = 65000	# static size of slices for now
	ChunkNo = 0			# index of File.Chunks
	OnCompletion = None	# Event

	def __init__(self, offset, chunksize, fileName, chunkNo, cHash = None):
		self.SliceCt = int(chunksize / self.SliceSize) + 1
		self.Slices = bitarray(self.SliceCt)
		self.ChunkSize = chunksize
		OnCompletion = Event()
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

	def Reset():
		self.Slices = bitarray(self.SliceCt)
		self.SlicesLeft = self.SliceCt


	def UpdateSlice(self, sliceNo, data):
		self.Slices[sliceNo] = True
		with open(self.File, 'r+b') as f:
			f.seek(sliceNo * self.SliceSize + self.Offset)
			f.write(data)
		
		self.SlicesLeft -= 1
		# If the chunk is complete
		if (self.SlicesLeft == 0):
			# Push event to parent with success bool
			self.OnCompletion(self.ChunkNo, self.Hash == self.HashChunk())
				

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
	ChunkSize = 20971520 # 20 MB
	ChunksLeft = 0
	Hash = None		# string
	Path = None		# string
	Name = None		# string
	Chunks = None	# Chunk[]
	Size = 0		# filesize, in bytes
	IsComplete = False

	# Events for when downloading
	RedoChunk = None	# Event
	FileComplete = None	# Event

	def __init__(self, path, name, size = None, cHashes = None, fhash = None):
		self.Name = name
		self.Path = path
		jPath = os.path.join(self.Path, self.Name)

		Chunks = []
		RedoChunk = Event()
		FileComplete = Event()

		if os.path.isfile(jPath):  # If the file exists (seeding)
			self._initFile(jPath)
		else:  # If the file DNE (downloading)
			self.Hash = fhash
			self.Size = size
			sizeLeft = self.Size
			i = 0
			for cHash in cHashes:
				if sizeLeft < self.ChunkSize:
					currentCkSz = sizeLeft
				else:
					currentCkSz = self.ChunkSize

				chunk = Chunk(i * self.ChunkSize, currentCkSz, jPath, i, cHash)
				chunk.OnCompletion += ChunkComplete
				self.Chunks.append(chunk)

				sizeLeft -= self.ChunkSize
				i += 1
			ChunksLeft = len(cHashes)


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
			chunk = Chunk(i * self.ChunkSize, currentCkSz, jPath, i)
			sizeLeft -= self.ChunkSize
			self.Chunks.append(chunk)

			cData = chunk.HashChunk()
			SHA1Hash.update(cData)
		self.Hash = SHA1Hash.hexdigest()

		# Need to somehow check if this file is complete from previous runs.
		# SQLite db at this point.
		if (False):
			self.IsComplete = True
			
		print(jPath, ": ", self.Hash)

	def ChunkComplete(chunkNo, correctHash):
		if (correctHash):
			self.ChunksLeft -= 1;
			if (self.ChunksLeft == 0):
				self.FileComplete(self.Hash)
		else:
			self.Chunks[chunkNo].Reset()
			self.RedoChunk(self.Hash, chunkNo)
			

class Directory():
	Files = None	# {hash : File}
	DirPath = None	# string path

	def __init__(self, dirPath):
		self.Files = {}
		self.DirPath = dirPath
		#load an index (fPath + hash)
		self.RecurseLoad(dirPath)
		

	def RecurseLoad(self, dirPath):
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
			b += struct.pack('>20s', chunk.Hash)
		return b

	# Used if we start d/ling a file
	def Create(self, fhash, name, size, cHashes):
		f = File(self.DirPath, name, size, cHashes, fhash)
		self.Files[fhash] = f
		return f
		

