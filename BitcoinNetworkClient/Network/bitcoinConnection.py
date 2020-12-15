import threading
from typing import List
from BitcoinNetworkClient.Network.responseHandlerThread import responseHandlerThread
from BitcoinNetworkClient.Network.responseHandlerData import responseHandlerData
import random
from BitcoinNetworkClient.BitcoinData.bitcoinParser import BitcoinEndcoder, cutBitcoinMsg
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
from BitcoinNetworkClient.util.data2 import NetworkAddress, Vstr, services
from BitcoinNetworkClient.util.data1 import Bint, Endian, data1util
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import version
import ipaddress
from time import time, sleep

class bitcoinConnection:

    def __init__(self, qdata: list, sendEvent: threading.Event):
        self.ip = qdata[0]
        self.port = qdata[1]
        self.chain = qdata[2]

        self.sendEvent = sendEvent
        self.KeepAlive = True
        self.cResponseHandlerData = responseHandlerData(self, self.chain, self.sendEvent)

        self.initConnection()

    def initConnection(self):
        self.cResponseHandlerData.setNextMsg(self.VersionMsg())
        self.sendEvent.set()

    def recvMsg(self, id: int, msg: bytes):
        thread = responseHandlerThread(id, self.cResponseHandlerData, msg)
        thread.start()

    def getSendMsg(self):
        return self.cResponseHandlerData.getNextMsg()

    def getKeepAlive(self):
        return self.KeepAlive

    def killSendThread(self):
        self.cResponseHandlerData.setNextMsg(b'')
        self.cResponseHandlerData.getSendEvent().set()

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