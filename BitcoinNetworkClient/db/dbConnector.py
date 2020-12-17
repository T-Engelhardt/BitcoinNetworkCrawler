import logging
from BitcoinNetworkClient.Network.networkQueue import NetworkQueue
import json
import mysql.connector

class dbConnector:

    def __init__(self):
        self.mydb = mysql.connector.connect(user='root', password='root', host='127.0.0.1', database='BitcoinNodes', auth_plugin='mysql_native_password')

    def insertIP(self, chain: str, IP: str, port: int):

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

    def insertJson(self, chain: str, IP: str, port: int, Object):
        '''
        json or NONE as Object
        '''
        mycursor = self.mydb.cursor()

        #get id of db entry
        sql = "SELECT id, ip_address, port FROM "+ chain +" WHERE (`ip_address` LIKE '%"+ IP +"%') AND (`port` LIKE '%"+ str(port) +"%')"
                
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
    
        if(len(myresult) == 0):
            raise Exception("Tried to Update IP entry in DB but no entry was found")
        dbID = myresult[0][0]

        if(Object == None):
            #add try to database
            #https://stackoverflow.com/a/3466
            sql = "INSERT INTO "+ chain +" (id, last_try_time, last_try_success) VALUES (%s, NOW(), FALSE) \
                ON DUPLICATE KEY UPDATE \
                last_try_time=VALUES(last_try_time), \
                last_try_success=VALUES(last_try_success);"
            #needs tuple for some reason
            val = (dbID,)
            mycursor.execute(sql, val)
            self.mydb.commit()
            mycursor.close()
        else:
            #add version to database
            data = json.loads(Object)
            if(data["command"] == "version"):

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

    def fillQueue(self, chain: str, queue: NetworkQueue):

        mycursor = self.mydb.cursor()

        #get items that are not last tried in the set interval -> DAY HOUR:MIN:SEC or never tried -> NULL
        sql = "SELECT ip_address, port FROM "+ chain +" WHERE `last_try_time` < (NOW() - INTERVAL '0 1:0:0' DAY_SECOND) OR `last_try_time` IS NULL"

        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        for x in myresult:
            tmp = [[x[0], x[1], chain]]
            print(tmp)
            queue.addToQueue(tmp)
        
        mycursor.close()
        
    def close(self):
        self.mydb.close()
