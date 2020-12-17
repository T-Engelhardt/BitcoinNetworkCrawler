from BitcoinNetworkClient.Network.networkThread import Client

import logging
import threading
import queue


class NetworkQueue(threading.Thread):

    def __init__(self, threadsnr, queuelenght):
        self.workQueue = queue.Queue(queuelenght)
        self.exitFlag = queue.Queue(1)
        self.exitFlag.put(int(1))

        self.threadList = []
        for i in range(threadsnr):
            self.threadList.append("Thread-"+str(i))
        self.threads = []

    def start(self):
        threadID = 1

        for tName in self.threadList:
            thread = Client(threadID, self, self.exitFlag)
            thread.start()
            self.threads.append(thread)
            threadID += 1

    def addToQueue(self, datalist):
        # Fill the queue
        countAddedItems = 0
        for data in datalist:
            try:
                self.workQueue.put(data, block=True, timeout=5.0)
                countAddedItems += 1
            except:
                logging.debug("Queue Full but "+ str(countAddedItems) +" Item got added to Queue")
                return
        logging.debug("All "+ str(countAddedItems) +" Items got added to Queue")

    def getItemQueue(self):
        try:
            return self.workQueue.get(block=True, timeout=5.0)
        except Exception as e:
            logging.debug(e)
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

    def getQueueObject(self):
        return self.workQueue