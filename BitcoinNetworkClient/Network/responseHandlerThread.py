from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from BitcoinNetworkClient.Network.responseHandlerData import responseHandlerData
    from BitcoinNetworkClient.Network.bitcoinConnection import bitcoinConnection

from BitcoinNetworkClient.BitcoinData.bitcoinParser import BitcoinEndcoder, cutBitcoinMsg
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader

import json
import threading
import logging


class responseHandlerThread(threading.Thread):

    def __init__(self, threadID: int, responseHandlerData: responseHandlerData, recvMsg: bytes , bitcoinConnection: bitcoinConnection):
        threading.Thread.__init__(self)
        self.name = ("responseHandlerThread " + str(threadID))
        self.cResponseHandlerData = responseHandlerData
        self.cBitcoinConnection = bitcoinConnection
        self.recvMsg = recvMsg

    def run(self):
        #cut if more then one message
        cutMsg = cutBitcoinMsg(self.recvMsg, self.cBitcoinConnection.getChain())
        cutMsgArray = cutMsg.getArrayMsg()
        for data in cutMsgArray:
            try:
                tmp = BitcoinHeader(data)
                #no in use yet // just tracks the recv cmd history
                self.cResponseHandlerData.addRecvCmd(tmp.getDir()["cmd"])
                #handle response
                self.handleResponse(tmp)
            except Exception as e:
                #no valid payload was found
                logging.debug(e)

    def handleResponse(self, Header: BitcoinHeader):

        cmd = Header.getDir()["cmd"]
        json_object = json.dumps(Header, indent = 4, cls=BitcoinEndcoder)
        
        if cmd == "verack":
            self.cResponseHandlerData.setNextMsg(self.cBitcoinConnection.verackMsg())
            self.cBitcoinConnection.getSendEvent().set()
        
        if cmd == "ping":
            pingNonce = Header.getDir()["payload"]
            self.cResponseHandlerData.setNextMsg(self.cBitcoinConnection.pongMsg(bytes(pingNonce)))
            self.cBitcoinConnection.getSendEvent().set()

        if cmd == "version":
            ip = self.cBitcoinConnection.getIP()
            port = self.cBitcoinConnection.getPort()
            chain = self.cBitcoinConnection.getChain()
            self.cBitcoinConnection.getDbConnector().insertJson(chain, ip, port, json_object)

        if cmd == "addr":
            self.cBitcoinConnection.getDbConnector().insertJson(None, None, None, json_object)
            #close connection
            self.cBitcoinConnection.setKeepAlive(False)
            #dont print addr
            return

        if cmd == "feefilter":
            #last message before inv data
            #getaddr not already send
            #second getadr in inv because < 70013 is not sending feefilter msg
            if(self.cResponseHandlerData.getSendCmd().count("getaddr") == 0):
                self.cResponseHandlerData.setNextMsg(self.cBitcoinConnection.getaddrMsg())
                self.cResponseHandlerData.addSendCmd("getaddr")
                self.cBitcoinConnection.getSendEvent().set()

        if cmd == "inv":
            #remove unnwanted inv data
            wantedInv = []
            tmp = json.loads(json_object)
            for x in tmp["payload"]["inventory"]:
                if ((x["type"] == "MSG_TX") or (x["type"] =="MSG_WITNESS_TX")):
                    continue
                wantedInv.append(x)
            
            showInv = {
                "chain": tmp["chain"],
                "command": tmp["command"],
                "length": tmp["length"],
                "payload": wantedInv
            }
            print(json.dumps(showInv, indent= 4))

            #send getaddr if not already send
            #second getadr because < 70013 is not sending feefilter msg
            if(self.cResponseHandlerData.getSendCmd().count("getaddr") == 0):
                self.cResponseHandlerData.setNextMsg(self.cBitcoinConnection.getaddrMsg())
                self.cResponseHandlerData.addSendCmd("getaddr")
                self.cBitcoinConnection.getSendEvent().set()
            return

        #default
        print(json_object)    
