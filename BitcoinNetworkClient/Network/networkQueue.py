from BitcoinNetworkClient.db.dbRefresh import refreshNetworkQueue
from BitcoinNetworkClient.db.dbPool import dbPool
from BitcoinNetworkClient.Network.networkThread import Client

import logging
import threading
import queue


class NetworkQueue(threading.Thread):

    def __init__(self, chain, threadsnr, queuelenght):
        self.workQueue = queue.Queue(queuelenght)
        self.exitFlag = queue.Queue(1)
        self.exitFlag.put(int(1))

        self.threadList = []
        for i in range(threadsnr):
            self.threadList.append("Thread-"+str(i))
        self.threads = []

        self.addLock = threading.Lock()
        self.getLock = threading.Lock()

        #number of clients plus 2 for puffer(dbRefresh)
        self.pool = dbPool(threadsnr+2)

        refreshNetworkQueue(chain, queuelenght, self, self.pool.getPool()).start()

    def start(self):
        threadID = 1

        for tName in self.threadList:
            thread = Client(threadID, self, self.exitFlag, self.getPool())
            thread.start()
            self.threads.append(thread)
            threadID += 1

    def getPool(self):
        return self.pool.getPool()

    def addToQueue(self, datalist) -> int:
        logging.debug("Waiting for lock -> addToQueue")
        self.addLock.acquire()
        logging.debug("Acquired lock -> addToQueue")
        # Fill the queue
        countAddedItems = 0
        for data in datalist:
            try:
                self.workQueue.put(data, block=False)
                countAddedItems += 1
            except:
                logging.debug("Queue Full but "+ str(countAddedItems) +" Item got added to Queue")
                self.addLock.release()
                logging.debug("Released lock -> addToQueue")
                return countAddedItems
        logging.debug("All "+ str(countAddedItems) +" Items got added to Queue")
        self.addLock.release()
        logging.debug("Released lock -> addToQueue")
        return countAddedItems

    def getItemQueue(self):
        logging.debug("Waiting for lock -> getItemQueue")
        self.getLock.acquire()
        logging.debug("Acquired lock -> getItemQueue")
        try:
            item = self.workQueue.get(block=True, timeout=5.0)
            self.getLock.release()
            logging.debug("Released lock -> getItemQueue")
            return item
        except Exception as e:
            logging.warning(e)
        self.getLock.release()
        logging.debug("Released lock -> getItemQueue")
        return None

    def closeEmptyOrNot(self, flag):
        #if flag == True wait for list to be empty else close immediately
        if flag:
            # Wait for queue to empty
            while not self.workQueue.empty():
                pass
        # Notify threads it's time to exit
        self.exitFlag.get()

    def waitForClients(self):
        # Wait for all threads to complete
        for t in self.threads:
            t.join()
        logging.debug("Exiting Network Queue Thread")

    def getQueueObject(self) -> queue.Queue:
        return self.workQueue