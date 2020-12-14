from time import time, sleep
from BitcoinNetworkClient.BitcoinData.bitcoinParser import BitcoinEndcoder, cutBitcoinMsg
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
import ipaddress
from BitcoinNetworkClient.util.data2 import NetworkAddress, Vstr, services
from BitcoinNetworkClient.util.data1 import Bint, Endian, data1util
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import version
import socket
import json
import random

class send:

    def __init__(self):
        self.start()

    def start(self):

        payloadversion = version({
            "version": Bint(70015, 32, Endian.LITTLE),
            "services": services([services.SERVICES_FLAG.NODE_NETWORK_LIMITED, services.SERVICES_FLAG.NODE_WITNESS]),
            "timestamp": Bint(int(time()), 64, Endian.LITTLE),
            "addr_recv": (NetworkAddress({
                "time": Bint(0, 32, Endian.BIG),
                "services": services([services.SERVICES_FLAG.NODE_WITNESS, services.SERVICES_FLAG.NODE_NETWORK_LIMITED]),
                "IPv6/4": ipaddress.ip_address('127.0.0.1'),
                "port": Bint(8333, 16, Endian.BIG)
            })),
            "addr_from": (NetworkAddress({
                "time": Bint(0, 32, Endian.BIG),
                "services": services([]),
                "IPv6/4": ipaddress.ip_address('::'),
                "port": Bint(0, 16, Endian.BIG)
            })),
            "nonce": Bint(random.getrandbits(64), 64, Endian.LITTLE),
            "user_agent": Vstr("/Satoshi:0.20.1/(PythonClient)"),
            "start_height": Bint(0, 32, Endian.LITTLE),
            "relay": int(0)
        })

        header = BitcoinHeader({
            "chain":"main",
            "cmd":"version",
            "payload": payloadversion
        })

        json_object = json.dumps(header, indent = 4, cls=BitcoinEndcoder)   
        print(json_object)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 8333))
        s.send(bytes(header))
        response_data = s.recv(4096)
        print(response_data)
        response_data2 = s.recv(4096)
        print(response_data2)
        response_data3 = response_data + response_data2
        cutMsg = cutBitcoinMsg(response_data3, "main")
        for x in cutMsg.getArrayMsg():   
            tmp = BitcoinHeader(x)
            json_object = json.dumps(tmp, indent = 4, cls=BitcoinEndcoder)
            print(json_object)

        while(1):
            pass