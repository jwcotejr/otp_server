from otp.net.NetworkClient import NetworkClient
from otp.core.Globals import ClientState


class Client(NetworkClient):

    def __init__(self, acceptor, client, channel):
        NetworkClient.__init__(self, acceptor, client)

        self.channel = channel
        self.state = ClientState.NEW
