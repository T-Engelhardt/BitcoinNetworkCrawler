from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from BitcoinNetworkClient.Network.networkQueue import NetworkQueue

from BitcoinNetworkClient.db.dbConnector import dbConnector

from time import sleep
import logging
import threading
import queue

class refreshNetworkQueue(threading.Thread):

    def __init__(self, chain: str, queue: NetworkQueue):
        threading.Thread.__init__(self)
        self.name = "Refill Network Queue"

        self.flag = True

        self.networkQueue = queue
        self.chain = chain

        logging.debug("Open DB connection")
        self.db = dbConnector()

    def run(self):

        while self.flag:

            logging.debug("Queue Size: "+str(self.networkQueue.getQueueObject().qsize()))
            self.db.fillQueue(self.chain, self.networkQueue)

            sleep(60)

    def stop(self):
        logging.debug("Close DB connection")
        self.db.close()
        self.flag = False
    
