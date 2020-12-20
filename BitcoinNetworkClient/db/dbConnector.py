from __future__ import annotations
from time import sleep
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from BitcoinNetworkClient.Network.networkQueue import NetworkQueue
    from mysql.connector import pooling

import logging
import json


class dbConnector:

    def __init__(self, pool: pooling.MySQLConnectionPool):

        self.openDBConnection(pool)

        while not self.mydb.is_connected():
            logging.debug("Got NO DB Connection ... Trying again")
            sleep(1)
            self.openDBConnection(pool)

    def openDBConnection(self, pool: pooling.MySQLConnectionPool):
        try:
            self.mydb = pool.get_connection()
            logging.debug("Got DB Connection")
        except Exception as e:
            logging.debug(e)

    def insertIP(self, chain: str, IP: str, port: int):
        #returns true if succesfully inserted or false when not

        mycursor = self.mydb.cursor()

        sql = "SELECT ip_address, port FROM "+ chain +" WHERE (`ip_address` LIKE '%"+ IP +"%')"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()

        if(len(myresult) == 0):
            sql = "INSERT INTO "+ chain +" (ip_address, port) VALUES (%s, %s)"
            val = (IP, port)
            mycursor.execute(sql, val)
            self.mydb.commit()
            mycursor.close()
            return True
        
        else:
            #check if port is also the same
            foundPorts = []
            for x in myresult:
                #get port
                foundPorts.append(x[1])
            if port not in foundPorts:
                #port not found with same ip address
                sql = "INSERT INTO "+ chain +" (ip_address, port) VALUES (%s, %s)"
                val = (IP, port)
                mycursor.execute(sql, val)
                self.mydb.commit()
                mycursor.close()
                return True
        return False

    def insertJson(self, chain: str, IP: str, port: int, Object):
        '''
        json or NONE as Object
        '''
        mycursor = self.mydb.cursor()

        if(chain != None and IP != None and port != None):
            #get id of db entry
            sql = "SELECT id, ip_address, port FROM "+ chain +" WHERE (`ip_address` LIKE '%"+ IP +"%') AND (`port` LIKE '%"+ str(port) +"%')"
                    
            mycursor.execute(sql)
            myresult = mycursor.fetchall()
        
            if(len(myresult) == 0):
                raise Exception("Tried to Update IP entry in DB but no entry was found")
            dbID = myresult[0][0]

        if(Object == None):
            #add try to database and remove entry from queue tag
            #https://stackoverflow.com/a/3466
            sql = "INSERT INTO "+ chain +" (id, last_try_time, last_try_success, added_to_queue) VALUES (%s, NOW(), FALSE, FALSE) \
                ON DUPLICATE KEY UPDATE \
                last_try_time=VALUES(last_try_time), \
                added_to_queue=VALUES(added_to_queue), \
                last_try_success=VALUES(last_try_success);"
            #needs tuple for some reason
            val = (dbID,)
            mycursor.execute(sql, val)
            self.mydb.commit()
            mycursor.close()
        else:
            logging.debug("add Json to DB")

            data = json.loads(Object)

            if(data["command"] == "version"):

                #count +1 in success counts
                sql = "UPDATE "+ chain +" SET try_success_count = try_success_count + 1 WHERE id = "+ str(dbID)
                mycursor.execute(sql)
                self.mydb.commit()

                logging.debug("version json")

                protocolVersion = data["payload"]["version"]
                payloadServices = data["payload"]["services"]
                payloadServicesHex = payloadServices["hex"]
                payloadUserAgent = data["payload"]["user_agent"]
                payloadStartHeight = data["payload"]["start_height"]

                #https://stackoverflow.com/a/3466
                sql = "INSERT INTO "+ chain +" (id, protocolVersion, servicesHex, user_agent, start_height, last_try_time, last_try_success) VALUES (%s, %s, %s, %s, %s, NOW(), TRUE) \
                    ON DUPLICATE KEY UPDATE \
                    protocolVersion=VALUES(protocolVersion), \
                    servicesHex=VALUES(servicesHex), \
                    user_agent=VALUES(user_agent), \
                    start_height=VALUES(start_height), \
                    last_try_time=VALUES(last_try_time), \
                    last_try_success=VALUES(last_try_success);"
                val = (dbID, protocolVersion, payloadServicesHex, payloadUserAgent, payloadStartHeight)
                mycursor.execute(sql, val)
                self.mydb.commit()
                mycursor.close()

            elif(data["command"] == "addr"):
                logging.debug("addr json")
                iChain = data["chain"]
                countInsert = 0
                for payload in data["payload"]["addr_list"]:
                    success = self.insertIP(iChain, payload["IPv6/4"], payload["port"])
                    if(success): countInsert += 1
                logging.debug("inserted "+ str(countInsert) +" new IPs in DB")

    def fillQueue(self, chain: str, queue: NetworkQueue):

        mycursor = self.mydb.cursor()

        #get items that are not last tried in the set interval -> DAY HOUR:MIN:SEC or never tried -> NULL
        sql = "SELECT id, ip_address, port FROM "+ chain +" WHERE `last_try_time` < (NOW() - INTERVAL '2 0:0:0' DAY_SECOND) OR `last_try_time` IS NULL AND `added_to_queue` is FALSE"

        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        forQueue = []
        ItemIDs = []
        for x in myresult:
            tmp = [x[1], x[2], chain]
            #list all ids of items
            ItemIDs.append(x[0])
            forQueue.append(tmp)
        if(len(forQueue) == 0):
            logging.debug("No new items to add to Queue")
        else:   
            #mark added item to queue with added_to_queue in DB
            #addToQueue returns number of added items
            ItemAddedCount = queue.addToQueue(forQueue)
            #only get items that where added to Queue
            markedIDs = ItemIDs[:ItemAddedCount]
            #create string with id from array -> remove [] and remove space between ids
            prepareIDs = str(markedIDs)[1:-1].replace(', ',',')
            logging.debug("markedIDs: "+ prepareIDs)
            sql = "UPDATE "+ chain +" SET `added_to_queue`=1 WHERE FIND_IN_SET(`id`, '"+ prepareIDs +"')"
            mycursor.execute(sql)
            self.mydb.commit()

        mycursor.close()
        
    def close(self):
        try:
            self.mydb.close()
            logging.debug("Return DB Connection")
        except Exception as e:
            logging.debug(e)
        
    def clearQueueTag(self, chain: str):

        mycursor = self.mydb.cursor()
        sql = "UPDATE "+ chain +" SET added_to_queue = 0;"
        mycursor.execute(sql)
        logging.debug("Cleared Queue tag in DB")
        mycursor.close()

    def deleteChain(self, chain: str):

        mycursor = self.mydb.cursor()
        sql = "DELETE FROM "+ chain +";"
        mycursor.execute(sql)
        sql = "ALTER TABLE "+ chain +" AUTO_INCREMENT = 1"
        mycursor.execute(sql)
        mycursor.close()
