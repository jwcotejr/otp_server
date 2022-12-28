from otp.net.NetworkClient import NetworkClient
from otp.core import MsgTypes


class MDParticipant(NetworkClient):

    def __init__(self, acceptor, connection):
        NetworkClient.__init__(self, acceptor, connection)

        # A list of our subscribed channels:
        self.channels = []

    def handleClientDatagram(self, dgi):
        """
        Handle a datagram sent by the client.
        """
        msgType = dgi.getUint16()

        if msgType == MsgTypes.CONTROL_SET_CHANNEL:
            self.handleControlSetChannel(dgi)

    def handleControlSetChannel(self, dgi):
        # Get the channel we want to subscribe to:
        channel = dgi.getUint64()

        # Subscribe to the channel:
        self.subscribeChannel(channel)

    def subscribeChannel(self, channel):
        self.channels.append(channel)
        self.acceptor.subscribeChannel(self, channel)
