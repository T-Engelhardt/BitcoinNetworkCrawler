from __future__ import annotations
import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import threading
    from mysql.connector import pooling
    from BitcoinNetworkClient.Network.bitcoinNetworkInfo import bitcoinNetInfo
    from BitcoinNetworkClient.util.configParser import config

from BitcoinNetworkClient.Network.responseHandlerThread import responseHandlerThread
from BitcoinNetworkClient.Network.responseHandlerData import responseHandlerData
from BitcoinNetworkClient.db.dbBitcoinCon import dbBitcoinCon

from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import version
from BitcoinNetworkClient.util.data2 import NetworkAddress, Vstr, services
from BitcoinNetworkClient.util.data1 import Bint, Endian

from time import time
import ipaddress
import random


class bitcoinConnection:

    def __init__(self, motherThreadID: int, qdata: bitcoinNetInfo, sendEvent: threading.Event, pool: pooling.MySQLConnectionPool, cfg: config):
        self.netInfo = qdata
        self.cfg = cfg
        self.motherThreadID = motherThreadID

        self.db = dbBitcoinCon(pool, qdata, cfg)

        self.sendEvent = sendEvent
        self.KeepAlive = True

        self.cResponseHandlerData = responseHandlerData(self.motherThreadID)
        self.responseThreads = []

        self.Addrv2 = False

    def initConnection(self):
        self.cResponseHandlerData.setNextMsg(self.VersionMsg())
        self.sendEvent.set()

    def recvMsg(self, id: int, msg: bytes):
        thread = responseHandlerThread(id, self.cResponseHandlerData, msg, self)
        self.responseThreads.append(thread)
        thread.start()

    def getSendMsg(self) ->list(BitcoinHeader):
        return self.cResponseHandlerData.getNextMsg()

    def getSendEvent(self) -> threading.Event:
        return self.sendEvent

    def getDbBitcoinCon(self) -> dbBitcoinCon:
        return self.db

    def getKeepAlive(self):
        return self.KeepAlive

    def signalKillConnection(self):
        self.KeepAlive = False

    def enableAddrV2(self):
        self.Addrv2 = True

    def getAddrV2Flag(self) -> bool:
        return self.Addrv2

    def killConnection(self):
        #wait for all repsonse operation before closing the db connection
        self.waitForChilds()
        #stop send thread
        self.killSendThread()
        #evaluate try
        self.db.evaluateTry()
        #close dbBitcoinCon
        self.db.closeDBConnection()

    def waitForChilds(self):
        # Wait for all threads to complete
        for t in self.responseThreads:
            t.join()

    def killSendThread(self):
        #close send thread
        logging.debug("Stop send Thread")
        self.cResponseHandlerData.setNextMsg(None)
        self.sendEvent.set()

    def getIP(self) -> str:
        return self.netInfo.getIP()

    def getPort(self) -> int:
        return self.netInfo.getPort()

    def getChain(self) -> str:
        return self.netInfo.getChain()

    def VersionMsg(self):
        tmp = version({
            "version": Bint(70016, 32, Endian.LITTLE),
            "services": services([]),
            "timestamp": Bint(int(time()), 64, Endian.LITTLE),
            "addr_recv": (NetworkAddress({
                "time": Bint(0, 32, Endian.BIG),
                "services": services([]),
                "IPv6/4": ipaddress.ip_address('::'),
                "port": Bint(0, 16, Endian.BIG)
            })),
            "addr_from": (NetworkAddress({
                "time": Bint(0, 32, Endian.BIG),
                "services": services([]),
                "IPv6/4": ipaddress.ip_address('::'),
                "port": Bint(0, 16, Endian.BIG)
            })),
            "nonce": Bint(random.getrandbits(64), 64, Endian.LITTLE),
            "user_agent": Vstr("/Satoshi:0.21.0/"),
            "start_height": Bint(1, 32, Endian.LITTLE),
            "relay": int(0)
        })

        return BitcoinHeader({
            "chain": self.netInfo.getChain(),
            "cmd": "version",
            "payload": tmp
        })

    def sendAddrV2(self):
        return BitcoinHeader({
            "chain": self.netInfo.getChain(),
            "cmd": "sendaddrv2",
            "payload": b''
        })

    def verackMsg(self):
        return BitcoinHeader({
            "chain": self.netInfo.getChain(),
            "cmd": "verack",
            "payload": b''
        })
    
    def getaddrMsg(self):
        return BitcoinHeader({
            "chain": self.netInfo.getChain(),
            "cmd": "getaddr",
            "payload": b''
        })

    def pongMsg(self, nonce):
        return BitcoinHeader({
            "chain": self.netInfo.getChain(),
            "cmd": "pong",
            "payload": nonce
        })