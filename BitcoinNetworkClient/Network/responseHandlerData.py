from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader

import threading
import logging


class responseHandlerData():
    
    def __init__(self, motherTreadID: int):
        self.recvCmdLock = threading.Lock()
        self.recvCmd = []

        self.sendCmdLock = threading.Lock()
        self.sendCmd = []

        self.sendNextMsgLock = threading.Lock()
        self.sendNextMsg = None

        self.motherTreadID = motherTreadID

    def getMotherTreadID(self):
        return self.motherTreadID

    #SEND CMD
    def addSendCmd(self, Object: str):
        logging.debug('Write: Waiting for lock -> sendCMD')
        self.sendCmdLock.acquire()
        try:
            logging.debug('Write: Acquired lock -> sendCMD')
            self.sendCmd.append(Object)
        finally:
            self.sendCmdLock.release()
            logging.debug('Write: Release for lock -> sendCMD')
    
    def getSendCmd(self):
        logging.debug('Read: Waiting for lock -> sendCMD')
        self.sendCmdLock.acquire()
        try:
            logging.debug('Read: Acquired lock -> sendCMD')
            result = self.sendCmd
        finally:
            self.sendCmdLock.release()
            logging.debug('Read: Release lock -> sendCMD')
        return result

    #RECIVE CMD
    def addRecvCmd(self, Object: str):
        logging.debug('Write: Waiting for lock -> recvCMD')
        self.recvCmdLock.acquire()
        try:
            logging.debug('Write: Acquired lock -> recvCMD')
            #Reset recvCmd
            if(Object == "RECV_CMD_RESET"):
                self.recvCmd = []
            else:
                self.recvCmd.append(Object)
        finally:
            self.recvCmdLock.release()
            logging.debug('Write: Release lock -> recvCMD')
    
    def getRecvCmd(self):
        logging.debug('Read: Waiting for lock -> recvCMD')
        self.recvCmdLock.acquire()
        try:
            logging.debug('Read: Acquired lock -> recvCMD')
            result = self.recvCmd
        finally:
            self.recvCmdLock.release()
            logging.debug('Read: Release lock -> recvCMD')
        return result

    #Next SEND MSG
    def setNextMsg(self, msg: BitcoinHeader):
        logging.debug('Write: Waiting for lock -> sendNextMsg')
        self.sendNextMsgLock.acquire()
        try:
            logging.debug('Write: Acquired lock -> sendNextMsg')
            self.sendNextMsg = msg
        finally:
            self.sendNextMsgLock.release()
            logging.debug('Write: Release for lock -> sendNextMsg')

    def getNextMsg(self):
        logging.debug('Read: Waiting for lock -> sendNextMsg')
        self.sendNextMsgLock.acquire()
        try:
            logging.debug('Read: Acquired lock -> sendNextMsg')
            result = self.sendNextMsg
        finally:
            self.sendNextMsgLock.release()
            logging.debug('Read: Release lock -> sendNextMsg')
        return result
