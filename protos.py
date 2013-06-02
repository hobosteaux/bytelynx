from struct import *
from common import *
from ChunkedFile import *

# DATA = (parsed[1], parsed[2])

#FORMATS[0] = ('>H', None) #Awk -> [char mType, ushort awkID]
def Awk(data, state, addr):
	state.Connections[addr].AwkPkt(data[0])

#FORMATS[1] = ('>H', None) #Ping -> [char mType, ushort pktID]
def Ping(data, state, addr):
	state.Connections[addr].SendAwk(data[0])

	#THIS IS FOR THE ACTION OF PINGING
	#pktID = state.Connections[addr].PktCounter
	#state.Connections[addr].SendData('>BH', 1, pktID)
	#state.Connections[addr].AddPing(pktID)

#FORMATS[2] = ('>HH', None) #Connection Init -> [char mType, ushort pktID, ushort port]
def InitConn(data, state, addr):
	state.Connections[addr].SendAwk(data[0])
	state.NewConn(addr)

#FORMATS[5] = ('>H16s', None) #Get File -> [char mType, ushort pktID, 128bit hash]
def GetFile(data, state, addr):
	state.Connections[addr].SendAwk(data[0])
	hashbytes = state.Files.GetChunkHashes(data[1])
	state.Connections[addr].SendData(6, (pack('>Q', state.Files[data[1]].Size) + hashbytes))

#FORMATS[6] = ('>H16s50cQ', '>16s') #File response -> [char mType, ushort pktID, 128bit hash, 50c name, ulonglong size (8 bit), [128bit hashes]]
def FileResponse(data, state, addr):
	state.Connections[addr].SendAwk(data[0])
	# Create(hash, name, size, cHashes)
	state.Files.Create(data[0][1], data[0][2], data[0][3], data[1])

#FORMATS[7] = ('>H16sH', None) #I/O request -> [char mType, ushort pktID, 128bit hash, ushort chunkNo]
def IORequest(data, state, addr):
	state.Connections[addr].SendAwk(data[0])
	chunk = state.Files[data[1]].Chunks[data[2]]
	for sliceNo in range(0, chunk.SliceCt):
		state.SlicesToSend.append(TransferSlice(state.Files[data[1]], chunk, sliceNo, addr))

#FORMATS[8] = ('>H16sH', '>H') #I/O resend -> [char mType, ushort pktID, 128bit hash, ushort chunkNo, slices(ushort arr)]
def IOResend(data, state, addr):
	state.Connections[addr].SendAwk(data[0][0])
	chunk = state.Files[data[0][1]].Chunks[data[0][2]]
	for sliceNo in data[1]:
		state.SlicesToSend.append(TransferSlice(state.Files[data[1]], chunk, sliceNo, addr))

#FORMATS[9] = ('>H16sHH', None) #I/O send -> [char mType, ushort pktID, 128bit hash, ushort chunkNo, ushort sliceNo, DATA]
def IOReceive(data, state, addr):
	state.Connections[addr].SendAwk(data[0])
	state.Files[data[0][1]].Chunks[data[0][2]].UpdateSlice(data[0][3], data[1])

# (struct format, handler)
Protos = {}
Protos[0] = (('>H', None), Awk)
Protos[1] = (('>H', None), Ping)
Protos[2] = (('>HH', None), InitConn)
Protos[5] = (('>H16s', None), GetFile)
Protos[6] = (('>H16s50cQ', '>16s'), FileResponse)
Protos[7] = (('>H16sH', None), IORequest)
Protos[8] = (('>H16sH', '>H'), IOResend)
Protos[9] = (('>H16sHH', None), IOReceive)

def UnpackArray(data, fmtNum):
	ssize = calcsize(Protos[fmtNum][0][1])
	arr = []
	for i in range(0, len(data) / ssize):
		arr.append(unpack(Protos[fmtNum][0][1], data[i*ssize : (i+1)*ssize])[0])
	return arr

def Unpack(data):
	num = unpack('>B', data[:1])[0]
	unpacked = unpack(Protos[num][0][0], data[1:calcsize(Protos[num][0][0])+1])

	if calcsize(Protos[num][0][0]) + 1 < len(data):
		if not Protos[num][0][1]: #Only if it is a data packet.
			return (num, unpacked, data[Protos[num][0][0] + 1:])
		else:
			return (num, unpacked, UnpackArray(data[Protos[num][0][0] + 1:], num))
	return (num, unpacked)
