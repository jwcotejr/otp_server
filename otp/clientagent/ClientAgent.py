from panda3d.core import UniqueIdAllocator

from otp.net.NetworkAcceptor import NetworkAcceptor
from otp.clientagent.ToontownClient import ToontownClient


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

    def getDcHash(self):
        return self.dcHash

    def getServerVersion(self):
        return self.serverVersion

    def allocateChannel(self):
        return self.channelAllocator.allocate()

    def deallocateChannel(self, channel):
        self.channelAllocator.free(channel)

    def createClient(self, connection):
        channel = self.allocateChannel()
        client = ToontownClient(self, connection, channel)
        self.clients[connection] = client

    def removeClient(self, client):
        # First, check to see if the client is connected:
        if not client.isConnected():
            return

        self.connectionReader.removeConnection(client.getConnection())
        self.connectionManager.closeConnection(client.getConnection())
        del self.clients[client.getConnection()]

    def handleClientDatagram(self, datagram):
        """
        Handles a datagram sent by a client.
        """
        connection = datagram.getConnection()
        self.clients[connection].handleClientDatagram(datagram)

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
