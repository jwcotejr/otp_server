from otp.net.NetworkClient import NetworkClient


class MDParticipant(NetworkClient):

    def __init__(self, acceptor, connection):
        NetworkClient.__init__(self, acceptor, connection)
