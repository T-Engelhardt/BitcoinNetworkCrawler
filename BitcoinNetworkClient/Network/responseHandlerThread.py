from BitcoinNetworkClient.Network.responseHandlerData import responseHandlerData
import json
import threading
import logging
from time import sleep, time
from BitcoinNetworkClient.BitcoinData.bitcoinParser import BitcoinEndcoder, cutBitcoinMsg
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
from BitcoinNetworkClient.util.data2 import NetworkAddress, Vstr, services
from BitcoinNetworkClient.util.data1 import Bint, Endian, data1util
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import ping, version
import ipaddress
import random

class responseHandlerThread(threading.Thread):

    def __init__(self, threadID: int, responseHandlerData: responseHandlerData, recvMsg: bytes):
        threading.Thread.__init__(self)
        self.name = ("responseHandlerThread " + str(threadID))
        self.cResponseHandlerData = responseHandlerData
        self.recvMsg = recvMsg
        self.recvPingNonce = b''
        self.cRecvCMD = []

    def run(self):
        #cut if more then one message
        cutMsg = cutBitcoinMsg(self.recvMsg, self.cResponseHandlerData.getChain())
        cutMsgArray = cutMsg.getArrayMsg()
        for data in cutMsgArray:
            try:
                tmp = BitcoinHeader(data)
                #no use yet
                self.cResponseHandlerData.addRecvCmd(tmp.getDir()["cmd"])
                #in use
                self.cRecvCMD.append(tmp.getDir()["cmd"])
                #safe ping nonce
                if(tmp.getDir()["cmd"] == "ping"):
                    self.recvPingNonce = tmp.getDir()["payload"]
                #dump message
                json_object = json.dumps(tmp, indent = 4, cls=BitcoinEndcoder)   
                print(json_object)
            except Exception as e:
                #no valid payload was found
                logging.debug(e)
        self.handleResponse()

    def handleResponse(self):
        cmd = self.cRecvCMD
        logging.debug("Recived CMD " + str(cmd))
        #check
        if "verack" in cmd:
            self.cResponseHandlerData.setNextMsg(self.cResponseHandlerData.getBitcoinConnection().VerackMsg())
            self.cResponseHandlerData.getSendEvent().set()
        if "ping" in cmd:
            self.cResponseHandlerData.setNextMsg(self.cResponseHandlerData.getBitcoinConnection().pong(self.recvPingNonce))
            self.cResponseHandlerData.getSendEvent().set()
