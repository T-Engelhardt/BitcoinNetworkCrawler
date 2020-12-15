import logging
from BitcoinNetworkClient.Network.bitcoinConnection import bitcoinConnection
import random
from BitcoinNetworkClient.BitcoinData.bitcoinParser import BitcoinEndcoder, cutBitcoinMsg
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
from BitcoinNetworkClient.util.data2 import NetworkAddress, Vstr, services
from BitcoinNetworkClient.util.data1 import Bint, Endian, data1util
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import version
import ipaddress
import socket
import threading
import select
from time import time, sleep
import queue

class Client(threading.Thread):

    '''
    https://www.tutorialspoint.com/python/python_multithreading.htm
    https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
    '''

    def __init__(self, threadID: int, queue: queue, queueLock: threading.Lock, exitFlag: queue, exitFlagLock: threading.Lock):
        threading.Thread.__init__(self)
        self.name = ("Client Mother " + str(threadID))
        self.threadID = threadID

        self.cQueue = queue
        self.queueLock = queueLock
        self.exitFlag = exitFlag
        self.exitFlagLock = exitFlagLock
        self.size = 4096
        self.connected = False
        self.sendEvent = threading.Event()
        self.ThreadChilds = []

    def run(self):
        logging.debug("Starting")

        self.exitFlagLock.acquire()
        flag = self.exitFlag.full()
        self.exitFlagLock.release()

        while flag:
            logging.debug('Waiting for lock -> NetworkQueue')
            self.queueLock.acquire()
            if not self.cQueue.empty():
                logging.debug('Acquired lock -> NetworkQueue')
                qdata = self.cQueue.get()
                self.queueLock.release()

                self.bitcoinConnection = bitcoinConnection(qdata, self.sendEvent)

                self.open_socket()

                if(self.connected):
                    self.ThreadChilds.append(ClientSent(self.threadID, self.server, self.bitcoinConnection, self.sendEvent))
                    self.ThreadChilds.append(ClientRecv(self.threadID, self.server, self.bitcoinConnection))
                    for t in self.ThreadChilds:
                        t.start()
                
                #get exit flag
                self.exitFlagLock.acquire()
                flag = self.exitFlag.full()
                self.exitFlagLock.release()
            else:
                self.queueLock.release()
                #wait for new queue entrys
                logging.debug('Waiting for new Tasks')
                sleep(5)

                #get exit flag
                self.exitFlagLock.acquire()
                flag = self.exitFlag.full()
                self.exitFlagLock.release()

        self.waitForChilds()
        logging.debug("Exiting Client Thread")

    def waitForChilds(self):
        # Wait for all threads to complete
        for t in self.ThreadChilds:
            t.join()

    def open_socket(self):
        """ Connect to the server """
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #self.server.settimeout(60.0)
            self.server.connect((self.bitcoinConnection.getIP(),self.bitcoinConnection.getPort(),))
            self.server.setblocking(0)
            self.connected = True
            logging.debug("connected")
        except socket.error:
            if self.server:
                self.server.close()
            logging.debug("Could not open socket")

class ClientSent(threading.Thread):

    def __init__(self, MotherThreadID: int, socket: socket, bitcoinConnection: bitcoinConnection, event: threading.Event):
        threading.Thread.__init__(self)
        self.name = ("Client "+ str(MotherThreadID) +" Sent")
        self.server = socket
        self.event = event
        self.cBitcoinConnection = bitcoinConnection

    def run(self):

        while True:
            logging.debug("waiting")
            self.event.wait()

            senddata = self.cBitcoinConnection.getSendMsg()
            #saftey check -> Can be remove probably in the future
            if(senddata != None):
                try:
                    logging.debug("send Data: " + senddata.getDir()["cmd"])
                    self.server.send(bytes(senddata))
                except Exception as e:
                    logging.debug(e)
            else:
                #type NONE found so close Thread
                break
            self.event.clear()



class ClientRecv(threading.Thread):

    def __init__(self, MotherThreadID: int, socket: socket, bitcoinConnection: bitcoinConnection):
        threading.Thread.__init__(self)
        self.name = ("Client "+ str(MotherThreadID) +" Recv")

        self.cBitcoinConnection = bitcoinConnection
        self.server = socket
        self.timeoutCounter = 0

    def run(self):

        RecvID = 0

        while self.cBitcoinConnection.getKeepAlive():

            #while for connection // loop to recive multiple packets
            #the loop packets tries to catch multiple packets but breaks out if x packets timeout -> add one timeout for whole loop

            data = b''
            loopTimeoutCounter = 0

            for packetNr in range(50):
                logging.debug("Packet "+ str(packetNr))

                ready = select.select([self.server], [], [], 2.0)
                if ready[0]:
                #https://stackoverflow.com/a/45251241
                    if(self.server.fileno() == -1):
                        self.cBitcoinConnection.setKeepAlive(False)
                        break
                    try:
                        data += self.server.recv(4096)
                        loopTimeoutCounter = 0
                    except:
                        self.cBitcoinConnection.setKeepAlive(False)
                        break
                else:
                    loopTimeoutCounter += 1
                    logging.debug("LoopTimeout " + str(loopTimeoutCounter))
                    #final timeout
                if(loopTimeoutCounter > 2):
                    break

            #get one timeout if no data is transmited in one rotation
            if (len(data) == 0):
                self.timeoutCounter += 1
                #partner closed the connection
                #self.server.recv returns nothing but loopTimeout +1 is not triggerd
                if(loopTimeoutCounter == 0):
                    break
            else:
                self.timeoutCounter = 0

            #final timeout
            logging.debug("Timeout "+ str(self.timeoutCounter))
            if(self.timeoutCounter > 3):
                logging.debug("final timeout")
                break

            #give packet to Bitcoin Connection
            if(len(data) != 0):
                self.cBitcoinConnection.recvMsg(RecvID, data)
            RecvID += 1

        logging.debug("connection closed")
        self.server.close()
        self.cBitcoinConnection.killSendThread()