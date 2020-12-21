from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mysql.connector.pooling import PooledMySQLConnection

import pathlib
import geoip2.database
import logging


class dbGeoIp:

    def __init__(self, chain: str, ip: str ,dbID: int, db: PooledMySQLConnection):
        self.ip = ip
        self.chain = chain
        self.dbID = dbID
        self.mydb = db

    def insertGeoData(self):

        mycursor = self.mydb.cursor()

        #check if geoData is not Null -> if null then length is zero
        sql = "SELECT id, geoDataID FROM "+ self.chain +" WHERE geoDataID is not NULL and id="+ str(self.dbID) +";"

        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        
        if(len(myresult) != 0):
            logging.debug("GEODATA already found for this entry in the Database")
            return
        else:
            #default -> Value cant be NONE
            continent, country, city, asnNr, asnName = "NULL", "NULL", "NULL", "NULL", "NULL"
            #Null Island
            latitude, longitude = 0, 0

            reader = geoip2.database.Reader(str(pathlib.Path(__file__).parent.absolute())+'/GeoLite2-City.mmdb')
            try:
                response = reader.city(self.ip)

                continent = response.continent.names["en"]
                if(continent == None): continent = "NULL"
                
                country = response.country.name
                if(country == None): country = "NULL"
                
                city = response.city.name
                if(city == None): city = "NULL"

                latitude = float("{:.4f}".format((response.location.latitude)))
                if(latitude == None): latitude = "NULL"

                longitude = float("{:.4f}".format((response.location.longitude)))
                if(longitude == None): longitude = "NULL"
            except Exception as e:
                logging.debug(e)

            reader = geoip2.database.Reader(str(pathlib.Path(__file__).parent.absolute())+'/GeoLite2-ASN.mmdb')
            try:
                response = reader.asn(self.ip)

                asnNr = response.autonomous_system_number
                if(asnNr == None): asnNr = "NULL"

                asnName = response.autonomous_system_organization
                if(asnName == None): asnName = "NULL"
            except Exception as e:
                logging.debug(e)

            sql1 = "INSERT INTO "+self.chain+"geodata (continent, country, city ,latitude, longitude, asnNr, asnName) \
                    VALUES (%s, %s, %s, %s, %s, %s, %s);"

            sql2 = "INSERT INTO "+ self.chain +" (id, geoDataID) VALUES (%s, LAST_INSERT_ID()) \
                    ON DUPLICATE KEY UPDATE \
                    id = Values(id), \
                    geoDataID = Values(geoDataID);"

            val1 = (continent, country, city, latitude, longitude, asnNr, asnName)
            val2 = (self.dbID,)

            try:
                mycursor.execute(sql1, val1)
            except Exception as e:
                logging.debug(e)
            try:
                mycursor.execute(sql2, val2)
            except Exception as e:
                logging.debug(e)

            try:
                self.mydb.commit()
            except Exception as e:
                logging.debug(e)
            mycursor.close()
            logging.debug("Inserted Geo Data into "+ str(self.dbID))
            return