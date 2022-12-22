from panda3d.core import QueuedConnectionManager, QueuedConnectionListener, QueuedConnectionReader
from panda3d.core import ConnectionWriter

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
