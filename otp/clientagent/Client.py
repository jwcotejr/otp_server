from otp.net.NetworkClient import NetworkClient


class Client(NetworkClient):

    def __init__(self, acceptor, client, channel):
        NetworkClient.__init__(self, acceptor, client)

        self.channel = channel
