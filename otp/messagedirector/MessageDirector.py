from otp.net.NetworkAcceptor import NetworkAcceptor


class MessageDirector(NetworkAcceptor):

    def __init__(self, host, port):
        NetworkAcceptor.__init__(self, host, port)

    @staticmethod
    def createFromConfig(config):
        host = config['host']
        port = config['port']
        MessageDirector(host, port)
