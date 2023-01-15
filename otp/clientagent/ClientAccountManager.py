from direct.directnotify import DirectNotifyGlobal
from direct.fsm.FSM import FSM

import semidbm


class ClientOperation(FSM):

    def __init__(self, manager, client):
        FSM.__init__(self, self.__class__.__name__)
        self.manager = manager
        self.client = client


class ClientOperationManager:
    notify = DirectNotifyGlobal.directNotify.newCategory('ClientOperationManager')

    def __init__(self, acceptor):
        self.acceptor = acceptor

        # A dictionary of client channels to operations:
        self.channel2operation = {}

    def runOperation(self, client, operationType, *args):
        # Get the client channel:
        channel = client.getChannel()

        # Check if an operation is already running for this client:
        operation = self.channel2operation.get(channel)
        if operation:
            # We can only run one operation at a time. Warn the user:
            self.notify.warning('An operation (%s) is already running for client %s' % (operation.name, channel))
            return

        # Create the new operation and start it:
        newOperation = operationType(self, client)
        self.channel2operation[channel] = newOperation
        newOperation.request('Start', *args)


class ClientAccountManager(ClientOperationManager):

    def __init__(self, acceptor):
        ClientOperationManager.__init__(self, acceptor)

        # Create our dbm:
        self.dbm = semidbm.open('databases/accounts', 'c')

    def handleLogin(self, client, playToken):
        pass  # TODO
