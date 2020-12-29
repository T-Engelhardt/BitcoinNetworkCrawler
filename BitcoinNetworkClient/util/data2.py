from BitcoinNetworkClient.util.data1 import Bint, Bchar, Endian, data1util
from BitcoinNetworkClient.util.serviceEnum import SERVICES_FLAG

import logging
import binascii
from enum import Enum
import ipaddress
import math
from base64 import b32decode, b32encode
import hashlib


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
            self.cbint = Bint(Object, 16, Endian.LITTLE)
        elif Object <= 4294967295:
            self.cPrefixBytes = b'\xfe'
            self.cbint = Bint(Object, 32, Endian.LITTLE)
        else:
            self.cPrefixBytes = b'\xff'
            self.cbint = Bint(Object, 64, Endian.LITTLE)

    def VintToBytes(self, Object):
        if Object[0] < 253:
            self.cbint = Bint(Object[0], 8, Endian.LITTLE)
        elif Object[0] < 254:
            self.cPrefixBytes = b'\xfd'
            self.cbint = Bint(Object[1:3], 16, Endian.LITTLE)
        elif Object[0] < 255:
            self.cPrefixBytes = b'\xfe'
            self.cbint = Bint(Object[1:5], 32, Endian.LITTLE)
        else:
            self.cPrefixBytes = b'\xff'
            self.cbint = Bint(Object[1:9], 64, Endian.LITTLE)

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
        "services": services([SERVICES_FLAG.NODE_NETWORK]),
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
            self.cdir["time"] = Bint(Object[0:4], 32, Endian.LITTLE)
            cutObject = Object[4::]
        else:
            self.cdir["time"] = Bint(0, 32, Endian.LITTLE)
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

    def __init__(self, Object):

        self.cbytes = b''
        self.cservices = "" #hex
        self.cservicesNames = []
        self.cservicesInt = 0

        if(type(Object) is bytes):
            self.cbytes = Object
            self.bytesToDir()
        elif(type(Object) is int):
            self.intToServiceNames(Object)
            self.StrToBytesInt()
        else:
            self.cservicesNames = Object
            self.StrToBytesInt()

    def bytesToDir(self):
        #hex and int of services
        iBint = Bint(data1util.swapBytes(self.cbytes), 64, Endian.BIG)
        self.cservicesInt = int(iBint)
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
        for x in SERVICES_FLAG:
            if(x.value in posServices):
                self.cservicesNames.append(x)

    def StrToBytesInt(self):
        #creates bytes and int representation
        iFlagInt = 0
        for x in self.cservicesNames:
            #2^bitPos
            iFlagInt += (math.pow(2, x.value))
        
        self.cservicesInt = int(iFlagInt)
        iFlagBin = Bint(int(iFlagInt), 64, Endian.BIG)
        self.cservices = iFlagBin.getHex()
        self.cbytes = data1util.swapBytes(bytes(iFlagBin))

    def intToServiceNames(self, servInt: int):
        tmp = 0
        #substract value from int if < 0 flag is not possible
        for x in reversed(SERVICES_FLAG):
            #2^bitPos
            tmp = servInt - math.pow(2, x.value)
            if(tmp < 0):
                #flag not valid
                continue
            else:
                #safe substract value for next loop run
                servInt = tmp
                self.cservicesNames.append(x)
                #all flags found
                if(tmp) == 0:
                    #reverse back
                    self.cservicesNames.reverse()
                    return
        #in last iteration of the loop tmp gets -1 if int is zero
        if(tmp == -1): return
        logging.warning("Unknown Service Flag " + str(int(tmp)))
        #raise ValueError("Not a valid Int Service representation")

    def getServicesNamesEnum(self):
        return self.cservicesNames

    def getServicesNamesStr(self):
        result = []
        for x in self.cservicesNames:
            result.append(x.name)
        return result
    
    def getServicesHex(self):
        return self.cservices
    
    def __int__(self):
        return self.cservicesInt

    def __bytes__(self):
        return self.cbytes

class InventoryVector:

    class INV_TYPE(Enum):
        ERROR = 0 
        MSG_TX = 1 
        MSG_BLOCK = 2 
        MSG_FILTERED_BLOCK = 3 
        MSG_WITNESS_TX  = 1073741825 #0x40000001
        MSG_WITNESS_BLOCK = 1073741826 #0x40000002
        MSG_FILTERED_WITNESS_BLOCK = 1073741827 #0x40000003

    def __init__(self, Object):
        '''
        test1 = InventoryVector({
        "type": InventoryVector.INV_TYPE.MSG_TX,
        "hash": "154c7d908a5f5d7f572bc184fd076f4ff91a3f364124dfcd822e09ccc8f15591"
        })
        test1 = InventoryVector({
        "type": InventoryVector.INV_TYPE.MSG_WITNESS_BLOCK,
        "hash": "0000000000000249ce1813cbbff7ef80b014e43752acac2fbd98e3e69a6a9fd2"
        })
        '''
        self.cdir = {
            "type": type(InventoryVector.INV_TYPE),
            "hash": "" #hex
        }

        self.cbytes = b''
        self.TypeNames = type(InventoryVector.INV_TYPE)

        if(type(Object) is bytes):
            self.cbytes = Object
            self.bytesToDir()
        else:
            self.cdir = Object
            self.DirToBytes()
    
    def bytesToDir(self):
        #get value of Type
        intType = int(Bint(data1util.swapBytes(self.cbytes[0:4]), 32, Endian.BIG))
        #get Type from value
        for x in InventoryVector.INV_TYPE:
            if(x.value == intType):
                self.TypeNames = x
        self.cdir["type"] = self.TypeNames
        #hash
        hash = Bchar(data1util.swapBytes(self.cbytes[4::]), 32 , Endian.LITTLE)
        self.cdir["hash"] = hash.getHex()

    def DirToBytes(self):
        self.cbytes += bytes(Bint(self.cdir["type"].value, 32, Endian.LITTLE))
        self.cbytes += data1util.swapBytes(bytearray.fromhex(self.cdir["hash"]))

    def getTypeNamesStr(self):
        return self.TypeNames.name

    def __bytes__(self):
        return self.cbytes
    
    def __len__(self):
        #fixed length
        return len(self.cbytes)

class NetworkAddressV2:

    #get length from data1 util
    class NETWORK_ID(Enum):
        IPV4 = 1
        IPV6  = 2
        TORV2 = 3
        TORV3 = 4
        I2P = 5
        CJDNS = 6

    def __init__(self, Object):

        self.cdir = {
            "time": type(Bint),
            "services": type(services),
            "networkID": type(NetworkAddressV2.NETWORK_ID),
            "addr[bytes]": type(bytes),
            "addr": "TBD",
            "port": type(Bint)
        }
        self.cbytes = b''
        self.cdir = Object
        self.createIPString()

        #TODO create bytes
        #self.bytesToNA(Object)

    def createIPString(self):
        if(self.cdir["networkID"] == NetworkAddressV2.NETWORK_ID.IPV4):
            self.cdir["addr"] = ipaddress.IPv4Address(self.cdir["addr[bytes]"])
        elif(self.cdir["networkID"] == NetworkAddressV2.NETWORK_ID.IPV6):
            self.cdir["addr"] = ipaddress.IPv6Address(self.cdir["addr[bytes]"])
        elif(self.cdir["networkID"] == NetworkAddressV2.NETWORK_ID.TORV2):
            self.cdir["addr"] = onionV2(self.cdir["addr[bytes]"])
        elif(self.cdir["networkID"] == NetworkAddressV2.NETWORK_ID.TORV3):
            self.cdir["addr"] = onionV3(self.cdir["addr[bytes]"])
        else:
            logging.warning("Unimplemented Network ID" + self.cdir["networkID"].name)
            print(self.cdir["addr[bytes]"])

    def bytesToNA(self, Object):
        raise Exception("Not implemented yet")

    def __bytes__(self):        
        return self.cbytes

    def __len__(self):
        return len(bytes(self))

    def getDir(self):
        return self.cdir

class NetworkAddressV2Helper:
    
    def getLengthNetworkID(id: NetworkAddressV2.NETWORK_ID) -> int:

        if(id == NetworkAddressV2.NETWORK_ID.IPV4):
            return 4
        elif(id == NetworkAddressV2.NETWORK_ID.IPV6):
            return 16
        elif(id == NetworkAddressV2.NETWORK_ID.TORV2):
            return 10
        elif(id == NetworkAddressV2.NETWORK_ID.TORV3):
            return 32
        elif(id == NetworkAddressV2.NETWORK_ID.I2P):
            return 32
        elif(id == NetworkAddressV2.NETWORK_ID.CJDNS):
            return 16
        else:
            raise Exception("No Valid Network ID with length found")

    def getNetworkID(id: bytes) -> NetworkAddressV2.NETWORK_ID:

        if(id == b'\x01'):
            return NetworkAddressV2.NETWORK_ID.IPV4
        elif(id == b'\x02'):
            return NetworkAddressV2.NETWORK_ID.IPV6
        elif(id == b'\x03'):
            return NetworkAddressV2.NETWORK_ID.TORV2
        elif(id == b'\x04'):
            return NetworkAddressV2.NETWORK_ID.TORV3
        elif(id == b'\x05'):
            return NetworkAddressV2.NETWORK_ID.I2P
        elif(id == b'\x06'):
            return NetworkAddressV2.NETWORK_ID.CJDNS
        else:
            raise Exception("No Valid Network ID found")

class onionV2():

    def __init__(self, Object):

        self.cbytes = b''
        self.cStr = ""

        if(type(Object) is bytes):
            self.bytesToStr(Object)
        else:
            self.strToBytes(Object)

    def bytesToStr(self, onion: bytes):
        baseString = b32encode(onion).decode("utf-8").lower()
        if(len(baseString) != 16):
            raise ValueError('Invalid onion %s', baseString)
        self.cStr = baseString + ".onion"

    def strToBytes(self, onion: str):
        if len(onion)>6 and onion.endswith('.onion'):
            vchAddr = b32decode(onion[0:-6], True)
            if len(vchAddr) != 10:
                raise ValueError('Invalid onion %s' % vchAddr)
            self.cbytes = vchAddr
        else:
            raise Exception("No Onion Addres found")

    def __str__(self):
        return self.cStr

    def __bytes__(self):
        return self.cbytes

class onionV3():

    def __init__(self, Object):

        self.cbytes = b''
        self.cStr = ""

        if(type(Object) is bytes):
            self.bytesToStr(Object)
        else:
            self.strToBytes(Object)

    def bytesToStr(self, onion: bytes):
        '''
        https://github.com/bitcoin/bips/blob/master/bip-0155.mediawiki#appendix-b-tor-v3-address-encoding
        '''
        checksumPayload = b".onion checksum" + onion + b"\x03"
        m = hashlib.sha3_256()
        m.update(checksumPayload)
        checksum = m.digest()

        payload = onion + checksum[:2] + b"\x03"

        baseString = b32encode(payload).decode("utf-8").lower()
        if(len(baseString) != 56):
            raise ValueError('Invalid onion %s', baseString)
        self.cStr = baseString + ".onion"

    def strToBytes(self, onion: str):
        if len(onion)>6 and onion.endswith('.onion'):
            #remove .onion
            vchAddr = b32decode(onion[0:-6], True)

            if len(vchAddr) != 35:
                raise ValueError('Invalid onion %s' % vchAddr)
            
            #pubkey | H(Checksum) | Version
            if(self.validatePubKey(vchAddr[:-3], vchAddr[-3:-1], vchAddr[-1])):
                #only safe pubkey
                self.cbytes = vchAddr[:-3]
            else:
                raise ValueError("Pubkey could not be validated")
        else:
            raise Exception("No Onion Addres found")

    def validatePubKey(self, pubKey: bytes, HChecksum: bytes, version: bytes) -> bool:

        checksumPayload = b".onion checksum" + pubKey + b"\x03"
        m = hashlib.sha3_256()
        m.update(checksumPayload)
        checksumNew = m.digest()

        if(HChecksum != checksumNew[:2]):
            return False
        if(bytes([version]) != b'\03'):
            return False
        return True

    def __str__(self):
        return self.cStr

    def __bytes__(self):
        return self.cbytes