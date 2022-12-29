from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator

from otp.net.NetworkConnector import NetworkConnector
from otp.database import DBBackendFactory
from otp.core import MsgTypes


class DatabaseServer(NetworkConnector):

    def __init__(self, control, generateMin, generateMax, backendConfig, mdHost, mdPort):
        NetworkConnector.__init__(self, mdHost, mdPort)

        # Control channel that we will subscribe to:
        self.control = control

        # Create our backend:
        backendName = backendConfig['type']
        self.backend = DBBackendFactory.createBackend(backendName, backendConfig, generateMin, generateMax)

        # Subscribe to our control channel:
        self.subscribeChannel(self.control)

    def createHandledDatagram(self, msgType):
        """
        Creates a datagram that will be handled on the Message Director.
        """
        datagram = PyDatagram()
        datagram.addUint8(1)  # One channel.
        datagram.addUint64(MsgTypes.CONTROL_MESSAGE)  # Control message.
        datagram.addUint16(msgType)  # Message type.
        return datagram

    def subscribeChannel(self, channel):
        """
        Subscribes to a channel.
        """
        datagram = self.createHandledDatagram(MsgTypes.CONTROL_SET_CHANNEL)
        datagram.addUint64(channel)  # Channel we are subscribing to.

        # Send the datagram to the message director:
        self.sendUpstream(datagram)

    def handleServerDatagram(self, datagram):
        """
        Handles a datagram from the Message Director.
        """
        dgi = PyDatagramIterator(datagram)

        # Get the source channel:
        channel = dgi.getUint64()

        # Get the message type:
        msgType = dgi.getUint16()

        # Handle the message:

    @staticmethod
    def createFromConfig(serviceConfig):
        # Do we have a Message Director?
        mdConfig = config.get('messagedirector', {})
        if not mdConfig:
            # If we don't have a Message Director, we cannot create a Database Server.
            raise Exception('Cannot create a Database Server without a Message Director!')

        # Get our config values:
        control = serviceConfig['control']
        generateMin = serviceConfig['generate']['min']
        generateMax = serviceConfig['generate']['max']
        backendConfig = serviceConfig['backend']
        mdHost = mdConfig['host']
        mdPort = mdConfig['port']

        # Create our DatabaseServer service:
        DatabaseServer(control, generateMin, generateMax, backendConfig, mdHost, mdPort)
