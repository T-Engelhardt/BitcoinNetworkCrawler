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
        self.name = ("Client "+ str(responseHandlerData.getMotherTreadID()) +" | responseHandlerThread " + str(threadID))
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
                logging.warning(e)
        #afer all Response got their handling send back response
        self.cBitcoinConnection.getSendEvent().set()

    def handleResponse(self, Header: BitcoinHeader):

        cmd = Header.getDir()["cmd"]
        logging.info("Recived -> " + cmd)
        json_object = json.dumps(Header, indent = 4, cls=BitcoinEndcoder)

        if cmd == "sendaddrv2":
            self.cBitcoinConnection.enableAddrV2()
        
        if cmd == "verack":
            #send sendaddrv2 msg before verack
            if(self.cBitcoinConnection.getAddrV2Flag()):
                self.cResponseHandlerData.setNextMsg(self.cBitcoinConnection.sendAddrV2())
            #send verack
            self.cResponseHandlerData.setNextMsg(self.cBitcoinConnection.verackMsg())
        
        if cmd == "ping":
            pingNonce = Header.getDir()["payload"]
            self.cResponseHandlerData.setNextMsg(self.cBitcoinConnection.pongMsg(bytes(pingNonce)))

        if cmd == "version":
            self.cBitcoinConnection.getDbBitcoinCon().insertJson(json_object)

        if cmd == "addr":
            self.cBitcoinConnection.getDbBitcoinCon().insertJson(json_object)
            #close connection but only if we recived more then one addr
            if(json.loads(json_object)["payload"]["count"] != 1):
                self.cBitcoinConnection.signalKillConnection()
            #dont print addr
            return

        if cmd == "addrv2":
            self.cBitcoinConnection.getDbBitcoinCon().insertJson(json_object)

        if cmd == "feefilter":
            #last message before inv data
            #getaddr not already send
            #second getadr in inv because < 70013 is not sending feefilter msg
            if(self.cResponseHandlerData.getSendCmd().count("getaddr") == 0):
                self.cResponseHandlerData.setNextMsg(self.cBitcoinConnection.getaddrMsg())
                self.cResponseHandlerData.addSendCmd("getaddr")

        if cmd == "inv":
            #Debug print inv Data
            '''
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
            #print(json.dumps(showInv, indent= 4))
            '''

            #send getaddr if not already send
            #second getadr because < 70013 is not sending feefilter msg
            if(self.cResponseHandlerData.getSendCmd().count("getaddr") == 0):
                self.cResponseHandlerData.setNextMsg(self.cBitcoinConnection.getaddrMsg())
                self.cResponseHandlerData.addSendCmd("getaddr")
            return

        #Debug print every Json msg
        #default
        #print(json_object)    
