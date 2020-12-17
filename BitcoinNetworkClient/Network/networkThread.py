from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from BitcoinNetworkClient.Network.networkQueue import NetworkQueue
    import queue

from BitcoinNetworkClient.Network.bitcoinConnection import bitcoinConnection

from time import sleep
import logging
import socket
import threading
import select
import logging


class Client(threading.Thread):

    '''
    https://www.tutorialspoint.com/python/python_multithreading.htm
    https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
    '''

    def __init__(self, threadID: int, NetQueue: NetworkQueue , exitFlag: queue):
        threading.Thread.__init__(self)
        self.name = ("Client Mother " + str(threadID))
        self.threadID = threadID

        self.NetQueue = NetQueue
        self.exitFlag = exitFlag

        self.connected = False
        self.sendEvent = threading.Event()
        self.ThreadChilds = []

    def run(self):
        logging.debug("Starting")

        flag = self.exitFlag.full()

        while flag:
            if not self.NetQueue.getQueueObject().empty():
                
                logging.debug('Found new Task')
                qdata = self.NetQueue.getItemQueue()
                if(qdata == None):
                    #queue got empty between now and the if statement
                    break

                self.bitcoinConnection =  bitcoinConnection(qdata, self.sendEvent)

                self.open_socket()

                if(self.connected):
                    self.ThreadChilds.append(ClientSent(self.threadID, self.server, self.bitcoinConnection, self.sendEvent))
                    self.ThreadChilds.append(ClientRecv(self.threadID, self.server, self.bitcoinConnection))
                    for t in self.ThreadChilds:
                        t.start()
                
                #check exit flag
                flag = self.exitFlag.full()
            else:
                #wait for new queue entrys
                logging.debug('Waiting for new Tasks')
                #wait a few seconds for a new task
                sleep(5)

                #check exit flag
                flag = self.exitFlag.full()

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