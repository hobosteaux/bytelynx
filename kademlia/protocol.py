#!/usr/bin/python3

import struct
from listExt import ExtList
from contact import Hash

EXTTAG = 'payload'
IPTAG = 'ip'
PORTTAG = 'port'
TYPETAG = 'type'
PTYPETAG = 'payload_type'
PKTIDTAG = 'pktid'
HASHTAG = 'hash'
TARGETHASHTAG = 'target_hash'

PINGMSG = 'ping'
PONGMSG = 'pong'
FINDNODEMSG = 'find_node'
FOUNDNODEMSG = 'found_nodes'
PAYLOADMSG = 'payload'

# This is clunky and ugly, but IP addrs and such need it.
def TranslateToMessage(tags):
	# Translate type from string to int.
	if (TYPETAG in tags):
		#print(tags[TYPETAG], '->', ReverseProtos[tags[TYPETAG]])
		tags[TYPETAG] = ReverseProtos[tags[TYPETAG]]
	# Tags contain an ip addr (string).
	# !!! QUICK SHORTCUT !!!
	# If it contains a ip, it contains a hash.
	if (EXTTAG in tags) and (IPTAG in tags[EXTTAG].first()):
		for item in tags[EXTTAG]:
			ipArr = item[IPTAG].split('.')
			item[IPTAG] = (int(x) for x in item[IPTAG].split('.'))
			item[HASHTAG] = item[HASHTAG].Value
	# Tags contain a hash.
	if (HASHTAG in tags):
		tags[HASHTAG] = tags[HASHTAG].Value
	if (TARGETHASHTAG in tags):
		tags[TARGETHASHTAG] = tags[TARGETHASHTAG].Value

def TranslateToTags(tags):
	# Translate type from int to string.
	if (TYPETAG in tags):
		#print(tags[TYPETAG], '->', Protos[tags[TYPETAG]].Name)
		tags[TYPETAG] = Protos[tags[TYPETAG]].Name
	# Tags contain an ip addr (string).
	if (EXTTAG in tags) and (IPTAG in tags[EXTTAG].first()):
		for item in tags[EXTTAG]:
			item[IPTAG] = '.'.join(map(str, item[IPTAG]))
			item[HASHTAG] = Hash(item[HASHTAG])
	# Tags contain a hash.
	if (HASHTAG in tags):
		tags[HASHTAG] = Hash(tags[HASHTAG])
	if (TARGETHASHTAG in tags):
		tags[TARGETHASHTAG] = Hash(tags[TARGETHASHTAG])



# A note about parsing - if it is NOT extended, but still has data after parsing,
# it is assumed that there is raw binary data after.
class Message():
	Name = ''
	IsExtended = False
	Parser = None		# List of struct strings ['H', '20c']
	ExtParser = None		
	TagNames = None		# Passed as a list ['id', ...]
	ExtTags = None	 

	def __init__(self, name, tagNames, staticParser, dynamicTags = None, dynamicParser = None):
		self.Name = name
		self.TagNames = tagNames
		self.Parser = staticParser
		if (dynamicParser != None):
			self.IsExtended = True
			self.ExtParser = dynamicParser
			self.ExtTags = dynamicTags

	# For extended mode, dictionary MUST have the extended tag in it.
	def Encode(self, tags):
		data = b''
		for idx, tag in enumerate(self.TagNames):
			#print(tag, tags[tag])
			data += struct.pack('>' + self.Parser[idx], tags[tag])
		if (self.IsExtended):
			for item in tags[EXTTAG]:
				for idx, tag in enumerate(self.ExtTags):
					# If we have a standard value.
					try:
						#print('EXT:', item, tag)
						data += struct.pack('>' + self.ExtParser[idx], item[tag])
					# If we have a list, unpack it as args.
					except struct.error:
						data += struct.pack('>' + self.ExtParser[idx], *item[tag])
		# Case that we have a raw raw binary blob.
		elif (EXTTAG in tags):
			data += tags[EXTTAG]
		return data

	def Decode(self, data):
		tags = {}
		offset = 0
		for idx, tag in enumerate(self.TagNames):
			# NOTE: struct.unpack returns a tuple no matter what.
			# If we use the notation 3s etc, this returns a 3-ple
			# If we use the notation 2s etc, this returns a 2-ple
			# If we use the notation s, this returns a 1-ple
			# Well shit.
			#print(self.Parser[idx], offset,offset + struct.calcsize(self.Parser[idx]))
			value = struct.unpack('>' + self.Parser[idx],\
				 data[offset : offset + struct.calcsize(self.Parser[idx])])
			if (len(value) == 1):
				tags[tag] = value[0]
			else:
				tags[tag] = value
			offset += struct.calcsize(self.Parser[idx])
		if (self.IsExtended):
			payload = ExtList()
			size = struct.calcsize(''.join(self.ExtParser))
			# Chop it up into the size of that data
			for i in range(0, int((len(data) - offset) / struct.calcsize(''.join(self.ExtParser)))):
				extTags = {}
				for idx, tag in enumerate(self.ExtTags):
					tagSize = struct.calcsize(self.ExtParser[idx])
					value = struct.unpack('>' + self.ExtParser[idx], data[offset:offset + tagSize])
					if (len(value) == 1):
						extTags[tag] = value[0]
					else:
						extTags[tag] = value
					offset += tagSize
				payload.append(extTags)
			tags[EXTTAG] = payload
		elif (len(data) > struct.calcsize(''.join(self.Parser))):
			tags[EXTTAG] = data[offset:]
		return tags

# This class is used for the base of any message.
class TransportMessage(Message):
	def __init__(self, name, tagNames, staticParser, dynamicTags = None, dynamicParser = None):
		super().__init__(name, [TYPETAG, PKTIDTAG, HASHTAG] + tagNames, \
			['B', 'H', '20s'] + staticParser, dynamicTags, dynamicParser)

# This class is used for any protos already wrapped in a transportMessage.
# Used for inside an encrypted message.
class PayloadMessage(Message):
	def __init__(self, name, tagNames, staticParser, dynamicTags = None, dynamicParser = None):
		super().__init__(name, [PTYPETAG] + tagNames, \
			['B'] + staticParser, dynamicTags, dynamicParser)

# name, tagNames, staticParser, dynamicTags, dynamicParser
Protos = {}
Protos[0] = TransportMessage(PINGMSG, [], [])
Protos[1] = TransportMessage(PONGMSG, [], [])
Protos[2] = TransportMessage(FINDNODEMSG, [TARGETHASHTAG], ['20s'])
Protos[3] = TransportMessage(FOUNDNODEMSG, [TARGETHASHTAG], ['20s'], [HASHTAG,IPTAG,PORTTAG], ['20s','4B','H'])
Protos[4] = TransportMessage(PAYLOADMSG, [], [])

ReverseProtos = {value.Name : key for key, value in Protos.items() }

# Master function to decode a bytestring.
def Decoder(bytestring):
	# struct.unpack('>B') will return (B,)
	tags = Protos[struct.unpack('>B', bytestring[:1])[0]].Decode(bytestring)
	TranslateToTags(tags)
	return tags

# Master function to encode tags.
def Encoder(tags):
	TranslateToMessage(tags)
	try:
		return Protos[tags[TYPETAG]].Encode(tags)
	# If we have a payload.
	except KeyError:
		return Protos[tags[PTYPETAG]].Encode(tags)



if __name__ == "__main__":
	print(ReverseProtos)

	protoNum = 1
	data = struct.pack('>BH20s', protoNum, 5403, b'09876543210987654321')
	tags = Protos[protoNum].Decode(data)
	print(Protos[protoNum].Name, tags)
#	print('Same:', data == Protos[0].Encode(tags))
	print('Same:', data == Encoder(tags))

	protoNum = 3
	data = struct.pack('>BH20s20s4BH', protoNum, 332, b'09876543210987654321', \
		b'12345678901234567890', 192,168,2,1, 758)
	tags = Protos[protoNum].Decode(data)
	print(Protos[protoNum].Name, tags)
	print('Same:', data == Protos[protoNum].Encode(tags))


