from BitcoinNetworkClient.Network.responseHandlerData import responseHandlerData
import json
import threading
import logging
from time import sleep, time
from BitcoinNetworkClient.BitcoinData.bitcoinParser import BitcoinEndcoder, cutBitcoinMsg
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
from BitcoinNetworkClient.util.data2 import NetworkAddress, Vstr, services
from BitcoinNetworkClient.util.data1 import Bint, Endian, data1util
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import version
import ipaddress
import random

class responseHandlerThread(threading.Thread):

    def __init__(self, threadID: int, responseHandlerData: responseHandlerData, recvMsg: bytes):
        threading.Thread.__init__(self)
        self.name = ("responseHandlerThread " + str(threadID))
        self.cResponseHandlerData = responseHandlerData
        self.recvMsg = recvMsg

    def run(self):
        #cut if more then one message
        cutMsg = cutBitcoinMsg(self.recvMsg, self.cResponseHandlerData.getChain())
        cutMsgArray = cutMsg.getArrayMsg()
        for data in cutMsgArray:
            try:
                tmp = BitcoinHeader(data)
                self.cResponseHandlerData.addRecvCmd(tmp.getDir()["cmd"])
                json_object = json.dumps(tmp, indent = 4, cls=BitcoinEndcoder)   
                print(json_object)
            except Exception as e:
                #no valid payload was found
                logging.debug(e)
        self.handleResponse()

    def handleResponse(self):
        cmd = self.cResponseHandlerData.getRecvCmd()
        if(len(cmd) > 0):
            if(cmd[-1] == "verack"):
                self.cResponseHandlerData.setNextMsg(self.cResponseHandlerData.getBitcoinConnection().VerackMsg())
                self.cResponseHandlerData.getSendEvent().set()
