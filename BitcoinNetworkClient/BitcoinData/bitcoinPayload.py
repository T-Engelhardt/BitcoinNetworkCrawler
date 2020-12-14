from BitcoinNetworkClient.util.data2 import NetworkAddress, Vstr, services
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