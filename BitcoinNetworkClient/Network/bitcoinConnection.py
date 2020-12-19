from __future__ import annotations
import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import threading

from BitcoinNetworkClient.Network.responseHandlerThread import responseHandlerThread
from BitcoinNetworkClient.Network.responseHandlerData import responseHandlerData
from BitcoinNetworkClient.db.dbConnector import dbConnector

from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import version
from BitcoinNetworkClient.util.data2 import NetworkAddress, Vstr, services
from BitcoinNetworkClient.util.data1 import Bint, Endian


from typing import List
from time import time
import ipaddress
import random


class bitcoinConnection:

    def __init__(self, qdata: list, sendEvent: threading.Event):
        self.ip = qdata[0]
        self.port = qdata[1]
        self.chain = qdata[2]

        logging.debug("Open DB connection")
        self.db = dbConnector()
        self.db.insertJson(self.chain, self.ip, self.port, None)

        self.sendEvent = sendEvent
        self.KeepAlive = True
        self.cResponseHandlerData = responseHandlerData(self, self.chain, self.sendEvent, self.db)

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

    def setKeepAlive(self, Flag: bool):
        self.KeepAlive = Flag

    def closeDBConnection(self):
        #close db connection
        logging.debug("Close DB connection")
        self.db.close()

    def killSendThread(self):
        self.closeDBConnection()
        #close send thread
        logging.debug("Stop send Thread")
        self.cResponseHandlerData.setNextMsg(None)
        self.cResponseHandlerData.getSendEvent().set()

    def getIP(self):
        return self.ip

    def getPort(self):
        return self.port

    def getChain(self):
        return self.chain

    def VersionMsg(self):
        tmp = version({
            "version": Bint(70015, 32, Endian.LITTLE),
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
            "user_agent": Vstr("/Satoshi:0.20.1/"),
            "start_height": Bint(0, 32, Endian.LITTLE),
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