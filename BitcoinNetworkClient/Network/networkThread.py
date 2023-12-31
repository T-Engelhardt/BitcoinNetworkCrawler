from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from BitcoinNetworkClient.Network.networkQueue import NetworkQueue
    import queue
    from mysql.connector import pooling
    from BitcoinNetworkClient.util.configParser import config

from BitcoinNetworkClient.Network.bitcoinConnection import bitcoinConnection

from time import sleep
import logging
import socket
import socks
import threading
import logging


class Client(threading.Thread):

    '''
    https://www.tutorialspoint.com/python/python_multithreading.htm
    https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
    '''

    def __init__(self, threadID: int, NetQueue: NetworkQueue , exitFlag: queue, pool: pooling.MySQLConnectionPool, cfg: config):
        threading.Thread.__init__(self)
        self.name = ("Client Mother " + str(threadID))
        self.threadID = threadID

        self.NetQueue = NetQueue
        self.exitFlag = exitFlag
        self.cfg = cfg

        self.connected = False
        self.ThreadChilds = []

        self.pool = pool

    def run(self):
        logging.info("Starting")

        while self.exitFlag.full():

            while True:
                logging.info("Open a new Client")
                
                #reset ThreadChilds all threads should be closed by now
                self.ThreadChilds = []
                
                qdata = self.NetQueue.getItemQueue()
                if(qdata == None):
                    #wait for new queue entrys
                    logging.debug('Waiting for new Tasks')
                    #wait a few seconds for a new task
                    sleep(5)
                    #skip opening a new connection
                    break

                #found new Task
                logging.info('Found new Task '+ str(qdata))                

                #open bitcoinConnection
                sendEvent = threading.Event()
                self.bitcoinConnection =  bitcoinConnection(self.threadID, qdata, sendEvent, self.pool, self.cfg)

                #returns true if succesfull
                connected = self.open_socket()

                if(connected):
                    #append to thread list
                    self.ThreadChilds.append(ClientSent(self.threadID, self.server, self.bitcoinConnection))
                    self.ThreadChilds.append(ClientRecv(self.threadID, self.server, self.bitcoinConnection))
                    #start threads
                    for t in self.ThreadChilds:
                        t.start()
                    #send and recive open so start connection
                    logging.info("init Connection")
                    self.bitcoinConnection.initConnection()
                    #break to wait for childs
                    break
                else:
                    #close DB connection
                    self.bitcoinConnection.killConnection()
                    #break to wait for childs
                    break
            
            logging.debug("Waiting for childs")
            #wait for (Send/Recv) Threads to close
            self.waitForChilds()
            logging.info("Close this Connection")

        self.waitForChilds()
        logging.info("Exiting Client Thread")

    def waitForChilds(self):
        # Wait for all threads to complete
        for t in self.ThreadChilds:
            t.join()

    def open_socket(self) -> bool:
        #opens socket returns true if succesfull
        if(self.bitcoinConnection.getIP().endswith(".onion")):
            #open socket trough socket
            try:
                socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050, True)
                self.server = socks.socksocket()
                self.server.settimeout(4.0)
                self.server.connect((self.bitcoinConnection.getIP(),self.bitcoinConnection.getPort(),))
                logging.info("TOR connected")
                return True
            except Exception as e:
                logging.warning(e)
                if self.server:
                    self.server.close()
                logging.info("Could not open TOR socket")
                return False
        else:
            #clear net socket
            try:
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.settimeout(2.0)
                self.server.connect((self.bitcoinConnection.getIP(),self.bitcoinConnection.getPort(),))
                logging.info("connected")
                return True
            except Exception as e:
                logging.warning(e)
                if self.server:
                    self.server.close()
                logging.info("Could not open socket")
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
            #exit if in senddata None Element
            if(None not in senddata):
                try:
                    bytesmsg = b''
                    for data in senddata:
                        logging.info("send Data: " + data.getDir()["cmd"])
                        bytesmsg += bytes(data)
                    self.server.send(bytesmsg)
                except Exception as e:
                    logging.warning(e)
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
                    #logging.debug(e)
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

        logging.info("connection closed")
        #close socket, send Thread, and DB connection in BitcoinConnection
        self.server.close()
        self.cBitcoinConnection.killConnection()