from panda3d.core import UniqueIdAllocator

from otp.net.NetworkAcceptor import NetworkAcceptor
from otp.clientagent.ToontownClient import ToontownClient


class ClientAgent(NetworkAcceptor):

    def __init__(self, host, port, serverVersion, dcHash, channelMin, channelMax, mdHost, mdPort):
        NetworkAcceptor.__init__(self, host, port)

        # Set our server version:
        self.serverVersion = serverVersion

        # Set our DC hash:
        self.dcHash = dcHash
        if self.dcHash is None:
            self.dcHash = dcFile.getHash()

        # Create our channel allocator:
        self.channelAllocator = UniqueIdAllocator(channelMin, channelMax)

        # Message Director info:
        self.mdHost = mdHost
        self.mdPort = mdPort

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
        client = ToontownClient(self, connection, channel, self.mdHost, self.mdPort)
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
    def createFromConfig(serviceConfig):
        # Do we have a Message Director?
        mdConfig = config.get('messagedirector', {})
        if not mdConfig:
            # If we don't have a Message Director, we cannot create a Client Agent.
            raise Exception('Cannot create a Client Agent without a Message Director!')

        # Get our config values:
        host = serviceConfig['host']
        port = serviceConfig['port']
        serverVersion = serviceConfig['server-version']
        dcHash = serviceConfig.get('dc-hash')
        channelMin = serviceConfig['channels']['min']
        channelMax = serviceConfig['channels']['max']
        mdHost = mdConfig['host']
        mdPort = mdConfig['port']

        # Create our ClientAgent service:
        ClientAgent(host, port, serverVersion, dcHash, channelMin, channelMax, mdHost, mdPort)
