from BitcoinNetworkClient.Network.responseHandler import responseHandler
import random
from BitcoinNetworkClient.BitcoinData.bitcoinParser import BitcoinEndcoder, cutBitcoinMsg
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
from BitcoinNetworkClient.util.data2 import NetworkAddress, Vstr, services
from BitcoinNetworkClient.util.data1 import Bint, Endian, data1util
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import version
import ipaddress
from time import time, sleep

class bitcoinConnection:

    def __init__(self, qdata):
        self.ip = qdata[0]
        self.port = qdata[1]
        self.chain = qdata[2]

        self.ckeepOpen = True
        self.handler = responseHandler()

        self.sendCmd = []
        self.recvCMD = []


    def getSendID(self, ID):
        #print("bitcoinConnection Send ", ID)
        #new connection
        if(len(self.recvCMD) == 0):
            self.sendCmd.append("cmd")
            return self.VersionMsg()
        elif(self.recvCMD[-1] == "version"):
            self.sendCmd.append("verack")
            return self.VerackMsg()
        #elif():
        #   insert new cases here not below (len(self.recvCMD) >= 2)
        #    pass
        elif(len(self.recvCMD) >= 2):
            if((self.recvCMD[-1] == "verack") and (self.recvCMD[-2] == "version")):
                self.sendCmd.append("verack")
                return self.VerackMsg()
            else:
                return self.endCase()
        else:
            return self.endCase()
            
    def endCase(self):
        #self.ckeepOpen = False
        if(self.sendCmd[-1] is not "getaddr"):
            self.sendCmd.append("getaddr")
            return self.GetAddrMsg()

    def setRecvID(self, msg, ID):
        #print("bitcoinConnection Recv ", ID)
        self.handler.receivedData(msg, self.chain)
        for cmd in self.handler.getLastCmd():
            self.recvCMD.append(cmd)

    def keepOpen(self):
        return self.ckeepOpen

    def getIP(self):
        return self.ip

    def getPort(self):
        return self.port

    def VersionMsg(self):
        tmp = version({
            "version": Bint(70013, 32, Endian.LITTLE),
            "services": services([services.SERVICES_FLAG.NODE_NETWORK_LIMITED, services.SERVICES_FLAG.NODE_WITNESS]),
            "timestamp": Bint(int(time()), 64, Endian.LITTLE),
            "addr_recv": (NetworkAddress({
                "time": Bint(0, 32, Endian.BIG),
                "services": services([services.SERVICES_FLAG.NODE_NETWORK, services.SERVICES_FLAG.NODE_WITNESS, services.SERVICES_FLAG.NODE_NETWORK_LIMITED]),
                "IPv6/4": ipaddress.ip_address('::'),
                "port": Bint(0, 16, Endian.BIG)
            })),
            "addr_from": (NetworkAddress({
                "time": Bint(0, 32, Endian.BIG),
                "services": services([services.SERVICES_FLAG.NODE_WITNESS, services.SERVICES_FLAG.NODE_NETWORK_LIMITED]),
                "IPv6/4": ipaddress.ip_address('::'),
                "port": Bint(0, 16, Endian.BIG)
            })),
            "nonce": Bint(random.getrandbits(64), 64, Endian.LITTLE),
            "user_agent": Vstr("/Satoshi:0.20.1/"),
            "start_height": Bint(0, 32, Endian.LITTLE),
            "relay": int(1)
        })

        return BitcoinHeader({
            "chain": self.chain,
            "cmd": "version",
            "payload": tmp
        })

    def VerackMsg(self):
        return BitcoinHeader({
            "chain": self.chain,
            "cmd": "verack",
            "payload": b''
        })
    
    def GetAddrMsg(self):
        return BitcoinHeader({
            "chain": self.chain,
            "cmd": "getaddr",
            "payload": b''
        })
