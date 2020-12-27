from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mysql.connector.pooling import MySQLConnectionPool, PooledMySQLConnection
    from mysql.connector.cursor import MySQLCursor
    from BitcoinNetworkClient.Network.networkQueue import NetworkQueue

from BitcoinNetworkClient.util.data1 import data1util

from mysql.connector import Error
from time import sleep
import ipaddress
import threading
import random
import logging


class dbConnection:

    def __init__(self, pool: MySQLConnectionPool):

        self.dbLock = threading.Lock()

        #self.mydb = type(PooledMySQLConnection)
        self.gotDBConnection = False
        self.openDBConnection(pool)

        while not self.gotDBConnection:
            logging.debug("Got NO DB Connection ... Trying again")
            #random sleep time between 1 and 3 seconds
            sleep(random.uniform(1,3))
            self.openDBConnection(pool)

    def openDBConnection(self, pool: MySQLConnectionPool) -> None:
        try:
            self.mydb = pool.get_connection()
            self.gotDBConnection = True
            logging.debug("Got DB Connection")
        except Exception as e:
            logging.warning(e)

    def closeDBConnection(self) ->None:
        try:
            self.mydb.close()
            logging.debug("Return DB Connection")
        except Exception as e:
            logging.warning(e)

    def insertIP(self, data, minQueuePrio: int) -> None:
        #chain, ip, port -> Array/data

        mycursor = self.getCursor()

        self.acquireDBlock()
        for info in data:

            chain = info[0]
            IP = info[1]
            port = info[2]

            #check for onion address
            if(str(IP).startswith("fd87:d87e:eb43")):
                try:
                    IP = data1util.Ipv6ToOnion(ipaddress.IPv6Address(IP))
                except Exception as e:
                    logging.warning(e)

            #insert into DB but on duplicate do nothing
            sql = "INSERT INTO "+ chain +" (ip_address, port, queue_prio) VALUES(%s, %s, %s) ON DUPLICATE KEY UPDATE id=id"
            val = (IP, port, minQueuePrio)
            
            #try again until DB is available again
            self.cursorExecuteWait(mycursor, sql, val, "Insert IP")

        #commit transaktion
        self.commitDB("Insert IP")
        self.releaseDBlock()

        #close cursor
        mycursor.close()

    def fillQueue(self, chain: str, queue: NetworkQueue, queuelenght: int):

        mycursor = self.getCursor()

        #LIMITS TO queuelength // prio NULL value if not null sort by last_try_time ASC else sort ASC by id
        sql = "SELECT id, ip_address, port \
                FROM "+ chain +" \
                WHERE queue_prio = ( SELECT MIN(queue_prio) FROM "+ chain +") AND `added_to_queue` is FALSE \
                ORDER BY last_try_time is NULL DESC , last_try_time ASC , id ASC LIMIT " + str(queuelenght)

        self.acquireDBlock()      
        self.cursorExecuteWait(mycursor, sql, None, "get marked IDs from DB fillQueue")
        myresult = mycursor.fetchall()
        self.releaseDBlock()

        forQueue = []
        ItemIDs = []

        for x in myresult:
            tmp = [x[1], x[2], chain]
            #list all ids of items
            ItemIDs.append(x[0])
            forQueue.append(tmp)
        if(len(forQueue) == 0):
            logging.info("No new items to add to Queue")
        else:   
            #mark added item to queue with added_to_queue in DB
            #addToQueue returns number of added items
            ItemAddedCount = queue.addToQueue(forQueue, queuelenght)
            logging.info("Added new items to Queue")
            #only get items that where added to Queue
            markedIDs = ItemIDs[:ItemAddedCount]
            #create string with id from array -> remove [] and remove space between ids
            prepareIDs = str(markedIDs)[1:-1].replace(', ',',')
            logging.debug("markedIDs: "+ prepareIDs)

            sql = "UPDATE "+ chain +" SET `added_to_queue`=1 WHERE FIND_IN_SET(`id`, '"+ prepareIDs +"')"

            #fill Queue locked up in testing
            self.acquireDBlock()
            self.cursorExecuteWait(mycursor, sql, None, "fillQueue markIDs")
            self.commitDB("fillQueue markIDs")
            self.releaseDBlock()
            
            logging.debug("Marked IDs from Queue in DB")

        mycursor.close()

    def getMinPrio(self, chain: str) -> int:

        mycursor = self.getCursor()

        sql = "SELECT MIN(queue_prio) FROM "+ chain

        self.acquireDBlock()
        self.cursorExecuteWait(mycursor, sql, None, "getMinPrio")
        myresult = mycursor.fetchall()
        self.releaseDBlock()
        mycursor.close()

        logging.debug("Min Queue Prio is :" + str(myresult[0][0]))

        return myresult[0][0]

    def clearQueueTag(self, chain: str):

        mycursor = self.getCursor()

        sql = "UPDATE "+ chain +" SET added_to_queue = 0"

        self.acquireDBlock()
        self.cursorExecuteWait(mycursor, sql, None, "clearQueueTag")
        self.commitDB("clearQueueTag")
        self.releaseDBlock()

        logging.debug("Cleared Queue tag in DB")
        mycursor.close()

    def cursorExecuteWait(self, ObjectCursor: MySQLCursor, sql: str, val, infoError: str) -> None:
        while True:
            try:
                if(val == None):
                    ObjectCursor.execute(sql)
                else:
                    ObjectCursor.execute(sql, val)
                break
            #My SQL error
            except Error as e:
                logging.error("%s execute -> CODE: %s MSG: %s", infoError, str(e.errno), e.msg)
                #1213 (40001): Deadlock found when trying to get lock; try restarting transaction
                if(e.errno == 1213):
                    logging.info("Retry cursor execute")
                    #random sleep time between 1 and 3 seconds
                    sleep(random.uniform(1,3))
                else:
                    #errno no solution implemented
                    #release DBlock after error
                    self.releaseDBlock()
                    break
                
    
    def commitDB(self, msg: str) -> None:
        try:
            self.mydb.commit()
            logging.info("Commit DB: "+ msg)
        except Error as e:
            logging.error("ERROR Commit DB "+ msg +" CODE: %s MSG: %s", str(e.errno), e.msg)
            #release DBlock after error
            self.releaseDBlock()

    def acquireDBlock(self) -> None:
        logging.debug('Waiting for DB lock')
        if(self.dbLock.acquire(True, 5.0)):
            logging.debug('Acquired DB lock')
        else:
            logging.debug('Acquired DB lock TIMEOUT')

    def releaseDBlock(self) -> None:
        try:
            self.dbLock.release()
        except Exception as e:
            logging.warning(e)
        logging.debug('Released DB lock')

    def getDB(self) -> PooledMySQLConnection:
        return self.mydb

    def getCursor(self) -> MySQLCursor:
        return self.mydb.cursor()