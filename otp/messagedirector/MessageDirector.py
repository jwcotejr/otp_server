from otp.net.NetworkAcceptor import NetworkAcceptor


class MessageDirector(NetworkAcceptor):

    def __init__(self, host, port):
        NetworkAcceptor.__init__(self, host, port)
