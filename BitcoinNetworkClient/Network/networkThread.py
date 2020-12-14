from BitcoinNetworkClient.Network.bitcoinConnection import bitcoinConnection
from BitcoinNetworkClient.Network.responseHandler import responseHandler
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
        self.threadID = threadID
        self.q = q
        self.queueLock = queueLock
        self.exitFlag = exitFlag
        self.exitFlagLock = exitFlagLock
        self.size = 4096
        self.connected = False

    def run(self):
        print("Starting " + self.name)

        self.exitFlagLock.acquire()
        flag = self.exitFlag.full()
        self.exitFlagLock.release()

        while flag:
            self.queueLock.acquire()
            if not self.q.empty():
                qdata = self.q.get()
                self.tracker = bitcoinConnection(qdata)
                self.queueLock.release()

                self.open_socket()

                if(self.connected):
                    self.socket_send()
                
                #get exit flag
                self.exitFlagLock.acquire()
                flag = self.exitFlag.full()
                self.exitFlagLock.release()
            else:
                self.queueLock.release()
                #wait for new queue entrys
                sleep(5)

                #get exit flag
                self.exitFlagLock.acquire()
                flag = self.exitFlag.full()
                self.exitFlagLock.release()

        print("Exiting ", self.name)

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
                self.tracker.setRecvID(data + data2, RecvID)
                RecvID += 1

            else:
                print(self.name, "timeout")

        print(self.name, "connection closed")
        self.server.close()

    def open_socket(self):
        """ Connect to the server """
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.settimeout(10)
            self.server.connect((self.tracker.getIP(),self.tracker.getPort(),))
            self.connected = True
            print(self.name, "is connected")
        except socket.error:
            if self.server:
                self.server.close()
            print (self.name, "Could not open socket")