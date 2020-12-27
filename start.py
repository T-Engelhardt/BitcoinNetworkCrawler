#import threading
import logging
import sys
from BitcoinNetworkClient.util.configParser import config
import BitcoinNetworkClient.Main
import argparse
import pathlib

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, help="path to config file")
    args = parser.parse_args()

    #if no path is spezified choose default
    if(args.config):
        path = args.config
        if(str(path).count("/") == 0):
            #file in current dir
            path = str(pathlib.Path(__file__).parent.absolute()) + "/" + path
    else:
        path = str(pathlib.Path(__file__).parent.absolute()) + "/default.yaml"

    #print settings for user
    print("\t\nLoading config file : " + str(path))
    cfg = config(path)
    print(str(cfg))

    #threading.settrace(BitcoinNetworkClient.Main.start())
    BitcoinNetworkClient.Main.start(cfg)
