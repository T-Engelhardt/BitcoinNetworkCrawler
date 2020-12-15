import time
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
import BitcoinNetworkClient.Network.bitcoinConnection as bitcoinConnection
import threading
import logging

class responseHandlerData():
    
    def __init__(self, bitcoinConnection:  bitcoinConnection, chain: str, sendEvent: threading.Event):
        self.recvCmdLock = threading.Lock()
        self.recvCmd = []

        self.sendCmdLock = threading.Lock()
        self.sendCmd = []

        self.sendNextMsgLock = threading.Lock()
        self.sendNextMsg = None

        self.chain = chain
        
        self.cBitcoinConnection = bitcoinConnection
        self.sendEvent = sendEvent

        self.noPayloadFound = b''
        self.noPayloadFoundLock = threading.Lock()

    def getBitcoinConnection(self) -> bitcoinConnection:
        return self.cBitcoinConnection

    def getSendEvent(self) -> threading.Event:
        return self.sendEvent

    def getChain(self) -> str:
        return self.chain

    #SEND CMD
    def addSendCmd(self, Object: str):
        logging.debug('Write: Waiting for lock -> cmd[]')
        self.sendCmdLock.acquire()
        try:
            logging.debug('Write: Acquired lock -> cmd[]')
            self.sendCmd.append(Object)
        finally:
            self.sendCmdLock.release()
    
    def getSendCmd(self):
        logging.debug('Read: Waiting for lock -> cmd[]')
        self.sendCmdLock.acquire()
        try:
            logging.debug('Read: Acquired lock -> cmd[]')
            return self.sendCmd
        finally:
            self.sendCmdLock.release()

    #RECIVE CMD
    def addRecvCmd(self, Object: str):
        logging.debug('Write: Waiting for lock -> recvCmd')
        self.recvCmdLock.acquire()
        try:
            logging.debug('Write: Acquired lock -> recvCmd')
            #Reset recvCmd
            if(Object == "RECV_CMD_RESET"):
                self.recvCmd = []
            else:
                self.recvCmd.append(Object)
        finally:
            self.recvCmdLock.release()
    
    def getRecvCmd(self):
        logging.debug('Read: Waiting for lock -> recvCmd')
        self.recvCmdLock.acquire()
        try:
            logging.debug('Read: Acquired lock -> recvCmd')
            return self.recvCmd
        finally:
            self.recvCmdLock.release()

    #Next SEND MSG
    def setNextMsg(self, msg: BitcoinHeader):
        logging.debug('Write: Waiting for lock -> sendNextMsg')
        self.sendNextMsgLock.acquire()
        try:
            logging.debug('Write: Acquired lock -> sendNextMsg')
            self.sendNextMsg = msg
        finally:
            self.sendNextMsgLock.release()

    def getNextMsg(self):
        logging.debug('Read: Waiting for lock -> sendNextMsg')
        self.sendNextMsgLock.acquire()
        try:
            logging.debug('Read: Acquired lock -> sendNextMsg')
            return self.sendNextMsg
        finally:
            self.sendNextMsgLock.release()
