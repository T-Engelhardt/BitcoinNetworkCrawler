from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from BitcoinNetworkClient.Network.networkQueue import NetworkQueue
    from mysql.connector import pooling

from BitcoinNetworkClient.db.dbConnector import dbConnector

from time import sleep
import logging
import threading
import queue

class refreshNetworkQueue(threading.Thread):

    def __init__(self, chain: str, queue: NetworkQueue, pool: pooling.MySQLConnectionPool):
        threading.Thread.__init__(self)
        self.name = "Refill Network Queue"

        self.flag = True

        self.networkQueue = queue
        self.chain = chain

        self.pool = pool

        #clear previous enqueued Items
        self.clearQueueTag()

    def run(self):

        while self.flag:

            logging.debug("Queue Size: "+str(self.networkQueue.getQueueObject().qsize()))
            self.db = dbConnector(self.pool)
            self.db.fillQueue(self.chain, self.networkQueue)
            self.db.close()

            sleep(60)

    def stop(self):
        self.flag = False
    
    def clearQueueTag(self):
        self.db = dbConnector(self.pool)
        self.db.clearQueueTag(self.chain)
        self.db.close()
