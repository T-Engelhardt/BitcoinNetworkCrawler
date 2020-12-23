from datetime import datetime
from time import time
from enum import Enum
import binascii
import struct
from base64 import b32decode, b32encode
import ipaddress


class Endian(Enum):
    LITTLE = 1
    BIG = 2

class Bint:

    def __init__(self, Object, bitsize, endian):
        #length in Bytes
        self.length = int(bitsize / 8)
        self.cbytes = b''
        #init with negative value
        self.cint = int()
        self.cendian = endian

        if(type(Object) is int):
            self.cint = Object
            self.IntToBytes()
        elif(type(Object) is bytes):
            self.cbytes = Object
            self.BytesToInt()

    def IntToBytes(self):
        if self.cendian == Endian.LITTLE:
            self.cbytes = (self.cint).to_bytes(self.length, byteorder='little')
        else:    
            self.cbytes = (self.cint).to_bytes(self.length, byteorder='big')

    def BytesToInt(self):
        if self.cendian == Endian.LITTLE:
            self.cint = int.from_bytes(self.cbytes, 'little', signed=False)
        else:
            self.cint = int.from_bytes(self.cbytes, 'big', signed=False)

    def getHex(self):
        ihex = binascii.hexlify(self.cbytes)
        return ihex.decode('utf-8')

    def __int__(self):
        return self.cint
    
    def __str__(self):
        return str(self.cint)

    def __bytes__(self):
        return self.cbytes

class Bchar():
    
    def __init__(self, Object, length, endian):
        #length in Bytes
        self.length = length
        self.cbytes = b''
        self.cstr = ""
        self.cendian = endian

        if(type(Object) is str):
            self.cstr = Object
            #take string size if input length is zero
            if(self.length == 0):
                self.length = len(Object)
            self.StrtoBytes()
        elif(type(Object) is bytes):
            self.cbytes = Object
            self.length = len(Object)
            self.BytesToStr()

    def StrtoBytes(self):
        #throw exception if char to small
        if((len(self.cstr) > self.length)):
            raise Exception("Bchar is to small for input string")

        ibytes = self.cstr.encode()
        if self.cendian == Endian.BIG:
            ibytes = data1util.swapBytes(ibytes)
            ibytes = b'\x00' * (self.length - len(ibytes)) + ibytes
        else:
            ibytes = ibytes + b'\x00' * (self.length - len(ibytes))

        self.cbytes = ibytes

    def BytesToStr(self):
        istr = self.cbytes.decode('utf-8','surrogateescape')
        if self.cendian == Endian.BIG:
            self.cstr = istr[::-1]
        else:
            self.cstr = istr

    def __str__(self):
        return self.cstr

    def __bytes__(self):
        return self.cbytes
    
    def __len__(self):
        return self.length
    
    def getHex(self):
        ihex = binascii.hexlify(self.cbytes)
        return ihex.decode('utf-8')

class data1util:

    def swapBytes(Object):
        result = b''
        for x in range(len(Object) -1, -1, -1):
            result = result + Object[x].to_bytes(1, byteorder='little')
        return result

    def removeNullBytes(Object):
        result = b''
        for x in range(len(Object)):
            if not (Object[x].to_bytes(1, byteorder='little') == b'\x00'):
                result += Object[x].to_bytes(1, byteorder='little')
        return result

    def getByteTime():
        return struct.pack(">i", int(time()))

    def getTimefromBint(input):
        return datetime.fromtimestamp(int(input)).strftime("%Y-%m-%d %H:%M:%S")

    def OnionToIpv6(onion: str) -> ipaddress.IPv6Address:
        #https://github.com/bitcoin/bitcoin/blob/c7ad94428ab6f54661d7a5441e1fdd0ebf034903/contrib/seeds/generate-seeds.py
        onionPrefix = b'\xfd\x87\xd8\x7e\xeb\x43'
        if len(onion)>6 and onion.endswith('.onion'):
            vchAddr = b32decode(onion[0:-6], True)
            if len(vchAddr) != 16-len(onionPrefix):
                raise ValueError('Invalid onion %s' % vchAddr)
            #return onionPrefix + vchAddr
            return ipaddress.IPv6Address(onionPrefix + vchAddr)
        else:
            raise Exception("No Onion Addres found")

    def Ipv6ToOnion(ipv6: ipaddress.IPv6Address) -> str:
        if(ipv6.version != 6):
            raise ValueError("Invalid ipv6")
        if(ipv6.packed[0:6] != b'\xfd\x87\xd8\x7e\xeb\x43'):
            raise ValueError("Not a valid ipv6 for onion address")
        #remove Prefix -> encode bytes into str -> make it lower case -> add .onion
        return b32encode(ipv6.packed[6:]).decode("utf-8").lower() + ".onion"