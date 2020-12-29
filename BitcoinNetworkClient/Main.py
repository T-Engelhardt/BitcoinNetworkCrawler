from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from BitcoinNetworkClient.util.configParser import config

from BitcoinNetworkClient.Network.networkQueue import NetworkQueue

from systemd.journal import JournalHandler
import sys
import logging

#tmp
from BitcoinNetworkClient.util.data2 import Vint, onionV2, onionV3, services
from BitcoinNetworkClient.BitcoinData.bitcoinData import BitcoinHeader
from BitcoinNetworkClient.BitcoinData.bitcoinParser import BitcoinEndcoder
from BitcoinNetworkClient.BitcoinData.bitcoinPayload import addrv2
from BitcoinNetworkClient.util.data1 import Bint, Endian
import json


def start(cfg: config):
    
    print("RUN")
    
    logging.basicConfig(level=cfg.getLogLevel(), format='%(asctime)s %(levelname)s (%(threadName)-10s) %(message)s', datefmt='%d.%m.%Y %H:%M:%S')

    #enable systemd logging
    #https://trstringer.com/systemd-logging-in-python/
    #https://stackoverflow.com/questions/34588421/how-to-log-to-journald-systemd-via-python
    if(cfg.getLogSystemd):
        #TODO not tested
        log = logging.getLogger(__name__)
        log.addHandler(JournalHandler())

    q = NetworkQueue(cfg)
    q.start()
    sys.exit(0)

    #print(str(onionV3(b'\xe7xV\xe1M\x80\x16\xdf\xc4\xa7\x02,\x7f\nQ\x18f\xe0\xba\x1d\xc3\x01\xfb\xd0\x04\xac\xad2|\xa9\x14\xc5')))
    #print(bytes(onionV3("454fnyknqaln7rfhaiwh6csrdbtoboq5yma7xuaevswte7fjctc7j2yd.onion")))
    #b'\x12\xd7J\xe4\xcb\x88\xc2WD\xa7' = clluvzglrdbforfh.onion
    
    #with open("BitcoinNetworkClient/test/bin/addrv2.bin", "rb") as f:
    #    read = bytes(f.read())

    #addrv2Obj = BitcoinHeader(read)

    #json_object = json.dumps(addrv2Obj, indent = 4, cls=BitcoinEndcoder)
    #print(json_object)

    #with open("payloadAddrv2.bin", "wb") as binary_file:
    #    binary_file.write(addrv2.getPayloadBytes())
