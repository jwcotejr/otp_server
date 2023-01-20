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
        elif msgType == MsgTypes.CONTROL_REMOVE_CHANNEL:
            self.handleControlRemoveChannel(dgi)

    def handleControlSetChannel(self, dgi):
        # Get the channel we want to subscribe to:
        channel = dgi.getUint64()

        # Subscribe to the channel:
        self.subscribeChannel(channel)

    def handleControlRemoveChannel(self, dgi):
        # Get the channel we want to unsubscribe from:
        channel = dgi.getUint64()

        # Unsubscribe from the channel:
        self.unsubscribeChannel(channel)

    def subscribeChannel(self, channel):
        self.channels.append(channel)
        self.acceptor.subscribeChannel(self, channel)

    def unsubscribeChannel(self, channel):
        self.channels.remove(channel)
        self.acceptor.unsubscribeChannel(self, channel)

    def handleDisconnect(self):
        """
        Gets called when the participant loses connection to the Message Director.
        """
        # Unsubscribe from all of our channels:
        for channel in self.channels[:]:
            self.unsubscribeChannel(channel)

        # Remove the participant:
        self.acceptor.removeClient(self)
        self.connected = False
