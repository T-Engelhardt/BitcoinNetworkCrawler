from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from BitcoinNetworkClient.Network.responseHandlerData import responseHandlerData

from BitcoinNetworkClient.BitcoinData.bitcoinParser import BitcoinEndcoder, cutBitcoinMsg
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader

import json
import threading
import logging


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
            self.cResponseHandlerData.setNextMsg(self.cResponseHandlerData.getBitcoinConnection().verackMsg())
            self.cResponseHandlerData.getSendEvent().set()
        
        if cmd == "ping":
            pingNonce = Header.getDir()["payload"]
            self.cResponseHandlerData.setNextMsg(self.cResponseHandlerData.getBitcoinConnection().pongMsg(bytes(pingNonce)))
            self.cResponseHandlerData.getSendEvent().set()

        if cmd == "feefilter":
            #last message before inv data
            self.cResponseHandlerData.setNextMsg(self.cResponseHandlerData.getBitcoinConnection().getaddrMsg())
            self.cResponseHandlerData.getSendEvent().set()

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

            #no need for more processing
            return

        #default
        print(json_object)    
