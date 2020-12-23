from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from BitcoinNetworkClient.Network.networkQueue import NetworkQueue
    from mysql.connector import pooling

from BitcoinNetworkClient.db.geoip.dbGeoIp import dbGeoIp
from BitcoinNetworkClient.util.data1 import data1util
from time import sleep
import ipaddress
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

    def insertIP(self, data):
        #chain, ip, port -> Array/data

        mycursor = self.mydb.cursor()

        for info in data:

            chain = info[0]
            IP = info[1]
            port = info[2]

            #check for onion address
            if(str(IP).startswith("fd87:d87e:eb43")):
                try:
                    IP = data1util.Ipv6ToOnion(ipaddress.IPv6Address(IP))
                except Exception as e:
                    logging.debug(e)

            #replaced with unique key constraint
            '''
            sql = "SELECT ip_address, port FROM "+ chain +" WHERE (`ip_address` LIKE '%"+ IP +"%')"
            mycursor.execute(sql)
            myresult = mycursor.fetchall()
            '''

            #insert into DB but on duplicate do nothing
            sql = "INSERT INTO "+ chain +" (ip_address, port) VALUES(%s, %s) ON DUPLICATE KEY UPDATE id=id"
            val = (IP, port)
            try:
                mycursor.execute(sql, val)
            except Exception as e:
                logging.debug(e)
            
        #commit transaktion
        try:
            self.mydb.commit()
            logging.debug("inserted new IPs in DB")
        except Exception as e:
            logging.debug(e)

        #close cursor
        mycursor.close()

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
            #add try to database and remove entry from queue tag also set Prio to min
            sql = "SELECT MIN(queue_prio) FROM "+ chain
            mycursor.execute(sql)
            myresult = mycursor.fetchall()
            minCount = myresult[0][0]

            #https://stackoverflow.com/a/3466
            sql = "INSERT INTO "+ chain +" (id, last_try_time, added_to_queue, try_count, queue_prio) VALUES (%s, NOW(), FALSE, 0, %s+1) \
                ON DUPLICATE KEY UPDATE \
                last_try_time=VALUES(last_try_time), \
                added_to_queue=VALUES(added_to_queue), \
                try_count = try_count + 1, \
                queue_prio=VALUES(queue_prio);"
            #needs tuple for some reason
            val = (dbID, minCount)
            mycursor.execute(sql, val)
            self.mydb.commit()

        else:
            logging.debug("add Json to DB")

            data = json.loads(Object)

            if(data["command"] == "version"):

                '''
                #count +1 in success counts
                sql = "UPDATE "+ chain +" SET try_success_count = try_success_count + 1 WHERE id = "+ str(dbID)
                mycursor.execute(sql)
                self.mydb.commit()
                '''

                logging.debug("version json")

                protocolVersion = data["payload"]["version"]
                payloadServices = data["payload"]["services"]
                payloadServicesHex = payloadServices["hex"]
                payloadUserAgent = data["payload"]["user_agent"]
                payloadStartHeight = data["payload"]["start_height"]

                #https://stackoverflow.com/a/3466
                #dont insert last_try_time because at the start of BitcoinConnection already set last_try_time
                #increment try_success_count by one -> in Values dummy 0 because try_success_count gets incremented but VALUES need to have the same number of columns
                sql = "INSERT INTO "+ chain +" (id, protocolVersion, servicesHex, user_agent, start_height, last_try_success_time, try_success_count) VALUES (%s, %s, %s, %s, %s, NOW(), 0) \
                    ON DUPLICATE KEY UPDATE \
                    protocolVersion=VALUES(protocolVersion), \
                    servicesHex=VALUES(servicesHex), \
                    user_agent=VALUES(user_agent), \
                    start_height=VALUES(start_height), \
                    last_try_success_time=VALUES(last_try_success_time), \
                    try_success_count = try_success_count + 1;"
                val = (dbID, protocolVersion, payloadServicesHex, payloadUserAgent, payloadStartHeight)
                mycursor.execute(sql, val)
                self.mydb.commit()

                #insert geo DATA -> skip geodata for .onion
                if(str(IP).endswith(".onion")):
                    pass
                else:
                    dbGeoIp(chain, IP, dbID, self.mydb).insertGeoData()

            elif(data["command"] == "addr"):
                #we dont need the cursor
                mycursor.close()
                logging.debug("addr json")
                iChain = data["chain"]
                insertArray = []
                for payload in data["payload"]["addr_list"]:
                    #success = self.insertIP(iChain, payload["IPv6/4"], payload["port"])
                    insertArray.append([iChain, payload["IPv6/4"], payload["port"]])
                self.insertIP(insertArray)

        #close all unclosed cursors
        try:
            mycursor.close()
        except Exception as e:
            logging.debug(e)

    def fillQueue(self, chain: str, queue: NetworkQueue):

        mycursor = self.mydb.cursor()

        '''
        #get items that are not last tried in the set interval -> DAY HOUR:MIN:SEC or never tried -> NULL
        sql = "SELECT id, ip_address, port FROM "+ chain +" WHERE `last_try_time` < (NOW() - INTERVAL '1 0:0:0' DAY_SECOND) OR `last_try_time` IS NULL AND `added_to_queue` is FALSE"
        '''
        #LIMITS TO 100 // prio NULL value if not null sort by last_try_time ASC else sort ASC by id
        sql = "SELECT id, ip_address, port \
                FROM "+ chain +" \
                WHERE try_count = ( SELECT MIN(queue_prio) FROM main) AND `added_to_queue` is FALSE ORDER BY last_try_time is NULL DESC , last_try_time ASC , id ASC LIMIT 200"

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

        #close all unclosed cursors
        try:
            mycursor.close()
        except Exception as e:
            logging.debug(e)
        
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
        self.mydb.commit()
        logging.debug("Cleared Queue tag in DB")
        mycursor.close()

    '''
    def deleteChain(self, chain: str):

        mycursor = self.mydb.cursor()
        sql = "DELETE FROM "+ chain +";"
        mycursor.execute(sql)
        sql = "ALTER TABLE "+ chain +" AUTO_INCREMENT = 1"
        mycursor.execute(sql)
        self.mydb.commit()
        mycursor.close()
    '''