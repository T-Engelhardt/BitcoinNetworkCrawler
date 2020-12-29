from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mysql.connector.pooling import MySQLConnectionPool
    from BitcoinNetworkClient.Network.bitcoinNetworkInfo import bitcoinNetInfo
    from BitcoinNetworkClient.util.configParser import config

from BitcoinNetworkClient.db.dbConnection import dbConnection
from BitcoinNetworkClient.db.geoip.dbGeoIp import dbGeoIp

import logging
import json


class dbBitcoinCon(dbConnection):

    def __init__(self, pool: MySQLConnectionPool, netInfo: bitcoinNetInfo, cfg: config):
        super().__init__(pool, cfg)

        self.connectionSuccess = False

        self.netInfo = netInfo

        self.dbID = self.getDBid()

    def getDBid(self) -> int:
        logging.debug("dbBitcoinCon trying to get DB id")

        mycursor = self.getCursor()

        #get id of db entry
        sql = "SELECT id FROM "+ self.netInfo.getChain() +" WHERE ip_address = %s AND port = %s"

        val = (self.netInfo.getIP(), self.netInfo.getPort())

        self.acquireDBlock()      
        self.cursorExecuteWait(mycursor, sql, val, "getDBid")
        myresult = mycursor.fetchall()
        self.releaseDBlock()

        mycursor.close()

        if(len(myresult) == 0):
            raise Exception("Tried to find DB ID but no entry was found")
        elif(len(myresult) == 1):
            logging.debug("DBID "+ str(myresult[0][0]))
            return myresult[0][0]
        else:
            raise Exception("More then one valid ip/port found")

    def insertJson(self, Object: str) -> None:
        #Object is json as string
        logging.info("add Json to DB")

        data = json.loads(Object)

        if(data["command"] == "version"):

            logging.info("version json")
            mycursor = self.getCursor()

            protocolVersion = data["payload"]["version"]
            payloadServices = data["payload"]["services"]
            payloadUserAgent = data["payload"]["user_agent"]
            payloadStartHeight = data["payload"]["start_height"]


            sql = "Update "+ self.netInfo.getChain() +" SET \
                protocolVersion = %s, \
                user_agent = %s, \
                start_height = %s \
                WHERE id = %s"

            val = (protocolVersion, payloadUserAgent, payloadStartHeight, self.dbID)

            self.acquireDBlock()      
            self.cursorExecuteWait(mycursor, sql, val, "insert Json Version")
            self.commitDB("insert Json Version")
            self.releaseDBlock()

            mycursor.close()

            #insert Service Data
            try:
                self.insertServiceInfo(payloadServices)
            except Exception as e:
                logging.warning(e)

            if(self.getConfig().getGeoIPEnable()):
                #insert geo DATA -> skip geodata for .onion
                if(self.netInfo.getIP().endswith(".onion")):
                    pass
                else:
                    try:
                        dbGeoIp(self.netInfo, self.dbID, self, self.getConfig()).insertGeoData()
                    except Exception as e:
                        logging.warning(e)
            else:
                logging.info("Skipping GeoIP")

            #mark connection as succesfull
            self.connectionSuccesfull()

        elif(data["command"] == "addr"):

            if(self.cfg.getDebugSkipInsert()):
                logging.info("Skipping Insert IP")
                return
            logging.info("addr json")

            iChain = data["chain"]
            insertArray = []
            for payload in data["payload"]["addr_list"]:
                insertArray.append([iChain, payload["IPv6/4"], payload["port"]])
            self.insertIP(insertArray, self.getMinPrio(iChain))

        elif(data["command"] == "addrv2"):

            if(self.cfg.getDebugSkipInsert()):
                logging.info("Skipping Insert IP")
                return
            logging.info("addrv2 json")

            iChain = data["chain"]
            insertArray = []
            for payload in data["payload"]["addr_list"]:
                if(payload["networkID"] == "IPV4" or
                    payload["networkID"] == "IPV6" or
                    payload["networkID"] == "TORV2" or
                    payload["networkID"] == "TORV3"):
                    insertArray.append([iChain, payload["addr"], payload["port"]])
                else:
                    logging.warning("Found unimplemented NetworkID" + payload["networkID"])
                    continue
            self.insertIP(insertArray, self.getMinPrio(iChain))

        else:
            logging.info("no valid json found")

    def evaluateTry(self) -> None:
        #update based on if connection successfull or not -> queue mult, prio
        mycursor = self.getCursor()

        if(self.connectionSuccess):
            
            sql = "Update "+ self.netInfo.getChain() +" SET \
                last_try_time = NOW(), \
                last_try_success_time = NOW(), \
                try_count = try_count + 1, \
                try_success_count = try_success_count + 1, \
                queue_mult = 1, \
                queue_prio = queue_prio + queue_mult, \
                added_to_queue = 0\
                WHERE id = %s"

        else:
            
            #multiply queue_mult by two but cap at 16
            sql = "Update "+ self.netInfo.getChain() +" SET \
                last_try_time = NOW(), \
                try_count = try_count + 1, \
                queue_mult = CASE \
                    When queue_mult >= 16 THEN 16 \
                    ELSE queue_mult * 2 END, \
                queue_prio = queue_prio + queue_mult, \
                added_to_queue = 0 \
                WHERE id = %s"

        val = (self.dbID,)

        self.acquireDBlock()      
        self.cursorExecuteWait(mycursor, sql, val, "evaluateTry in DB")
        self.commitDB("evaluateTry in DB")
        self.releaseDBlock()

        mycursor.close()

    def insertServiceInfo(self, serviceData: str):

        mycursor = self.getCursor()

        #check if there is already an entry with given hex
        sql = "SELECT serviceDataID FROM "+ self.netInfo.getChain() +"servicedata WHERE serviceHex = %s"
        val = (serviceData["hex"],)

        self.acquireDBlock()      
        self.cursorExecuteWait(mycursor, sql, val, "Check if Hex in ServiceData DB")
        myresult = mycursor.fetchall()
        self.releaseDBlock()

        if(len(myresult) == 0):
            serviceDataID = None
            logging.debug("No Hex in ServiceData DB found")
        else:
            serviceDataID = myresult[0][0]
            logging.debug("Hex already in ServiceData DB -> " + str(serviceDataID))

        if(serviceDataID == None):

            #insert new hex/names value in ServiceDataDB
            sql = "INSERT INTO "+ self.netInfo.getChain() +"servicedata (serviceHex, serviceName) VALUES(%s, %s)"
            #create str from pyhton list and cut array [] brackets away
            val = (serviceData["hex"], str(serviceData["names"])[1:-1])

            logging.debug("Insert new Service Data into ServiceDataDB")
            self.acquireDBlock()      
            self.cursorExecuteWait(mycursor, sql, val, "Insert into ServiceData DB")
            self.releaseDBlock()

            #change serviceDataID to LAST_INSERT_ID
            sqlNext = "Update "+ self.netInfo.getChain() +" SET \
                serviceDataID = LAST_INSERT_ID() \
                WHERE id = %s"
            valNext = (self.dbID,)

        else:

            #serivceData already in ServiceDataDB so serviceDataID is needed to update ServiceData in chain DB
            sqlNext = "Update "+ self.netInfo.getChain() +" SET \
                serviceDataID = %s \
                WHERE id = %s"
            valNext = (serviceDataID, self.dbID)

        self.acquireDBlock()      
        self.cursorExecuteWait(mycursor, sqlNext, valNext, "Insert ServiceData into chain DB")
        self.commitDB("Insert ServiceData into chain DB")
        self.releaseDBlock()

        mycursor.close()

    def connectionSuccesfull(self) -> None:
        self.connectionSuccess = True