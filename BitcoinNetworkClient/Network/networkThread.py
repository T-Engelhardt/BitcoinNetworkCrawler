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

class Client(threading.Thread):

    '''
    https://www.tutorialspoint.com/python/python_multithreading.htm
    https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
    '''

    def __init__(self, threadID, q, queueLock, exitFlag, exitFlagLock):
        threading.Thread.__init__(self)
        self.name = ("ClientThread " + str(threadID))
        self.q = q
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
            if not self.q.empty():
                logging.debug('Acquired lock -> NetworkQueue')
                qdata = self.q.get()
                self.queueLock.release()
                self.tracker = bitcoinConnection(qdata, self.sendEvent)

                self.open_socket()

                if(self.connected):
                    #start send recive threads and add threads
                    #TODO
                    ClientSent(self.server, self.tracker, self.sendEvent).start()
                    ClientRecv(self.server, self.tracker).start()
                
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

    '''
    def socket_send(self):

        SendID = 0
        RecvID = 0

        while self.tracker.keepOpen():

            senddata = self.tracker.getSendID(SendID)
            #saftey check -> Can be remove probably in the future
            if(senddata != None):
                self.server.send(bytes(senddata))
                SendID += 1

            self.server.setblocking(0)
            ready = select.select([self.server], [], [], 3)
            if ready[0]:
                data2 = b''
                data = self.server.recv(self.size)

                #only recived header
                if len(data) == 24:
                    ready2 = select.select([self.server], [], [], 3)
                    if ready2[0]:
                        data2 = self.server.recv(self.size)

                #TODO
                self.tracker.recvMsg(RecvID, data + data2)
                RecvID += 1

            else:
                print(self.name, "timeout")

        print(self.name, "connection closed")
        self.server.close()
    '''

    def open_socket(self):
        """ Connect to the server """
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.settimeout(5)
            self.server.connect((self.tracker.getIP(),self.tracker.getPort(),))
            self.connected = True
            logging.debug("connected")
        except socket.error:
            if self.server:
                self.server.close()
            logging.debug("Could not open socket")

class ClientSent(threading.Thread):

    def __init__(self, socket, tracker, event):
        threading.Thread.__init__(self)
        self.name = ("ClientSent")
        self.server = socket
        self.event = event
        self.tracker = tracker

    def run(self):

        while True:
            logging.debug("waiting")
            self.event.wait()
            logging.debug("send Data")

            senddata = self.tracker.getSendMsg()
            #saftey check -> Can be remove probably in the future
            if(senddata != None):
                self.server.send(bytes(senddata))
            self.event.clear()



class ClientRecv(threading.Thread):

    def __init__(self, socket, tracker):
        threading.Thread.__init__(self)
        self.name = ("ClientRecv")

        self.tracker = tracker
        self.server = socket

    def run(self):

        RecvID = 0
        timeoutCounter = 0

        while self.tracker.keepOpen():

            self.server.setblocking(0)
            ready = select.select([self.server], [], [], 10)
            if ready[0]:
                data2 = b''
                data = self.server.recv(4096)
                timeoutCounter = 0

                #only recived header
                if len(data) == 24:
                    ready2 = select.select([self.server], [], [], 10)
                    if ready2[0]:
                        data2 = self.server.recv(4096)
                        timeoutCounter = 0
                    else:
                        logging.debug("timeout")
                        timeoutCounter += 1

                #TODO
                self.tracker.recvMsg(RecvID, data + data2)
                RecvID += 1

            else:
                logging.debug("timeout")
                timeoutCounter += 1
                if(timeoutCounter >= 6):
                    break

        logging.debug("connection closed")
        self.server.close()