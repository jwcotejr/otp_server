from otp.net.NetworkAcceptor import NetworkAcceptor
from otp.messagedirector.MDParticipant import MDParticipant


class MessageDirector(NetworkAcceptor):

    def __init__(self, host, port):
        NetworkAcceptor.__init__(self, host, port)

        # A dictionary of connections to participants:
        self.participants = {}

    def createClient(self, connection):
        participant = MDParticipant(self, connection)
        self.participants[connection] = participant
