from otp.core.UniqueObject import UniqueObject


class NetworkClient(UniqueObject):

    def __init__(self, acceptor, connection):
        self.acceptor = acceptor
        self.connection = connection
        self.connected = True

        # Run our tasks to make sure the client is connected:
        taskMgr.add(self.monitorTask, self.uniqueName('monitor-task'))

    def sendDownstream(self, datagram):
        self.acceptor.connectionWriter.send(datagram, self.connection)

    def isConnected(self):
        return self.connected

    def getConnection(self):
        return self.connection

    def cleanup(self):
        taskMgr.remove(self.uniqueName('monitor-task'))

    def handleDisconnect(self):
        raise NotImplementedError

    def monitorTask(self, task):
        if not self.acceptor.connectionReader.isConnectionOk(self.connection):
            self.handleDisconnect()
            self.connected = False
            self.cleanup()

        return task.cont
