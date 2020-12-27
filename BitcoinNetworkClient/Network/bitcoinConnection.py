from __future__ import annotations
import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import threading
    from mysql.connector import pooling

from BitcoinNetworkClient.Network.responseHandlerThread import responseHandlerThread
from BitcoinNetworkClient.Network.responseHandlerData import responseHandlerData
from BitcoinNetworkClient.db.dbBitcoinCon import dbBitcoinCon

from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import version
from BitcoinNetworkClient.util.data2 import NetworkAddress, Vstr, services
from BitcoinNetworkClient.util.data1 import Bint, Endian

from typing import List
from time import time
import ipaddress
import random


class bitcoinConnection:

    def __init__(self, motherThreadID: int, qdata: list, sendEvent: threading.Event, pool: pooling.MySQLConnectionPool):
        self.ip = qdata[0]
        self.port = qdata[1]
        self.chain = qdata[2]

        self.motherThreadID = motherThreadID

        self.db = dbBitcoinCon(pool, self.chain, self.ip, self.port)

        self.sendEvent = sendEvent
        self.KeepAlive = True

        self.cResponseHandlerData = responseHandlerData(self.motherThreadID)
        self.responseThreads = []

    def initConnection(self):
        self.cResponseHandlerData.setNextMsg(self.VersionMsg())
        self.sendEvent.set()

    def recvMsg(self, id: int, msg: bytes):
        thread = responseHandlerThread(id, self.cResponseHandlerData, msg, self)
        self.responseThreads.append(thread)
        thread.start()

    def getSendMsg(self):
        return self.cResponseHandlerData.getNextMsg()

    def getSendEvent(self) -> threading.Event:
        return self.sendEvent

    def getDbBitcoinCon(self) -> dbBitcoinCon:
        return self.db

    def getKeepAlive(self):
        return self.KeepAlive

    def signalKillConnection(self):
        self.KeepAlive = False

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
        return self.ip

    def getPort(self) -> int:
        return self.port

    def getChain(self) -> str:
        return self.chain

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
            "chain": self.chain,
            "cmd": "version",
            "payload": tmp
        })

    def verackMsg(self):
        return BitcoinHeader({
            "chain": self.chain,
            "cmd": "verack",
            "payload": b''
        })
    
    def getaddrMsg(self):
        return BitcoinHeader({
            "chain": self.chain,
            "cmd": "getaddr",
            "payload": b''
        })

    def pongMsg(self, nonce):
        return BitcoinHeader({
            "chain": self.chain,
            "cmd": "pong",
            "payload": nonce
        })