import logging
import threading
import queue
from BitcoinNetworkClient.Network.networkThread import Client

class NetworkQueue(threading.Thread):

    def __init__(self, threadsnr, queuelenght):
        self.exitFlagLock = threading.Lock()
        self.exitFlag = queue.Queue(1)
        self.exitFlag.put(int(1))
        self.threadList = []
        for i in range(threadsnr):
            self.threadList.append("Thread-"+str(i))
        self.queueLock = threading.Lock()
        self.workQueue = queue.Queue(queuelenght)
        self.threads = []

    def start(self):
        threadID = 1

        for tName in self.threadList:
            thread = Client(threadID, self.workQueue, self.queueLock, self.exitFlag, self.exitFlagLock)
            thread.start()
            self.threads.append(thread)
            threadID += 1

    def addToQueue(self, datalist):
        # Fill the queue
        self.queueLock.acquire()
        for data in datalist:
            self.workQueue.put(data, False)
        self.queueLock.release()

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