from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from BitcoinNetworkClient.Network.networkQueue import NetworkQueue
    from mysql.connector import pooling

from BitcoinNetworkClient.db.dbConnection import dbConnection

from time import sleep
import logging
import threading

class refreshNetworkQueue(threading.Thread):

    def __init__(self, chain: str, queuelenght: int, queue: NetworkQueue, pool: pooling.MySQLConnectionPool):
        threading.Thread.__init__(self)
        self.name = "Refill Network Queue"

        self.exitFlag = False

        self.networkQueue = queue
        self.chain = chain
        self.queuelenght = queuelenght

        self.pool = pool

        #clear previous enqueued Items
        self.clearQueueTag()

    def run(self):

        #breakout if self.flag is false // dont use while with sleep 60 -> incase of SIGINT it does take to long to exit -> check every 10 sec
        while not self.exitFlag:
            for x in range(6):
                if self.exitFlag:
                    break
                if(x == 0):
                    logging.info("Queue Size: "+str(self.networkQueue.getQueueObject().qsize()))
                    self.db = dbConnection(self.pool)
                    self.db.fillQueue(self.chain, self.networkQueue, self.queuelenght)
                    self.db.closeDBConnection()
                sleep(10)
        
        #if exiting correctly unmark all Entries in the DB
        self.clearQueueTag()

    def stop(self):
        self.exitFlag = True
    
    def clearQueueTag(self):
        self.db = dbConnection(self.pool)
        self.db.clearQueueTag(self.chain)
        self.db.closeDBConnection()
