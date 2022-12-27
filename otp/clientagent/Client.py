from direct.distributed.PyDatagram import PyDatagram

from otp.net.NetworkClient import NetworkClient
from otp.core.Globals import ClientState
from otp.core import MsgTypes
from otp.core import Types


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
        datagram.addUint64(Types.BCHAN_MESSAGEDIRECTOR)  # Message Director channel.
        datagram.addUint64(self.channel)  # Source channel.
        datagram.addUint16(msgType)  # Message type.
        return datagram

    def subscribeChannel(self, channel):
        """
        Subscribes to a channel.
        """
        datagram = self.createHandledDatagram(MsgTypes.CONTROL_SET_CHANNEL)
        datagram.addUint64(channel)
        self.sendUpstream(datagram)
