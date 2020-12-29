from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

import pathlib
import logging
import yaml

class config:

    def __init__(self, path: str) -> None:

        #cut path /util out
        self.projectPath = str(pathlib.Path(__file__).parent.absolute())[:-4]

        try:
            with open(path, "r") as ymlfile:
                self.cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        except:
            self.cfg = None

    def getBasicClientNr(self) -> int:
        try:
            result = self.cfg["basic"]["client"]
        except:
            #default
            result = 1
        return result

    def getBasicQueueLength(self) -> int:
        try:
            result = self.cfg["basic"]["length"]
        except:
            #default
            result = 10
        return result

    def getBasicChain(self) -> str:
        try:
            result = self.cfg["basic"]["chain"]
        except:
            #default
            result = "regtest"
        return result

    def getLogLevel(self) -> logging:
        try:
            tmp = self.cfg["log"]["level"]
            if(tmp == "DEBUG"):
                result = logging.DEBUG
            elif(tmp == "INFO"):
                result = logging.INFO
            elif(tmp == "WARNING"):
                result = logging.WARNING
            elif(tmp == "ERROR"):
                result = logging.ERROR
            elif(tmp == "CRITICAL"):
                result = logging.CRITICAL
            else:
                result = logging.DEBUG
        except:
            #default
            result = logging.DEBUG
        return result

    def getLogSystemd(self) -> bool:
        try:
            tmp = self.cfg["log"]["systemd"]
            if(tmp == "1"):
                result = True
            else:
                result = False
        except:
            #default
            result = False
        return result

    def getSqlHost(self) -> str:
        try:
            result = self.cfg["mysql"]["host"]
        except:
            #default
            result = "127.0.0.1"
        return result

    def getSqlUser(self) -> str:
        try:
            result = self.cfg["mysql"]["user"]
        except:
            #default
            result = "root"
        return result

    def getSqlPwd(self) -> str:
        try:
            result = self.cfg["mysql"]["passwd"]
        except:
            #default
            result = "root"
        return result

    def getSqlDB(self) -> str:
        try:
            result = self.cfg["mysql"]["db"]
        except:
            #default
            result = "BitcoinNodesTest"
        return result

    def getGeoIPEnable(self) -> bool:
        try:
            tmp = self.cfg["geoip"]["enable"]
            if(tmp == "1"):
                result = True
            else:
                result = False
        except:
            #default
            result = True
        return result

    def getGeoIPDir(self) -> str:
        try:
            result = self.cfg["geoip"]["path"]
            if(str(result).endswith("/")):
                pass
            else:
                result += "/"
        except:
            #default
            result = self.projectPath + "db/geoip/"
        return result

    def getDebugSkipInsert(self) -> bool:
        try:
            tmp = self.cfg["debug"]["skipInsert"]
            if(tmp == "1"):
                result = True
            else:
                result = False
        except:
            #default
            result = False
        return result

    def __str__(self):
        result = ""
        result += "ClientNr: " + str(self.getBasicClientNr()) +"\t\n"
        result += "QueueLength: " + str(self.getBasicQueueLength()) +"\t\n"
        result += "Chain: " + str(self.getBasicChain()) +"\t\n"
        result += "LogLevel: " + str(self.getLogLevel()) +"\t\n"
        result += "LogSystemd: " + str(self.getLogSystemd()) +"\t\n"
        result += "SqlHost: " + str(self.getSqlHost()) +"\t\n"
        result += "SqlDB: " + str(self.getSqlDB()) +"\t\n"
        result += "SqlUser: " + str(self.getSqlUser()) +"\t\n"
        result += "SqlPWD: " + "***" +"\t\n"
        result += "GeoIP Enabled: " + str(self.getGeoIPEnable()) +"\t\n"
        result += "GeoIp Dir: " + str(self.getGeoIPDir()) +"\t\n"
        result += "DebugSkipInsert: " + str(self.getDebugSkipInsert()) +"\t\n"

        return result