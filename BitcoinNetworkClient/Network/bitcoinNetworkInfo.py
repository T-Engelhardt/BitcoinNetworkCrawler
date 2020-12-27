class bitcoinNetInfo:

    def __init__(self, chain: str, ip: str, port: int) -> None:
        self.chain = chain
        self.ip = ip
        self.port = port

    def getChain(self) -> str:
        return self.chain

    def getIP(self) -> str:
        return self.ip

    def getPort(self) -> int:
        return self.port

    def getNetArray(self):
        return [self.getChain(), self.getIP(), self.getPort()]

    def __str__(self) -> str:
        return str(self.getNetArray())