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

    def createClient(self, connection):
        participant = MDParticipant(self, connection)
        self.participants[connection] = participant

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

        # Check if the message is going to us:
        if channelCount == 1 and channels[0] == MsgTypes.CONTROL_MESSAGE:
            # Since this message is being handled by us, we will need to get the participant via the connection:
            connection = datagram.getConnection()
            participant = self.participants[connection]

            # Now that we have the participant, we can have them handle the message directly:
            participant.handleClientDatagram(dgi)
            return
