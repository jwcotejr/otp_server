from direct.directnotify import DirectNotifyGlobal
from direct.fsm.FSM import FSM

from otp.core import MsgTypes

import semidbm


class ClientOperation(FSM):

    def __init__(self, manager, client):
        FSM.__init__(self, self.__class__.__name__)

        # Our account manager:
        self.manager = manager

        # Our target client:
        self.client = client


class LoginAccountFSM(ClientOperation):
    notify = DirectNotifyGlobal.directNotify.newCategory('LoginAccountFSM')

    def __init__(self, manager, client):
        ClientOperation.__init__(self, manager, client)

        # Our target client's play token:
        self.playToken = None

        # Our target client's account ID:
        self.accountId = None

    def enterStart(self, playToken):
        # Store our play token:
        self.playToken = playToken

        # Check if our play token exists in the accounts database:
        if self.playToken not in self.manager.dbm:
            # It does not, so we will create a new account object:
            self.demand('CreateAccount')
            return

        # It does, so we will query the database for our account object.
        # First, store our account ID:
        self.accountId = int(self.manager.dbm[self.playToken])

        # Next, query the database. We don't need to query for any
        # fields, we're just ensuring that the account object exists
        # in the database:
        self.manager.acceptor.dbInterface.getStoredValues(
            self.client,
            MsgTypes.DBSERVER_ID,
            self.accountId,
            [],
            self.__handleQueried)

    def __handleQueried(self, dclass, _):
        # Is this an Account DC class?
        if dclass != dcFile.getClassByName('Account'):
            # It is not; likely the account ID was not found in the database. Warn the user:
            self.notify.warning('Account %s for client %s with play token %s not found in the database!' % (
                self.accountId, self.client.getChannel(), self.playToken))
            return

        self.demand('GotAccount')


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
        # LoginAccountFSM will handle the rest:
        self.runOperation(client, LoginAccountFSM, playToken)
