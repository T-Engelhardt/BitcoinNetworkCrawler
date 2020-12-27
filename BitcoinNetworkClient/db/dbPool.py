from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from BitcoinNetworkClient.util.configParser import config

from mysql.connector.pooling import MySQLConnectionPool

import logging

class dbPool:

    def __init__(self, cfg: config):

        size = cfg.getBasicClientNr() + int(cfg.getBasicClientNr() / 2)
        if(size < 4):
            size = 4

        #create DB pool
        try:
            self.connection_pool = MySQLConnectionPool(pool_name="BitcoinNodes_pool",
                                                        pool_size=size,
                                                        pool_reset_session=True,
                                                        host=cfg.getSqlHost(),
                                                        database=cfg.getSqlDB(),
                                                        user=cfg.getSqlUser(),
                                                        password=cfg.getSqlPwd(),
                                                        auth_plugin='mysql_native_password')

        except Exception as e:
            logging.error(e)

    def getPool(self) -> MySQLConnectionPool:
        return self.connection_pool
