
import binascii
from enum import Enum
import ipaddress
import math 
from BitcoinNetworkClient.util.data1 import Bint, Bchar, Endian, data1util


class Vint:
    
    def __init__(self, Object):
        self.cbint = type(Bint)
        self.cPrefixBytes = b''

        if(type(Object) is int):
            self.IntToVint(Object)
        elif(type(Object) is bytes):
            self.VintToBytes(Object)

    def IntToVint(self, Object):
        if Object < 253:
            self.cbint = Bint(Object, 8, Endian.LITTLE)
        elif Object <= 65535:
            self.cPrefixBytes = b'\xfd'
            self.cbint = Bint(Object, 16, Endian.BIG)
        elif Object <= 4294967295:
            self.cPrefixBytes = b'\xfe'
            self.cbint = Bint(Object, 32, Endian.BIG)
        else:
            self.cPrefixBytes = b'\xff'
            self.cbint = Bint(Object, 64, Endian.BIG)

    def VintToBytes(self, Object):
        if Object[0] < 253:
            self.cbint = Bint(Object[0], 8, Endian.LITTLE)
        elif Object[0] <= 65535:
            self.cPrefixBytes = b'\xfd'
            self.cbint = Bint(Object[1:3], 16, Endian.BIG)
        elif Object[0] <= 4294967295:
            self.cPrefixBytes = b'\xfe'
            self.cbint = Bint(Object[1:5], 32, Endian.BIG)
        else:
            self.cPrefixBytes = b'\xff'
            self.cbint = Bint(Object[1:9], 64, Endian.BIG)

    def __int__(self):
        return int(self.cbint)

    def __bytes__(self):
        return self.cPrefixBytes + bytes(self.cbint)

    def __len__(self):
        return len(bytes(self))

    def getHex(self):
        ihex = binascii.hexlify(bytes(self))
        return ihex.decode('utf-8')

class Vstr:
    
    def __init__(self, Object):
        self.cVint = type(Vint)
        self.cBchar = type(Bchar)

        if(type(Object) is str):
            self.strToVstr(Object)
        elif(type(Object) is bytes):
            self.VstrTostr(Object)

    def strToVstr(self, Object):
        self.cBchar = Bchar(Object, 0, Endian.LITTLE)
        self.cVint = Vint(len(self.cBchar))

    def VstrTostr(self, Object):
        if(len(Object) > 0 and len(Object) <= 1):
            self.cVint = Vint(Object[0])
        elif(len(Object) > 1 and len(Object) <= 3):
            self.cVint = Vint(Object[0:3])
        elif(len(Object) > 3 and len(Object) <= 5):
            self.cVint = Vint(Object[0:5])
        elif(len(Object) > 5 and len(Object) <= 9):
            self.cVint = Vint(Object[0:9])
        else:
            self.cVint = Vint(Object[0:9])

        self.cBchar = Bchar(Object[len(self.cVint):len(self.cVint)+int(self.cVint)], int(self.cVint), Endian.LITTLE)

        if(int(self.cVint) != len(self.cBchar)):
            raise Exception("Vstr size is not equal")

    def getHex(self):
        ihex = binascii.hexlify(bytes(self))
        return ihex.decode('utf-8')

    def __bytes__(self):
        return bytes(self.cVint) + bytes(self.cBchar)

    def __str__(self):
        return str(self.cBchar)

    def __len__(self):
        return len(self.cVint) + len(self.cBchar)

class NetworkAddress:
    
    '''
    test1 = NetworkAddress({
        "time": Bint(data1util.getByteTime(), 32, Endian.BIG),
        "services": services([services.SERVICES_FLAG.NODE_NETWORK]),
        "IPv6/4": ipaddress.ip_address('10.0.0.1'),
        "port": Bint(8333, 16, Endian.BIG)
        })
    '''

    def __init__(self, Object):
        self.cdir = {
            "time": type(Bint),
            "services": type(services),
            "IPv6/4": type(ipaddress),
            "port": type(Bint)
        }
        self.cbytes = b''

        if(type(Object) is bytes):
            self.cbytes = Object
            self.bytesToNA(Object)
        else:
            self.cdir = Object

    def bytesToNA(self, Object):
        #with time
        if(len(Object) == 30):
            self.cdir["time"] = Bint(Object[0:4], 32, Endian.BIG)
            cutObject = Object[4::]
        else:
            self.cdir["time"] = Bint(0, 32, Endian.BIG)
            cutObject = Object

        #services
        self.cdir["services"] = services(cutObject[0:8])
        #65535 is \x00..\xFF\xFF
        if(int(Bint(cutObject[8:20], 12, Endian.BIG)) == 65535):
            #ipv4
            self.cdir["IPv6/4"] = ipaddress.ip_address(cutObject[20:24])
        else:
            #ipv6
            self.cdir["IPv6/4"] = ipaddress.ip_address(cutObject[8:24])
        #port
        self.cdir["port"] = Bint(cutObject[24:26], 16, Endian.BIG)

    def __bytes__(self):
        if(len(self.cbytes) == 0):
            #time
            if(int(self.cdir["time"]) != 0):
                self.cbytes += bytes(self.cdir["time"])
            #service
            self.cbytes += bytes(self.cdir["services"])
            #ip
            if(self.cdir["IPv6/4"].version == 4):
                self.cbytes += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF'
            self.cbytes += self.cdir["IPv6/4"].packed
            #port
            self.cbytes += bytes(self.cdir["port"])
        
        return self.cbytes

    def __len__(self):
        return len(bytes(self))

    def getDir(self):
        return self.cdir

    def getTime(self):
        return data1util.getTimefromBint(self.cdir["time"])

    def getServices(self):
        return self.cdir["services"]

    def getIP(self):
        return self.cdir["IPv6/4"]

    def getPort(self):
        return self.cdir["port"]

class services:

    class SERVICES_FLAG(Enum):
        #log2(1,2,4,8,1024)
        #bit position
        NODE_NETWORK = 0 #1
        NODE_GETUTXO  = 1 #2
        NODE_BLOOM = 2 #4
        NODE_WITNESS = 3 #8
        NODE_NETWORK_LIMITED = 10 #1024

    def __init__(self, Object):

        self.cbytes = b''
        self.cservices = "" #hex
        self.cservicesNames = []

        if(type(Object) is bytes):
            self.cbytes = Object
            self.bytesToDir()
        else:
            self.cservicesNames = Object
            self.StrToBytes()

    def bytesToDir(self):
        #hex of services
        iBint = Bint(data1util.swapBytes(self.cbytes), 64, Endian.BIG)
        self.cservices = iBint.getHex()
        #get bit from services
        #https://stackoverflow.com/a/4859937
        binServices = bin(int(self.cservices, 16))[2:].zfill(64)
        #find bit pos with 1
        #transverse backwards trough 64 bit
        posServices = []
        posIndex = 63
        for idx, val in enumerate(binServices):
            if(val == bin(1).strip('0b')):
                posServices.append(posIndex)
            posIndex -= 1
        
        #compare pos with bit heigth of flags
        for x in self.SERVICES_FLAG:
            if(x.value in posServices):
                self.cservicesNames.append(x)

    def StrToBytes(self):
        iFlagInt = 0
        for x in self.cservicesNames:
            #2^bitPos
            iFlagInt += (math.pow(2, x.value))
        
        iFlagBin = Bint(int(iFlagInt), 64, Endian.BIG)
        self.cservices = iFlagBin.getHex()
        self.cbytes = data1util.swapBytes(bytes(iFlagBin))

    def getServicesNamesEnum(self):
        return self.cservicesNames

    def getServicesNamesStr(self):
        result = []
        for x in self.cservicesNames:
            result.append(x.name)
        return result
    
    def getServicesHex(self):
        return self.cservices
    
    def __bytes__(self):
        return self.cbytes