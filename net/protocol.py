#!/usr/bin/python3

import struct

from common import Hash, List as list
#from  tag import Tag, HashTag, AddressTag

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
def translate_to_message(tags):
	"""
	Functions that contain all of the datatype translations.
	This should really be built into the parser, assign converters.
	"""
	# Translate type from string to int.
	if (TYPETAG in tags):
		#print(tags[TYPETAG], '->', REVERSE_PROTOS[tags[TYPETAG]])
		tags[TYPETAG] = REVERSE_PROTOS[tags[TYPETAG]]
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

def translate_to_tags(tags):
	# Translate type from int to string.
	if (TYPETAG in tags):
		#print(tags[TYPETAG], '->', PROTOS[tags[TYPETAG]].name)
		tags[TYPETAG] = PROTOS[tags[TYPETAG]].name
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
	name = ''
	is_extended = False
	parser = None		# List of struct strings ['H', '20c']
	ext_parser = None		
	tag_names = None		# Passed as a list ['id', ...]
	ext_tags = None	 

	def __init__(self, name, tagnames, staticparser, dynamicTags = None, daynamic_parser = None):
		self.name = name
		self.tag_names = tagnames
		self.parser = staticparser
		if (daynamic_parser != None):
			self.is_extended = True
			self.ext_parser = daynamic_parser
			self.ext_tags = dynamicTags

	# For extended mode, dictionary MUST have the extended tag in it.
	def encode(self, tags):
		data = b''
		for idx, tag in enumerate(self.tag_names):
			#print(tag, tags[tag])
			data += struct.pack('>' + self.parser[idx], tags[tag])
		if (self.is_extended):
			for item in tags[EXTTAG]:
				for idx, tag in enumerate(self.ext_tags):
					# If we have a standard value.
					try:
						#print('EXT:', item, tag)
						data += struct.pack('>' + self.ext_parser[idx], item[tag])
					# If we have a list, unpack it as args.
					except struct.error:
						data += struct.pack('>' + self.ext_parser[idx], *item[tag])
		# Case that we have a raw raw binary blob.
		elif (EXTTAG in tags):
			data += tags[EXTTAG]
		return data

	def decode(self, data):
		tags = {}
		offset = 0
		for idx, tag in enumerate(self.tag_names):
			# NOTE: struct.unpack returns a tuple no matter what.
			# If we use the notation 3s etc, this returns a 3-ple
			# If we use the notation 2s etc, this returns a 2-ple
			# If we use the notation s, this returns a 1-ple
			# Well shit.
			#print(self.parser[idx], offset,offset + struct.calcsize(self.parser[idx]))
			value = struct.unpack('>' + self.parser[idx],\
				 data[offset : offset + struct.calcsize(self.parser[idx])])
			if (len(value) == 1):
				tags[tag] = value[0]
			else:
				tags[tag] = value
			offset += struct.calcsize(self.parser[idx])
		if (self.is_extended):
			payload = list()
			size = struct.calcsize(''.join(self.ext_parser))
			# Chop it up into the size of that data
			for i in range(0, int((len(data) - offset) / struct.calcsize(''.join(self.ext_parser)))):
				extTags = {}
				for idx, tag in enumerate(self.ext_tags):
					tagSize = struct.calcsize(self.ext_parser[idx])
					value = struct.unpack('>' + self.ext_parser[idx], data[offset:offset + tagSize])
					if (len(value) == 1):
						extTags[tag] = value[0]
					else:
						extTags[tag] = value
					offset += tagSize
				payload.append(extTags)
			tags[EXTTAG] = payload
		elif (len(data) > struct.calcsize(''.join(self.parser))):
			tags[EXTTAG] = data[offset:]
		return tags

# This class is used for the base of any message.
class TransportMessage(Message):
	def __init__(self, name, tagnames, staticparser, dynamicTags = None, daynamic_parser = None):
		super().__init__(name, [TYPETAG, PKTIDTAG, HASHTAG] + tagnames, \
			['B', 'H', '20s'] + staticparser, dynamicTags, daynamic_parser)

# This class is used for any protos already wrapped in a transportMessage.
# Used for inside an encrypted message.
class PayloadMessage(Message):
	def __init__(self, name, tagnames, staticparser, dynamicTags = None, daynamic_parser = None):
		super().__init__(name, [PTYPETAG] + tagnames, \
			['B'] + staticparser, dynamicTags, daynamic_parser)

# name, tagnames, staticparser, dynamicTags, daynamic_parser
PROTOS = {}
PROTOS[0] = TransportMessage(PINGMSG, [], [])
PROTOS[1] = TransportMessage(PONGMSG, [], [])
PROTOS[2] = TransportMessage(FINDNODEMSG, [TARGETHASHTAG], ['20s'])
PROTOS[3] = TransportMessage(FOUNDNODEMSG, [TARGETHASHTAG], ['20s'], [HASHTAG,IPTAG,PORTTAG], ['20s','4B','H'])
PROTOS[4] = TransportMessage(PAYLOADMSG, [], [])

REVERSE_PROTOS = {value.name : key for key, value in PROTOS.items() }

def decoder(bytestring):
	"""
	Master function to decode a bytestring.
	This requires the first byte to be a msg id.

	:param bytestring: A raw string of bytes from the wire.
	:type bytestring: bytes
	"""
	# struct.unpack('>B') will return (B,)
	tags = PROTOS[struct.unpack('>B', bytestring[:1])[0]].decode(bytestring)
	translate_to_tags(tags)
	return tags

def encoder(tags):
	"""
	Master function to encode tags.
	This function transforms the values into binary-packed
	data dependent on the TYPETAG.
	
	:param tags: A dictionary of tags and values.
	:type tags: {}
	"""
	translate_to_message(tags)
	try:
		return PROTOS[tags[TYPETAG]].encode(tags)
	# If we have a payload.
	except KeyError:
		return PROTOS[tags[PTYPETAG]].encode(tags)



if __name__ == "__main__":
	print(REVERSE_PROTOS)

	protoNum = 1
	data = struct.pack('>BH20s', protoNum, 5403, b'09876543210987654321')
	tags = PROTOS[protoNum].decode(data)
	print(PROTOS[protoNum].name, tags)
#	print('Same:', data == PROTOS[0].encode(tags))
	print('Same:', data == encoder(tags))

	protoNum = 3
	data = struct.pack('>BH20s20s4BH', protoNum, 332, b'09876543210987654321', \
		b'12345678901234567890', 192,168,2,1, 758)
	tags = PROTOS[protoNum].decode(data)
	print(PROTOS[protoNum].name, tags)
	print('Same:', data == PROTOS[protoNum].encode(tags))


