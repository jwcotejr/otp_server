from direct.distributed.PyDatagram import PyDatagram

from otp.net.NetworkClient import NetworkClient
from otp.core.Globals import ClientState
from otp.core import MsgTypes


class Client(NetworkClient):

    def __init__(self, acceptor, client, channel):
        NetworkClient.__init__(self, acceptor, client)

        self.channel = channel
        self.state = ClientState.NEW

        # Subscribe to our own channel and the client channel:
        self.subscribeChannel(self.channel)
        self.subscribeChannel(MsgTypes.CHANNEL_CLIENT_BROADCAST)

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
