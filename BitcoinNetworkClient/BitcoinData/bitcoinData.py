from BitcoinNetworkClient.util.data1 import Bint, Bchar, Endian, data1util
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import addr, inv, ping, version

import hashlib


class BitcoinConst:

    MAGIC_VALUES = {
        "main": b'\xd9\xb4\xbe\xf9',
        "regtest": b'\xda\xb5\xbf\xfa',
        "testnet3": b'\x07\x09\x11\x0b'
    }

class BitcoinHeader:

    def __init__(self, Object):
        self.cdir = {
            "chain": "",
            "cmd": "",
            "payload": b''
        }
        self.PayloadLength = 0
        self.HeaderBytes = b''
        self.PayloadBytes = b''
        self.PayloadChecksum = b''

        if(type(Object) is bytes):
            #parse Bitcoin Data and return payload with cmd
            self.createInfoFromBytes(Object)
        else:
            #create Bitcoin Data with Header
            self.cdir = Object
            self.createHeader(Object)

    def createHeader(self, Object):
        #magic
        if(self.cdir["chain"] == "main"):
            self.HeaderBytes += data1util.swapBytes(BitcoinConst.MAGIC_VALUES["main"])
        elif(self.cdir["chain"] == "regtest"):
            self.HeaderBytes += data1util.swapBytes(BitcoinConst.MAGIC_VALUES["regtest"])
        elif(self.cdir["chain"] == "testnet3"):
            self.HeaderBytes += data1util.swapBytes(BitcoinConst.MAGIC_VALUES["testnet3"])
        else:
            raise Exception("Dir BitcoinHeader: no valid chain declared")
        #cmd
        self.HeaderBytes += bytes(Bchar(self.cdir["cmd"], 12, Endian.LITTLE))
        #payload length
        self.HeaderBytes += bytes(Bint(len(self.cdir["payload"]), 32, Endian.LITTLE))
        self.PayloadLength = len(self.cdir["payload"])
        #checksum payload
        payloadhash = hashlib.sha256((hashlib.sha256(bytes(self.cdir["payload"])).digest())).digest()
        self.HeaderBytes +=payloadhash[0:4]
        self.PayloadChecksum = payloadhash[0:4]
        #add payload to class
        self.PayloadBytes = bytes(self.cdir["payload"])

    def createInfoFromBytes(self, Object):
        #check if Header is atleast 24Bytes
        if(len(Object) < 24):
            raise Exception("Bytes BitcoinHeader: Header to small")
        #cut Data in pieces
        self.HeaderBytes = Object[0:24]
        self.PayloadBytes = Object[24::]
        #set length but minus the 24 byte header
        self.PayloadLength = len(self.PayloadBytes)
        #build Dir in Class
        #getchain
        if(self.HeaderBytes[0:4] == data1util.swapBytes(BitcoinConst.MAGIC_VALUES["main"])):
            self.cdir["chain"] = "main"
        elif(self.HeaderBytes[0:4] == data1util.swapBytes(BitcoinConst.MAGIC_VALUES["regtest"])):
            self.cdir["chain"] = "regtest"
        elif(self.HeaderBytes[0:4] == data1util.swapBytes(BitcoinConst.MAGIC_VALUES["testnet3"])):
            self.cdir["chain"] = "testnet3"
        else:
            raise Exception("Bytes BitcoinHeader: no valid chain found")
        #getcmd
        self.cdir["cmd"] = str(Bchar(data1util.removeNullBytes(self.HeaderBytes[4:16]), 12, Endian.LITTLE)) 
        #check given length
        if(int(Bint(self.HeaderBytes[16:20], 32, Endian.LITTLE)) != self.PayloadLength):
            raise Exception("Bytes BitcoinHeader: "+ str(int(Bint(self.HeaderBytes[16:20], 32, Endian.LITTLE))) +" given Payload length not equal to " + str(self.PayloadLength))
        #check given payload hash
        payloadhash = hashlib.sha256((hashlib.sha256(self.PayloadBytes).digest())).digest()
        if(self.HeaderBytes[20:24] != payloadhash[0:4]):
            raise Exception("Bytes BitcoinHeader: given hash is not equal")
        else:
            #TODO dont use bytes instead use class in bitcoinPayload
            self.PayloadChecksum = payloadhash[0:4]
            if(self.cdir["cmd"] == "version"):
                 self.cdir["payload"] = version(self.PayloadBytes)
            elif(self.cdir["cmd"] == "inv"):
                self.cdir["payload"] = inv(self.PayloadBytes)
            elif(self.cdir["cmd"] == "ping"):
                self.cdir["payload"] = ping(self.PayloadBytes)
            elif(self.cdir["cmd"] == "addr"):
                self.cdir["payload"] = addr(self.PayloadBytes)
            else:
                self.cdir["payload"] = self.PayloadBytes

    def __bytes__(self):
        return self.HeaderBytes + self.PayloadBytes

    def getPayloadBytes(self):
        return self.PayloadBytes

    def getPayloadChecksum(self):
        return self.PayloadChecksum

    def getHeader(self):
        return self.HeaderBytes

    def getDir(self):
        return self.cdir

    def __len__(self):
        '''
        returns the length of the payload NOT the Header
        Header is 24 Bytes
        '''
        return self.PayloadLength
