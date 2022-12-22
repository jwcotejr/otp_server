from panda3d.core import UniqueIdAllocator

from otp.net.NetworkAcceptor import NetworkAcceptor
from otp.clientagent.Client import Client


class ClientAgent(NetworkAcceptor):

    def __init__(self, host, port, serverVersion, dcHash, channelMin, channelMax):
        NetworkAcceptor.__init__(self, host, port)

        # Set our server version:
        self.serverVersion = serverVersion

        # Set our DC hash:
        self.dcHash = dcHash
        if self.dcHash is None:
            self.dcHash = dcFile.getHash()

        # Create our channel allocator:
        self.channelAllocator = UniqueIdAllocator(channelMin, channelMax)

        # A dictionary of connections to clients:
        self.clients = {}

    def allocateChannel(self):
        return self.channelAllocator.allocate()

    def createClient(self, connection):
        channel = self.allocateChannel()
        client = Client(self, connection, channel)
        self.clients[connection] = client

    def handleClientDatagram(self, datagram):
        """
        Handles a datagram sent by a client.
        """

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
