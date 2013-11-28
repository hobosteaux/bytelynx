#!/usr/bin/python3
from contact import Hash
from struct import pack

a = Hash(pack('<B', 5))
print(a.SigBit())
print(a.ToBitString())

b = Hash(pack('<B', 7))
print(a.AbsDiff(b))
