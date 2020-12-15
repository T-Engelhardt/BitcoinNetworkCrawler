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
        self.name = ("ClientThread " + str(threadID))

        self.cQueue = queue
        self.queueLock = queueLock
        self.exitFlag = exitFlag
        self.exitFlagLock = exitFlagLock
        self.size = 4096
        self.connected = False
        self.sendEvent = threading.Event()

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
                    ClientSent(self.server, self.bitcoinConnection, self.sendEvent).start()
                    ClientRecv(self.server, self.bitcoinConnection).start()
                
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

        logging.debug('Exiting')

    def open_socket(self):
        """ Connect to the server """
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.settimeout(5)
            self.server.connect((self.bitcoinConnection.getIP(),self.bitcoinConnection.getPort(),))
            self.connected = True
            logging.debug("connected")
        except socket.error:
            if self.server:
                self.server.close()
            logging.debug("Could not open socket")

class ClientSent(threading.Thread):

    def __init__(self, socket: socket, bitcoinConnection: bitcoinConnection, event: threading.Event):
        threading.Thread.__init__(self)
        self.name = ("ClientSent")
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
                    logging.debug("send Data")
                    self.server.send(bytes(senddata))
                except Exception as e:
                    logging.debug(e)
                    break
            self.event.clear()



class ClientRecv(threading.Thread):

    def __init__(self, socket: socket, bitcoinConnection: bitcoinConnection):
        threading.Thread.__init__(self)
        self.name = ("ClientRecv")

        self.cBitcoinConnection = bitcoinConnection
        self.server = socket

    def run(self):

        RecvID = 0
        timeoutCounter = 0

        while self.cBitcoinConnection.getKeepAlive():

            data1 = b''
            data2 = b''
            data3 = b''

            self.server.setblocking(0)

            #packet 1
            ready = select.select([self.server], [], [], 10)
            if ready[0]:
                data1 = self.server.recv(4096)
                timeoutCounter = 0
            else:
                timeoutCounter += 1
                logging.debug("timeout " + str(timeoutCounter))
                
            
            #packet 2
            ready = select.select([self.server], [], [], 6)
            if ready[0]:
                data2 = self.server.recv(4096)
                timeoutCounter = 0
            else:
                timeoutCounter += 1
                logging.debug("timeout " + str(timeoutCounter))
            
            #packet 3
            ready = select.select([self.server], [], [], 3)
            if ready[0]:
                data3 = self.server.recv(4096)
                timeoutCounter = 0
            else:
                timeoutCounter += 1
                logging.debug("timeout " + str(timeoutCounter))

            #give packet to Bitcoin Connection
            if(len(data1 + data2 + data3) != 0):
                self.cBitcoinConnection.recvMsg(RecvID, data1 + data2 + data3)
            RecvID += 1

            #final timeout
            if(timeoutCounter >= 6):
                logging.debug("finale timeout")
                break

        logging.debug("connection closed")
        self.server.close()
        self.cBitcoinConnection.killSendThread()