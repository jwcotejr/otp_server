from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator

from otp.net.NetworkAcceptor import NetworkAcceptor
from otp.messagedirector.MDParticipant import MDParticipant
from otp.messagedirector.ChannelMap import ChannelMap
from otp.core import MsgTypes


class MessageDirector(NetworkAcceptor):

    def __init__(self, host, port):
        NetworkAcceptor.__init__(self, host, port)

        # A dictionary of connections to participants:
        self.participants = {}

        # The map of channels to list of participants:
        self.channelMap = ChannelMap()

    def subscribeChannel(self, participant, channel):
        """
        Subscribes a participant to a channel.
        """
        self.channelMap.subscribe(participant, channel)

    def unsubscribeChannel(self, participant, channel):
        """
        Unsubscribes a participant from a channel.
        """
        self.channelMap.unsubscribe(participant, channel)

    def createClient(self, connection):
        participant = MDParticipant(self, connection)
        self.participants[connection] = participant

    def removeClient(self, client):
        # First, check to see if the client is connected:
        if not client.isConnected():
            return

        self.connectionReader.removeConnection(client.getConnection())
        self.connectionManager.closeConnection(client.getConnection())
        del self.participants[client.getConnection()]

    def handleClientDatagram(self, datagram):
        """
        Handles a datagram sent by a participant.
        """

        # First, we need to extract all of the channels from the datagram:
        dgi = PyDatagramIterator(datagram)
        channels = []
        channelCount = dgi.getUint8()

        # Extract all of the channels:
        for _ in range(channelCount):
            channel = dgi.getUint64()
            channels.append(channel)

        # Get the participant from the connection:
        connection = datagram.getConnection()
        participant = self.participants[connection]

        # Check if the message is going to us:
        if channelCount == 1 and channels[0] == MsgTypes.CONTROL_MESSAGE:
            # Handle the message directly:
            participant.handleClientDatagram(dgi)
            return

        # It doesn't look like we are handling the message directly; look up our participants:
        participants = self.lookupParticipants(channels)

        # We want to remove the sender from the participant list:
        if participant in participants:
            participants.remove(participant)

        # Create a datagram out of our remaining bytes:
        datagram = PyDatagram(dgi.getRemainingBytes())

        # Iterate through the participants and send them the message:
        for targetParticipant in participants:
            targetParticipant.sendDownstream(datagram)

    def lookupParticipants(self, channels):
        """
        Gets all of the participants subscribed to a certain channel.
        """
        participants = []

        # Iterate through all of our channels:
        for channel in channels:
            # Fetch the participants:
            participants.extend(self.channelMap.getParticipantsFromChannel(channel))

        # Return our list of participants:
        return participants
