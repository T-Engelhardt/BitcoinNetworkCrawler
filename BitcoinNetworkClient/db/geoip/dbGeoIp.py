from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from BitcoinNetworkClient.db.dbBitcoinCon import dbBitcoinCon
    from BitcoinNetworkClient.Network.bitcoinNetworkInfo import bitcoinNetInfo
    from BitcoinNetworkClient.util.configParser import config

import geoip2.database
import logging


class dbGeoIp:

    def __init__(self, netInfo: bitcoinNetInfo, dbID: int, db: dbBitcoinCon, cfg: config):

        self.dbID = dbID
        self.netInfo = netInfo
        self.mydb = db
        self.cfg = cfg

    def insertGeoData(self):

        mycursor = self.mydb.getCursor()

        #check if there is already a GeoData entry
        sql = "SELECT geoDataID FROM "+ self.netInfo.getChain() +" WHERE id="+ str(self.dbID) +";"

        self.mydb.acquireDBlock()      
        self.mydb.cursorExecuteWait(mycursor, sql, None, "Geoip check if Null")
        myresult = mycursor.fetchall()
        self.mydb.releaseDBlock()
        
        geoDBid = myresult[0][0]

        #default None
        continent, country, city, asnNr, asnName = None, None, None, None, None
        #Null Island
        latitude, longitude = 0, 0

        reader = geoip2.database.Reader(self.cfg.getGeoIPDir()+'GeoLite2-City.mmdb')
        try:
            response = reader.city(self.netInfo.getIP())
            continent = response.continent.names["en"]
            country = response.country.name
            city = response.city.name
            latitude = float("{:.4f}".format((response.location.latitude)))
            longitude = float("{:.4f}".format((response.location.longitude)))
        except Exception as e:
            logging.warning(e)

        reader = geoip2.database.Reader(self.cfg.getGeoIPDir()+'GeoLite2-ASN.mmdb')
        try:
            response = reader.asn(self.netInfo.getIP())
            asnNr = response.autonomous_system_number
            asnName = response.autonomous_system_organization
        except Exception as e:
            logging.warning(e)


        if(geoDBid == None):
            logging.debug("NO GEODATA entry found in Database")

            sql1 = "INSERT INTO "+ self.netInfo.getChain() +"geodata (continent, country, city ,latitude, longitude, asnNr, asnName) \
                    VALUES (%s, %s, %s, %s, %s, %s, %s);"

            sql2 = "UPDATE "+ self.netInfo.getChain() +" SET \
                    geoDataID = LAST_INSERT_ID() \
                    WHERE id = "+ str(self.dbID)

            val1 = (continent, country, city, latitude, longitude, asnNr, asnName)

            self.mydb.acquireDBlock()      
            self.mydb.cursorExecuteWait(mycursor, sql1, val1, "insert Geodata into geodate db")
            self.mydb.cursorExecuteWait(mycursor, sql2, None, "insert GeodataID into chain db")
            self.mydb.commitDB("insert new Geodata")
            self.mydb.releaseDBlock()

        else:
            logging.debug("GEODATA already found for this entry in the Database")
            
            sql = "Update "+ self.netInfo.getChain() +"geodata SET \
                continent = %s, \
                country = %s, \
                city = %s, \
                latitude = %s, \
                longitude = %s, \
                asnNr = %s, \
                asnName = %s \
                WHERE geoDataID = %s"

            val = (continent, country, city, latitude, longitude, asnNr, asnName, geoDBid)

            self.mydb.acquireDBlock()      
            self.mydb.cursorExecuteWait(mycursor, sql, val, "update Geodata in geodate db")
            self.mydb.commitDB("update Geodata")
            self.mydb.releaseDBlock()
            logging.info("Update Geo Data at "+ str(geoDBid))

        mycursor.close()
            
        logging.info("Inserted Geo Data into "+ str(self.dbID))
        return