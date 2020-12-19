from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from BitcoinNetworkClient.Network.networkQueue import NetworkQueue
    import queue
    from mysql.connector import pooling

from BitcoinNetworkClient.Network.bitcoinConnection import bitcoinConnection

from time import sleep
import logging
import socket
import threading
import logging


class Client(threading.Thread):

    '''
    https://www.tutorialspoint.com/python/python_multithreading.htm
    https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
    '''

    def __init__(self, threadID: int, NetQueue: NetworkQueue , exitFlag: queue, pool: pooling.MySQLConnectionPool):
        threading.Thread.__init__(self)
        self.name = ("Client Mother " + str(threadID))
        self.threadID = threadID

        self.NetQueue = NetQueue
        self.exitFlag = exitFlag

        self.connected = False
        self.ThreadChilds = []

        self.pool = pool

    def run(self):
        logging.debug("Starting")

        thisConnection = True

        while self.exitFlag.full():

            while thisConnection:
                logging.debug("Open a new Client")

                #wait for old connection/(Send/Recv) Threads to close
                self.waitForChilds()
                
                qdata = self.NetQueue.getItemQueue()
                if(qdata == None):
                    #wait for new queue entrys
                    logging.debug('Waiting for new Tasks')
                    #wait a few seconds for a new task
                    sleep(5)
                    #close thisConnection
                    break

                #found new Task
                logging.debug('Found new Task ' + str(qdata[0]) + " " + str(qdata[1]) + " " + str(qdata[2]))                

                #open bitcoinConnection
                sendEvent = threading.Event()
                self.bitcoinConnection =  bitcoinConnection(qdata, sendEvent, self.pool)

                #returns true if succesfull
                connected = self.open_socket()

                if(connected):
                    #reset ThreadChilds all threads should be closed by now
                    self.ThreadChilds = []
                    #append to thread list
                    self.ThreadChilds.append(ClientSent(self.threadID, self.server, self.bitcoinConnection))
                    self.ThreadChilds.append(ClientRecv(self.threadID, self.server, self.bitcoinConnection))
                    #start threads
                    for t in self.ThreadChilds:
                        t.start()
                    #send and recive open so start connection
                    logging.debug("init Connection")
                    self.bitcoinConnection.initConnection()
                else:
                    #close DB connection
                    self.bitcoinConnection.closeDBConnection()
                    break
            
            logging.debug("Close this Connection")

        self.waitForChilds()
        logging.debug("Exiting Client Thread")

    def waitForChilds(self):
        # Wait for all threads to complete
        for t in self.ThreadChilds:
            t.join()

    def open_socket(self) -> bool:
        #opens socket returns true if succesfull
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.settimeout(3.0)
            self.server.connect((self.bitcoinConnection.getIP(),self.bitcoinConnection.getPort(),))
            logging.debug("connected")
            return True
        except socket.error:
            if self.server:
                self.server.close()
            logging.debug("Could not open socket")
            return False

class ClientSent(threading.Thread):

    def __init__(self, MotherThreadID: int, socket: socket, bitcoinConnection: bitcoinConnection):
        threading.Thread.__init__(self)
        self.name = ("Client "+ str(MotherThreadID) +" Sent")
        self.server = socket
        self.cBitcoinConnection = bitcoinConnection
        self.event = self.cBitcoinConnection.getSendEvent()

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
                    break
            else:
                #type NONE found so close Thread
                break
            self.event.clear()
        
        logging.debug("closing")



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

                #https://stackoverflow.com/a/45251241
                if(self.server.fileno() == -1):
                    self.cBitcoinConnection.setKeepAlive(False)
                    break
                try:
                    data += self.server.recv(4096)
                    loopTimeoutCounter = 0
                except Exception as e:
                    logging.debug(e)
                    loopTimeoutCounter += 1
                    logging.debug("LoopTimeout " + str(loopTimeoutCounter))
                
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
        #close socket, send Thread, and DB connection in BitcoinConnection
        self.server.close()
        self.cBitcoinConnection.killSendThread()
        self.cBitcoinConnection.closeDBConnection()