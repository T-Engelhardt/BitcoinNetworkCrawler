from BitcoinNetworkClient.util.data2 import InventoryVector, NetworkAddress, Vint, Vstr, services
from BitcoinNetworkClient.util.data1 import Bint, Endian


class version:

    def __init__(self, Object):

        self.cdir = {
            "version": type(Bint),
            "services": type(services),
            "timestamp": type(Bint),
            "addr_recv": type(NetworkAddress),
            "addr_from": type(NetworkAddress),
            "nonce": type(Bint),
            "user_agent": type(Vstr),
            "start_height": type(Bint),
            "relay": type(int)
        }

        self.cbytes = b''
        self.clength = 0

        if(type(Object) is bytes):
            self.cbytes = Object
            self.clength = len(self.cbytes)
            self.bytesToDir(Object)
        else:
            self.cdir = Object
            self.DirToBytes()
    
    def bytesToDir(self, Object):
        self.cdir["version"] = Bint(Object[0:4], 32, Endian.LITTLE)
        self.cdir["services"] = services(Object[4:12])
        #self.cdir["services"] = Bint(Object[4:12], 32, Endian.LITTLE)
        self.cdir["timestamp"] = Bint(Object[12:20], 64, Endian.LITTLE)
        self.cdir["addr_recv"] = NetworkAddress(Object[20:46])
        self.cdir["addr_from"] = NetworkAddress(Object[46:72])
        self.cdir["nonce"] = Bint(Object[72:80], 64, Endian.LITTLE)
        #Vstr determines the length of the string
        self.cdir["user_agent"] = Vstr(Object[80::])
        offset = len(Vstr(Object[80::]))
        self.cdir["start_height"] = Bint(Object[80+offset:84+offset], 32, Endian.LITTLE)
        self.cdir["relay"] = int.from_bytes(Object[84+offset:85+offset], 'little', signed=False)

    def DirToBytes(self):
        self.cbytes += bytes(self.cdir["version"])
        self.cbytes += bytes(self.cdir["services"])
        self.cbytes += bytes(self.cdir["timestamp"])
        self.cbytes += bytes(self.cdir["addr_recv"])
        self.cbytes += bytes(self.cdir["addr_from"])
        self.cbytes += bytes(self.cdir["nonce"])
        self.cbytes += bytes(self.cdir["user_agent"])
        self.cbytes += bytes(self.cdir["start_height"])
        #relay
        if(self.cdir["relay"] == int(1)):
            self.cbytes += b'\x01'
        else:
            self.cbytes += b'\x00'
        #set length
        self.clength = len(self.cbytes)

    def getDir(self):
        return self.cdir

    def __bytes__(self):
        return self.cbytes
    
    def __len__(self):
        return self.clength

class verack:

    def __len__(self):
        return 0

    def __bytes__(self):
        return b''

class inv:

    def __init__(self, Object):
        '''
        input bytes or [InventoryVector, ...]
        '''
        self.cdir = {
            "count": type(Vint),
            "inventory": [] #type(InventoryVector)
        }

        self.cbytes = b''
        self.clength = 0

        if(type(Object) is bytes):
            self.cbytes = Object
            self.clength = len(self.cbytes)
            self.bytesToDir(Object)
        else:
            self.InvArrayToBytes(Object)

    def bytesToDir(self, Object):
        self.cdir["count"] = Vint(Object[0:9])
        #cut Vint to get inventory
        cutBytes = Object[len(self.cdir["count"])::]
        foundSize = int(len(cutBytes) / 36)
        if(int(self.cdir["count"]) != foundSize):
            raise Exception("inv Bytes: given count " + str(int(self.cdir["count"])) + " not equal to inventory of " + str(foundSize))
        for x in range(foundSize):
            self.cdir["inventory"].append(InventoryVector(cutBytes[0+(x*36):36+(x*36)]))

    def InvArrayToBytes(self, Object):
        self.cdir["inventory"] = Object
        self.cdir["count"] = Vint(len(self.cdir["inventory"]))
        self.cbytes += bytes(self.cdir["count"])
        for x in Object:
            self.cbytes += bytes(x)

    def getDir(self):
        return self.cdir

    def __bytes__(self):
        return self.cbytes
    
    def __len__(self):
        return self.clength

class ping:
    #ping or pong with nounce 
    #input bytes or Bint(Object, 64, Endian.BIG)

    def __init__(self, Object):

        self.cbytes = b''
        self.cnonce = type(Bint)

        if(type(Object) is bytes):
            self.cbytes = Object
            self.cnonce = Bint(Object, 64, Endian.BIG)
        else:
            self.cnonce = Object
            self.cbytes = bytes(Object)
            
    def getNonce(self):
        return self.cnonce
    
    def __bytes__(self):
        return self.cbytes

    def __len__(self):
        return len(self.cbytes)

class addr:

    def __init__(self, Object):
        '''
        input bytes or [NetworkAddress, ...]
        '''
        self.cdir = {
            "count": type(Vint),
            "addr_list": [] #type(NetworkAddress)
        }

        self.cbytes = b''
        self.clength = 0

        if(type(Object) is bytes):
            self.cbytes = Object
            self.clength = len(self.cbytes)
            self.bytesToDir(Object)
        else:
            self.addrArrayToBytes(Object)

    def bytesToDir(self, Object):
        #TODO
        self.cdir["count"] = Vint(Object[0:9])
        print(bytes(self.cdir["count"]))
        #cut Vint to get inventory
        cutBytes = Object[len(self.cdir["count"])::]
        foundSize = int(len(cutBytes) / 30)
        if(int(self.cdir["count"]) != foundSize):
            raise Exception("addr Bytes: given count " + str(int(self.cdir["count"])) + " not equal to inventory of " + str(foundSize))
        for x in range(foundSize):
            self.cdir["addr_list"].append(NetworkAddress(cutBytes[0+(x*30):30+(x*30)]))

    def addrArrayToBytes(self, Object):
        self.cdir["addr_list"] = Object
        self.cdir["count"] = Vint(len(self.cdir["addr_list"]))
        self.cbytes += bytes(self.cdir["count"])
        for x in Object:
            self.cbytes += bytes(x)

    def getDir(self):
        return self.cdir

    def __bytes__(self):
        return self.cbytes
    
    def __len__(self):
        return self.clength