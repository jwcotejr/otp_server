from otp.core.UniqueObject import UniqueObject


class NetworkConnector(UniqueObject):

    def __init__(self, host, port):
        self.host = host
        self.port = port
