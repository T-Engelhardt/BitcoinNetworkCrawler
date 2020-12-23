#class to fix or convert entrys in db
#NOW -> old ipv6 wrapped onion into .onion address

import ipaddress
from BitcoinNetworkClient.util.data1 import data1util
from BitcoinNetworkClient.db.dbPool import dbPool


class dbConvert:

    def __init__(self):
        self.mydb = dbPool(1).getPool().get_connection()
        self.run()

    def run(self):
        mycursor = self.mydb.cursor()
        
        sql = "SELECT id, ip_address FROM main WHERE (`ip_address` LIKE '%fd87:d87e:eb43:%')"

        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        for x in myresult:
            print(data1util.Ipv6ToOnion(ipaddress.IPv6Address(x[1])), x[0])

            sql = "INSERT INTO main (id, ip_address) VALUES (%s, %s) \
                ON DUPLICATE KEY UPDATE \
                ip_address=VALUES(ip_address);"
            val = (x[0], data1util.Ipv6ToOnion(ipaddress.IPv6Address(x[1])))
            mycursor.execute(sql, val)

        self.mydb.commit()
        mycursor.close()
        self.mydb.close()

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