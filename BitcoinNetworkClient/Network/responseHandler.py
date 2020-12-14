import json
import threading
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

class responseHandler:

    def __init__(self):
        self.cmd = []

    def receivedData(self, Object, chain):
        cutMsg = cutBitcoinMsg(Object, chain)
        cutMsgArray = cutMsg.getArrayMsg()
        for data in cutMsgArray:
            try:
                tmp = BitcoinHeader(data)
                self.cmd.append(tmp.getDir()["cmd"])
                json_object = json.dumps(tmp, indent = 4, cls=BitcoinEndcoder)   
                print(json_object)
            except:
                pass

    def getLastCmd(self):
        #return last cmd from Bitcoin Message and deletes old cmd
        result = self.cmd
        self.cmd = []
        return result