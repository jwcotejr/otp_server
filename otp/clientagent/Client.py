from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator

from otp.net.NetworkClient import NetworkClient
from otp.net.NetworkConnector import NetworkConnector
from otp.core.Globals import ClientState
from otp.core import MsgTypes
from otp.clientagent import ClientMessages


class Client(NetworkClient):

    def __init__(self, acceptor, client, channel, mdHost, mdPort):
        NetworkClient.__init__(self, acceptor, client)

        self.channel = channel
        self.state = ClientState.NEW

        # Create our connection to the Message Director and override a method:
        self.mdConnection = NetworkConnector(mdHost, mdPort)
        self.mdConnection.handleServerDatagram = self.handleServerDatagram

        # Subscribe to our own channel and the client channel:
        self.subscribeChannel(self.channel)
        self.subscribeChannel(MsgTypes.CHANNEL_CLIENT_BROADCAST)

    def handleClientDatagram(self, datagram):
        """
        Handles a datagram coming from the client.
        """
        dgi = PyDatagramIterator(datagram)

        if self.state == ClientState.NEW:
            self.handlePreAuth(dgi)

    def handlePreAuth(self, dgi):
        # Must be overridden by subclass.
        raise NotImplementedError

    def handleServerDatagram(self, datagram):
        """
        Handles a datagram coming from the Message Director.
        """
        raise NotImplementedError

    def createHandledDatagram(self, msgType):
        """
        Creates a datagram that will be handled on the Message Director.
        """
        datagram = PyDatagram()
        datagram.addUint8(1)  # One channel.
        datagram.addUint64(MsgTypes.CONTROL_MESSAGE)  # Control message.
        datagram.addUint16(msgType)  # Message type.
        return datagram

    def sendUpstream(self, datagram):
        """
        Sends a datagram to the Message Director.
        """
        self.mdConnection.sendUpstream(datagram)

    def subscribeChannel(self, channel):
        """
        Subscribes to a channel.
        """
        datagram = self.createHandledDatagram(MsgTypes.CONTROL_SET_CHANNEL)
        datagram.addUint64(channel)  # Channel we are subscribing to.
        self.sendUpstream(datagram)

    def handleDisconnect(self):
        """
        Handles a client disconnect.
        """
        self.acceptor.deallocateChannel(self.channel)
        self.acceptor.removeClient(self)
        self.mdConnection.closeConnection()
        self.connected = False

    def sendDisconnect(self, reason, message):
        if not self.connected:
            return

        datagram = PyDatagram()
        datagram.addUint16(ClientMessages.CLIENT_GO_GET_LOST)
        datagram.addUint16(reason)
        datagram.addString(message)
        self.sendDownstream(datagram)
        self.handleDisconnect()
