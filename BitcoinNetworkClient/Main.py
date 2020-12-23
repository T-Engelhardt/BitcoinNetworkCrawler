from BitcoinNetworkClient.db.dbConvert import dbConvert
from BitcoinNetworkClient.db.dbRefresh import refreshNetworkQueue
import threading
from BitcoinNetworkClient.db.dbConnector import dbConnector
from time import sleep
from BitcoinNetworkClient.Network.networkQueue import NetworkQueue
from BitcoinNetworkClient.Network.networkThread import Client
from threading import Thread
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import addr, inv, ping, verack, version
from BitcoinNetworkClient.util.data1 import Bint, Endian, data1util
from BitcoinNetworkClient.BitcoinData.bitcoinParser import BitcoinEndcoder, cutBitcoinMsg
from BitcoinNetworkClient.util.data2 import InventoryVector, NetworkAddress, Vint, Vstr, services
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
import ipaddress
import json 
import random
import logging


def start():
    
    print("RUN")
    
    logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )

    #ipList = [["127.0.0.1", 18331, "regtest"], ["127.0.0.1", 18332, "regtest"], ["127.0.0.1", 18333, "regtest"], ["127.0.0.1", 18334, "regtest"]]
    #ipList = [["34.80.224.42", 8333, "main"]]
    #ipList2 = [["127.0.0.1", 1112]]
    #MYSQL
    #
    #SELECT user_agent,COUNT(user_agent) FROM main GROUP BY user_agent ORDER BY COUNT(user_agent) desc ;
    #SELECT COUNT(*) FROM main
    #
    q = NetworkQueue("main", 4, 200)
    q.start()

    #print(data1util.OnionToIpv6("j2ehpso7ngkscjrm.onion"))
    #print(data1util.Ipv6ToOnion(ipaddress.IPv6Address("fd87:d87e:eb43:437f:1ea0:8efb:8cab:85a4")))

    #try:
    #    q.addToQueue(ipList)
    #except:
    #    print("queue Full")
    
    #q.closeEmptyOrNot(True)
    #q.waitForClients()
    
    #db = dbConnector()
    #db.insertIP("testnet3", "127.0.0.3", 8312)

    #with open("BitcoinNetworkClient/test/bin/addr1000.bin", "rb") as f:
    #    read = bytes(f.read())

    #json_object = json.dumps(BitcoinHeader(read), indent = 4, cls=BitcoinEndcoder)
    #print(json_object)   
    #db = dbConnector()
    #db.deleteChain("main")
    #db.deleteChain("regtest")
    #db.deleteChain("testnet3")
    #db.insertJson(None, None, None, json_object)
    #db.insertIP("regtest", "127.0.0.1", 18331)
    #db.insertIP("regtest", "127.0.0.1", 18332)
    #db.insertIP("regtest", "127.0.0.1", 18333)
    #db.insertIP("regtest", "127.0.0.1", 18334)
    #db.insertIP("main", "34.80.224.42", 8333)


    # tor prefix in ipv6 mapped onion "fd87:d87e:eb43::""

    #sleep(10)
    #q.closeEmptyOrNot(True)
    #q.waitForClients()
    #refill.stop()
    
    '''
    #db.insertJson("testnet3", "127.0.0.2", 8333, json_object)
    #db.fillQueue("testnet3", q)

    db.close()
    
    #print(q.getItemQueue())
    #print(q.getItemQueue())
    '''
    '''
    test1 = InventoryVector({
        "type": InventoryVector.INV_TYPE.MSG_TX,
        "hash": "154c7d908a5f5d7f572bc184fd076f4ff91a3f364124dfcd822e09ccc8f15591"
    })
    #print(bytes(test1))

    test2 = InventoryVector({
        "type": InventoryVector.INV_TYPE.MSG_WITNESS_BLOCK,
        "hash": "0000000000000249ce1813cbbff7ef80b014e43752acac2fbd98e3e69a6a9fd2"
    })
    #print(bytes(test2))
    testArray = [test1, test2]
    test3 = inv([test1, test2])
    print(bytes(test3))

    test4 = inv(b'\x02\x01\x00\x00\x00\x91U\xf1\xc8\xcc\t.\x82\xcd\xdf$A6?\x1a\xf9Oo\x07\xfd\x84\xc1+W\x7f]_\x8a\x90}L\x15\x02\x00\x00@\xd2\x9fj\x9a\xe6\xe3\x98\xbd/\xac\xacR7\xe4\x14\xb0\x80\xef\xf7\xbf\xcb\x13\x18\xceI\x02\x00\x00\x00\x00\x00\x00')
    json_object = json.dumps(test4, indent = 4, cls=BitcoinEndcoder)   
    print(json_object)
    '''

    '''
    self.versionPayload = version({
            "version": Bint(70015, 32, Endian.LITTLE),
            "services": services([services.SERVICES_FLAG.NODE_NETWORK_LIMITED, services.SERVICES_FLAG.NODE_WITNESS]),
            "timestamp": Bint(int(time()), 64, Endian.LITTLE),
            "addr_recv": (NetworkAddress({
                "time": Bint(0, 32, Endian.BIG),
                "services": services([services.SERVICES_FLAG.NODE_NETWORK, services.SERVICES_FLAG.NODE_WITNESS, services.SERVICES_FLAG.NODE_NETWORK_LIMITED]),
                "IPv6/4": ipaddress.ip_address('::'),
                "port": Bint(0, 16, Endian.BIG)
            })),
            "addr_from": (NetworkAddress({
                "time": Bint(0, 32, Endian.BIG),
                "services": services([services.SERVICES_FLAG.NODE_WITNESS, services.SERVICES_FLAG.NODE_NETWORK_LIMITED]),
                "IPv6/4": ipaddress.ip_address('::'),
                "port": Bint(0, 16, Endian.BIG)
            })),
            "nonce": Bint(random.getrandbits(64), 64, Endian.LITTLE),
            "user_agent": Vstr("/Satoshi:0.20.1/"),
            "start_height": Bint(182915, 32, Endian.LITTLE),
            "relay": int(1)
        })

        self.HeaderVersion = BitcoinHeader({
        "chain":"regtest",
        "cmd":"version",
        "payload": self.versionPayload
        })
    '''

    #json_object = json.dumps(test1.getDir(), indent = 4, cls=BitcoinEndcoder)   
    #print(json_object)

    #with open("test2.bin", "wb") as binary_file:
    #    binary_file.write(bytes(test1))
    #with open("BitcoinNetworkClient/test/bin/realVersion.bin", "rb") as f:
    #    read = bytes(f.read())

    #print(read)

    #test1 = cutBitcoinMsg(b'\xf9\xbe\xb4\xd9version\x00\x00\x00\x00\x00f\x00\x00\x00I\xae\x1b\x8f\x7f\x11\x01\x00\x08\x04\x00\x00\x00\x00\x00\x00\x88_\xd6_\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfb\xdb\xb92\x99x\xd7\xef\x10/Satoshi:0.20.1/\xc6B\x03\x00\x01\xf9\xbe\xb4\xd9verack\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00]\xf6\xe0\xe2')
    #test2 = cutBitcoinMsg(b'\xf9\xbe\xb4\xd9\xf9\xbe\xb4\xd9\xf9\xbe\xb4\xd9', "main")
    #print(test2.getArrayMsg())



    #test2 = BitcoinHeader(read)
    #print(test2.getDir())
    #print(test2.getHeader())
    #print(test2.getPayloadBytes())
    #print(test2.getDir())
    #json_object = json.dumps(test2, indent = 4, cls=BitcoinEndcoder)   
    #print(json_object)

    '''
    test3 = version({
            "version": Bint(70015, 32, Endian.LITTLE),
            "services": services([services.SERVICES_FLAG.NODE_NETWORK_LIMITED, services.SERVICES_FLAG.NODE_WITNESS]),
            "timestamp": Bint(1607793952, 64, Endian.LITTLE),
            "addr_recv": (NetworkAddress({
                "time": Bint(0, 32, Endian.BIG),
                "services": services([services.SERVICES_FLAG.NODE_NETWORK, services.SERVICES_FLAG.NODE_WITNESS, services.SERVICES_FLAG.NODE_NETWORK_LIMITED]),
                "IPv6/4": ipaddress.ip_address('193.42.110.30'),
                "port": Bint(8333, 16, Endian.BIG)
        })),
            "addr_from": (NetworkAddress({
                "time": Bint(0, 32, Endian.BIG),
                "services": services([services.SERVICES_FLAG.NODE_WITNESS, services.SERVICES_FLAG.NODE_NETWORK_LIMITED]),
                "IPv6/4": ipaddress.ip_address('::'),
                "port": Bint(0, 16, Endian.BIG)
        })),
            "nonce": Bint(508788465527495011, 64, Endian.LITTLE),
            "user_agent": Vstr("/Satoshi:0.20.1/"),
            "start_height": Bint(182915, 32, Endian.LITTLE),
            "relay": int(1)
    })

    test1 = BitcoinHeader({
        "chain":"main",
        "cmd":"version",
        "payload": test3
    })

    json_object = json.dumps(test1, indent = 4, cls=BitcoinEndcoder)   
    print(json_object)
    #print(bytes(test3))

    '''

    #test1 = BitcoinHeader({
    #    "chain":"main",
    #    "cmd":"verack",
    #    "payload": verack()
    #})

    #0000000000000408 :: 10000001000 :: 1032 :: Witness Net_Limit
    #0000000000000409 :: 10000001001 :: 1033 :: Witness Net_Limit Net
    #000000000000040d :: 10000001101 :: 1037 :: Witness Net_Limit Net Bloom
    #ser1 = services(b'\x08\x04\x00\x00\x00\x00\x00\x00')
    #ser2 = services(b'\x09\x04\x00\x00\x00\x00\x00\x00')
    #ser3 = services(b'\x0d\x04\x00\x00\x00\x00\x00\x00')
    #print(ser1.getServicesNamesStr())
    #print(ser2.getServicesNamesStr())
    #print(ser3.getServicesNamesStr())
    #ser1 = services([services.SERVICES_FLAG.NODE_WITNESS, services.SERVICES_FLAG.NODE_NETWORK_LIMITED])
    #ser2 = services([services.SERVICES_FLAG.NODE_NETWORK, services.SERVICES_FLAG.NODE_WITNESS, services.SERVICES_FLAG.NODE_NETWORK_LIMITED])
    #ser3 = services([services.SERVICES_FLAG.NODE_NETWORK, services.SERVICES_FLAG.NODE_WITNESS, services.SERVICES_FLAG.NODE_NETWORK_LIMITED, services.SERVICES_FLAG.NODE_BLOOM])
    #print(bytes(ser1))
    #print(ser1.getServicesHex())
    #print(bytes(ser2))
    #print(ser2.getServicesHex())
    #print(bytes(ser3))
    #print(ser3.getServicesHex())
    #print(test3.getServicesNamesStr())
    #test3 = services([services.SERVICES_FLAG.NODE_NETWORK, services.SERVICES_FLAG.NODE_WITNESS, services.SERVICES_FLAG.NODE_NETWORK_LIMITED])
    #print(bytes(test3))
    #test4 = services([services.SERVICES_FLAG.NODE_NETWORK_LIMITED, services.SERVICES_FLAG.NODE_WITNESS, services.SERVICES_FLAG.NODE_NETWORK])
    #print(test4.getServicesHex())
    #print(bytes(test4))
    #print(test4.getServicesNamesStr())

    #print(data1util.getTimefromByte(time))


    #test1 = NetworkAddress({
    #    "time": Bint(data1util.getByteTime(), 32, Endian.BIG),
    #    "services": services([services.SERVICES_FLAG.NODE_NETWORK]),
    #    "IPv6/4": ipaddress.ip_address('10.0.0.1'),
    #    "port": Bint(8333, 16, Endian.BIG)
    #    })

    #print(bytes(test1))
    #print(test1.getDir())
    #json_object = json.dumps(test1, indent = 4, cls=BitcoinEndcoder)
    #print(json_object)

    #test2 = NetworkAddress(b'_\xd4\xed\x8e\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\n\x00\x00\x01 \x8d')
    #print(test2.getDir())
    #json_object = json.dumps(test2, indent = 4, cls=BitcoinEndcoder)
    #print(json_object)
    #print(test1.getTime())
    #print(test1.getServices())
    #print(test1.getIP())
    #print(test1.getPort())
    #print(bytes(test1))
    #print(len(test1))

    

    #test2 = NetworkAddress(b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\n\x00\x00\x01 \x8d")
    #print(test2.getTime())
    #print(test2.getServices())
    #print(test2.getIP())
    #print(test2.getPort())
    #print(len(test2))
    #print(bytes(test2))

    #print(ip.version)
    #test1 = Vint(b'\xfd\x01\xa6')
    #print(int(test1))
    #print(bytes(test1))
    #print(test1.getHex())
    #print(len(test1))

    #test1 = Vstr(b'\x17/Satoshi:0.20.99/(test)')
    #print(bytes(test1))
    #print(str(test1))
    #print(len(test1))

    #test1 = Bint(123456789,32,Endian.BIG)
    #print(int(test1))
    #print(bytes(test1))
    #print(test1.getHex())

    #test2 = Bchar("version",0,Endian.BIG)
    #print(str(test2))
    #print(bytes(test2))
    #print(test2.length)
    #print(test2.getHex())

    




    #test1 = binary("/Satoshi:0.20.99/(test)", 1, False)
    #print(test1.datastring)
    #print(test1.datahex)
    #print(test1.databin)
    #test2 = binary(test1.datalen, 1, False)

    #with open("test2.bin", "wb") as binary_file:
    #    binary_file.write(test2.databin + test1.databin)

    #print("\n")
    #test2 = binary(100, 8, True)
    #print(test2.datastring)
    #print(test2.datahex)
    #print(test2.databin)

    #print("\n")
    #b'\xD9\xB4\xBE\xF9'
    #test3 = binary(b'\x70\x61\x75\x6c', 8, False)
    #print(test3.datastring)
    #print(test3.datahex)
    #print(test3.databin)
    
    #print("\n")
    #test4 = binary(b'\xD9\xB4\xBE\xF9', 4, True)
    #print(test4.datastring)
    #print(test4.datahex)
    #print(test4.databin)
