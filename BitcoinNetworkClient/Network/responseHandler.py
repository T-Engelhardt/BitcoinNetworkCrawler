import json
import threading
import logging
from time import time
from BitcoinNetworkClient.BitcoinData.bitcoinParser import BitcoinEndcoder, cutBitcoinMsg
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
from BitcoinNetworkClient.util.data2 import NetworkAddress, Vstr, services
from BitcoinNetworkClient.util.data1 import Bint, Endian, data1util
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import version
import ipaddress
import random

'''
class responseHandlerThread(threading.Thread):

    def __init__(self, threadID, handler, msg):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.handler = handler
        self.msg = msg
        
    #TODO
    def run(self):
        print("Starting Recv " + self.name)
        print(self.msg)
'''

class responseHandlerThread(threading.Thread):

    def __init__(self, threadID, respData, msg):
        threading.Thread.__init__(self)
        self.name = ("responseHandlerThread " + str(threadID))
        self.respData = respData
        self.msg = msg

    def run(self):
        cutMsg = cutBitcoinMsg(self.msg, self.respData.chain)
        cutMsgArray = cutMsg.getArrayMsg()
        for data in cutMsgArray:
            try:
                tmp = BitcoinHeader(data)
                self.respData.addCmd(tmp.getDir()["cmd"])
                json_object = json.dumps(tmp, indent = 4, cls=BitcoinEndcoder)   
                print(json_object)
            except:
                pass
        self.handleResponse()

    def handleResponse(self):
        cmd = self.respData.getCmd()
        if(len(cmd) > 0):
            if(cmd[-1] == "verack"):
                self.respData.setNextMsg(self.respData.bitcoinCon.VerackMsg())
                self.respData.sendEvent.set()

class responseHandlerData():
    
    def __init__(self, bitcoinCon, chain, sendEvent):
        self.lock = threading.Lock()
        self.cmd = []
        self.chain = chain
        self.sendEvent = sendEvent
        self.bitcoinCon = bitcoinCon
        self.nextMsg = b''

    def addCmd(self, Object):
        logging.debug('Waiting for lock -> cmd[]')
        self.lock.acquire()
        try:
            logging.debug('Acquired lock -> cmd[]')
            self.cmd.append(Object)
        finally:
            self.lock.release()
    
    def getCmd(self):
        return self.cmd

    def setNextMsg(self, msg):
        self.nextMsg = msg

    def getNextMsg(self):
        return self.nextMsg
