from panda3d.core import QueuedConnectionManager, QueuedConnectionListener, QueuedConnectionReader
from panda3d.core import ConnectionWriter, PointerToConnection, NetAddress

from otp.core.UniqueObject import UniqueObject


class NetworkAcceptor(UniqueObject):

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.connectionManager = QueuedConnectionManager()
        self.connectionListener = QueuedConnectionListener(self.connectionManager, 0)
        self.connectionReader = QueuedConnectionReader(self.connectionManager, 0)
        self.connectionWriter = ConnectionWriter(self.connectionManager, 0)

        self.tcpSocket = self.connectionManager.openTCPServerRendezvous(host, port, 1000)
        self.connectionListener.addConnection(self.tcpSocket)

        taskMgr.add(self.listenerPollTask, self.uniqueName('listener-poll-task'))
        taskMgr.add(self.readerPollTask, self.uniqueName('reader-poll-task'))

    def listenerPollTask(self, task):
        # Listens for new connections (i.e. new clients)
        if self.connectionListener.newConnectionAvailable():
            rendezvous = PointerToConnection()
            netAddress = NetAddress()
            connection = PointerToConnection()
            if self.connectionListener.getNewConnection(rendezvous, netAddress, connection):
                # We got a new connection!

                # Dereference:
                connection = connection.p()

                # Now we can start listening to our new connection:
                self.connectionReader.addConnection(connection)

                # Create the client instance for our new connection:
                self.createClient(connection)

        return task.cont
