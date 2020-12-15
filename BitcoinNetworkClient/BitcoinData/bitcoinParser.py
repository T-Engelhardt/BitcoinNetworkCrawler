#class to determine which bitcoinPayload is used form bitcoinData.Header
import binascii
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinConst, BitcoinHeader
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import addr, inv, ping, verack, version
from BitcoinNetworkClient.util.data1 import Bchar, Bint, data1util
from BitcoinNetworkClient.util.data2 import InventoryVector, NetworkAddress, Vint, Vstr, services
import json
import ipaddress

class BitcoinEndcoder(json.JSONEncoder):

    # overload method default
    def default(self, obj):

        # Match all the types you want to handle in your converter
        if isinstance(obj, ipaddress.IPv4Address):
            return str(obj)
        if isinstance(obj, ipaddress.IPv6Address):
            return str(obj)
        if isinstance(obj, bytes):
            return "Bytes[" + str(len(obj)) + "]"
        if isinstance(obj, Bint):
            return int(obj)
        if isinstance(obj, Vint):
            return int(obj)
        if isinstance(obj, Bchar):
            return str(obj)
        if isinstance(obj, Vstr):
            return str(obj)
        if isinstance(obj, NetworkAddress):
            return ({
                "time": obj.cdir["time"],
                "time[Human]": str(data1util.getTimefromBint(obj.cdir["time"])),
                "services": obj.cdir["services"],
                "IPv6/4": obj.cdir["IPv6/4"],
                "port": obj.cdir["port"]
            })
        if isinstance(obj, InventoryVector):
            return ({
                "type": obj.getTypeNamesStr(),
                "hash": obj.cdir["hash"]
            })
        if isinstance(obj, services):
            return (obj.getServicesNamesStr())  
        if isinstance(obj, BitcoinHeader):
            return ({
                "chain": obj.cdir["chain"],
                "command": obj.cdir["cmd"],
                "length": len(obj),
                "checksum": binascii.hexlify(obj.getPayloadChecksum()).decode('utf-8'),
                "payload": obj.cdir["payload"]
            })
        if isinstance(obj, version):
            return ({
                "version": obj.cdir["version"],
                "services": obj.cdir["services"],
                "timestamp": obj.cdir["timestamp"],
                "timestamp[Human]": str(data1util.getTimefromBint(obj.cdir["timestamp"])),
                "addr_recv": obj.cdir["addr_recv"],
                "addr_from": obj.cdir["addr_from"],
                "nonce": obj.cdir["nonce"],
                "user_agent": obj.cdir["user_agent"],
                "start_height": obj.cdir["start_height"],
                "relay": obj.cdir["relay"]
            })
        if isinstance(obj, verack):
            return ""
        if isinstance(obj, inv):
            return ({
                "count": obj.cdir["count"],
                "inventory": obj.cdir["inventory"]
            })
        if isinstance(obj, ping):
            return ({
                "nonce": obj.getNonce()
            })
        if isinstance(obj, addr):
            return ({
                "count": obj.cdir["count"],
                "addr_list": obj.cdir["addr_list"]
            })
        return json.JSONEncoder.default(self, obj)

class cutBitcoinMsg:

    def __init__(self, Object, chain):
        self.cchain = chain
        self.cbytes = Object
        self.cIndex = []
        self.cutBytes()

    def cutBytes(self):
        magicIndex = []
        for idx, val in enumerate(self.cbytes):
            if(idx > (len(self.cbytes) -4)):
                break
            if((int.to_bytes(BitcoinConst.MAGIC_VALUES[self.cchain][3], 1,'little', signed=False)) == (int.to_bytes(self.cbytes[idx], 1,'little', signed=False))):
                if((int.to_bytes(BitcoinConst.MAGIC_VALUES[self.cchain][2], 1,'little', signed=False)) == (int.to_bytes(self.cbytes[idx+1], 1,'little', signed=False))):
                    if((int.to_bytes(BitcoinConst.MAGIC_VALUES[self.cchain][1], 1,'little', signed=False)) == (int.to_bytes(self.cbytes[idx+2], 1,'little', signed=False))):
                        if((int.to_bytes(BitcoinConst.MAGIC_VALUES[self.cchain][0], 1,'little', signed=False)) == (int.to_bytes(self.cbytes[idx+3], 1,'little', signed=False))):
                            magicIndex.append(idx)
        
        self.cIndex = magicIndex
    
    def getArrayMsg(self):
        if(len(self.cIndex) == 0):
            return []
        if(len(self.cIndex) == 1):
            return [self.cbytes]
        if(len(self.cIndex) > 1):
            lastIndex = 0
            result = []
            for idx, val in enumerate(self.cIndex):
                #get rest of bytes [x::] -> cant use next index
                if(idx == len(self.cIndex)-1):
                    lastIndex = val
                    break
                result.append(self.cbytes[val:self.cIndex[idx+1]])
            result.append(self.cbytes[lastIndex::])
            return result
            

    