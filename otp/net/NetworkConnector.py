from panda3d.core import QueuedConnectionManager, QueuedConnectionReader
from panda3d.core import ConnectionWriter, NetDatagram

from direct.task.TaskManagerGlobal import taskMgr

from otp.core.UniqueObject import UniqueObject


class NetworkConnector(UniqueObject):

    def __init__(self, host, port):
        self.host = host
        self.port = port

        # Set up our networking interfaces:
        self.connectionManager = QueuedConnectionManager()
        self.connectionReader = QueuedConnectionReader(self.connectionManager, 0)
        self.connectionWriter = ConnectionWriter(self.connectionManager, 0)

        self.connection = self.connectionManager.openTCPClientConnection(host, port, 10)
        self.connectionReader.addConnection(self.connection)

        taskMgr.add(self.readerPollTask, self.uniqueName('reader-poll-task'))

    def readerPollTask(self, task):
        """
        Continuously polls for new messages on the server.
        """
        while self.readerPollOnce():
            pass

        return task.cont

    def readerPollOnce(self):
        """
        Checks for messages available to the server.
        """
        # Check if we have any data available:
        dataAvailable = self.connectionReader.dataAvailable()
        if dataAvailable:
            # Get the data:
            datagram = NetDatagram()
            if self.connectionReader.getData(datagram):
                # We got the data! We can now process it:
                self.handleServerDatagram(datagram)

        return dataAvailable

    def sendUpstream(self, datagram):
        self.connectionWriter.send(datagram, self.connection)

    def closeConnection(self):
        """
        Close the connection.
        """
        self.connectionReader.removeConnection(self.connection)
        self.connectionManager.closeConnection(self.connection)

    def handleServerDatagram(self, datagram):
        # Must be overridden by subclass.
        raise NotImplementedError
