from mysql.connector.pooling import MySQLConnectionPool

import logging

class dbPool:

    def __init__(self, poolsize: int):

        #create DB pool
        try:
            self.connection_pool = MySQLConnectionPool(pool_name="BitcoinNodes_pool",
                                                        pool_size=poolsize,
                                                        pool_reset_session=True,
                                                        host='127.0.0.1',
                                                        database='BitcoinNodes',
                                                        user='root',
                                                        password='root',
                                                        auth_plugin='mysql_native_password')

        except Exception as e:
            logging.error(e)

    def getPool(self) -> MySQLConnectionPool:
        return self.connection_pool
