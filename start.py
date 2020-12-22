import threading
import BitcoinNetworkClient.Main

if __name__ == "__main__":
    threading.settrace(BitcoinNetworkClient.Main.start())
