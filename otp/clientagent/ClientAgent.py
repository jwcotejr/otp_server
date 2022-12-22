from otp.net.NetworkAcceptor import NetworkAcceptor


class ClientAgent(NetworkAcceptor):

    def __init__(self, host, port, serverVersion, dcHash, channelMin, channelMax):
        NetworkAcceptor.__init__(self, host, port)

    @staticmethod
    def createFromConfig(config):
        # Get our config values:
        host = config['host']
        port = config['port']
        serverVersion = config['server-version']
        dcHash = config.get('dc-hash')
        channelMin = config['channels']['min']
        channelMax = config['channels']['max']

        # Create our ClientAgent service:
        ClientAgent(host, port, serverVersion, dcHash, channelMin, channelMax)
