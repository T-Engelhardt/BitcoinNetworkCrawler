from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from BitcoinNetworkClient.util.configParser import config

from BitcoinNetworkClient.Network.networkQueue import NetworkQueue

import sys
import logging


def start(cfg: config):
    
    print("RUN")
    
    logging.basicConfig(level=cfg.getLogLevel(), format='%(asctime)s %(levelname)s (%(threadName)-10s) %(message)s', datefmt='%d.%m.%Y %H:%M:%S')

    q = NetworkQueue(cfg)
    q.start()
    sys.exit(0)

    #with open("BitcoinNetworkClient/test/bin/addr1000.bin", "rb") as f:
    #    read = bytes(f.read())
    #print(read)

    #json_object = json.dumps(BitcoinHeader(read), indent = 4, cls=BitcoinEndcoder)
    #print(json_object)

    #with open("test2.bin", "wb") as binary_file:
    #    binary_file.write(bytes(test1))