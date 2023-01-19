from direct.directnotify import DirectNotifyGlobal
from direct.fsm.FSM import FSM

from otp.core import MsgTypes

import semidbm
import time


class ClientOperation(FSM):

    def __init__(self, manager, client, callback):
        FSM.__init__(self, self.__class__.__name__)

        # Our account manager:
        self.manager = manager

        # Our target client:
        self.client = client

        # Our callback:
        self.callback = callback

    def enterOff(self, success, *args):
        # Delete this operation from the manager's dictionary:
        del self.manager.channel2operation[self.client.getChannel()]

        # If this operation was successful, and we have a callback, call it:
        if success and self.callback:
            # Pass all remaining args to the callback as well:
            self.callback(*args)


class LoginAccountFSM(ClientOperation):
    notify = DirectNotifyGlobal.directNotify.newCategory('LoginAccountFSM')

    def __init__(self, manager, client, callback):
        ClientOperation.__init__(self, manager, client, callback)

        # Our target client's play token:
        self.playToken = None

        # Our target client's account ID:
        self.accountId = None

        # Our account object's fields:
        self.account = {}

    def enterStart(self, playToken, fields=[]):
        # Store our play token:
        self.playToken = playToken

        # Check if our play token exists in the accounts database:
        if self.playToken.encode('utf-8') not in self.manager.dbm:
            # It does not, so we will create a new account object:
            self.demand('CreateAccount')
            return

        # It does, so we will query the database for our account object.
        # First, store our account ID:
        self.accountId = int(self.manager.dbm[self.playToken])

        # Next, query the database. We are primarily ensuring that the account object exists
        # in the database, however we are also querying for any fields specified by the user:
        self.manager.acceptor.dbInterface.getStoredValues(
            self.client,
            MsgTypes.DBSERVER_ID,
            self.accountId,
            fields,
            self.__handleQueried)

    def __handleQueried(self, dclass, fields):
        # Is this an Account DC class?
        if dclass != dcFile.getClassByName('Account'):
            # It is not; likely the account ID was not found in the database. Warn the user:
            self.notify.warning('Account %s for client %s with play token %s not found in the database!' % (
                self.accountId, self.client.getChannel(), self.playToken))
            self.demand('Off', False)
            return

        # Got the account! Move on to the GotAccount state:
        self.account = fields
        self.demand('GotAccount')

    def enterCreateAccount(self):
        # In this state, we will create a new Account object in the database for this play token.
        # First, set up our dictionary of fields/values we want stored in the new Account object:
        self.account = {
            # ACCOUNT_AV_SET and pirateAvatars defaults are defined in otp.dc
            'HOUSE_ID_SET': [0] * 6,
            'ESTATE_ID': 0,
            'ACCOUNT_AV_SET_DEL': [],
            'CREATED': time.ctime(),
            'LAST_LOGIN': time.ctime()
        }

        # Now, create the new Account object in the database:
        self.manager.acceptor.dbInterface.createStoredObject(
            self.client,
            MsgTypes.DBSERVER_ID,
            MsgTypes.DBSERVER_ACCOUNT_OBJECT_TYPE,
            self.account,
            self.__handleAccountCreated)

    def __handleAccountCreated(self, doId):
        # Are we currently in the CreateAccount state?
        if self.state != 'CreateAccount':
            # We are not, so we should not continue further. Warn the user:
            self.notify.warning('Got account created response for play token %s outside of CreateAccount state!' % (
                self.playToken))
            self.demand('Off', False)
            return

        # Was the account creation successful?
        if not doId:
            # It was not. Warn the user:
            self.notify.warning('Database failed to create new account object for play token %s' % self.playToken)
            self.demand('Off', False)
            return

        # Account created successfully! Store the account ID in the accounts database:
        self.accountId = doId
        self.manager.dbm[self.playToken] = str(self.accountId)
        self.manager.dbm.sync()

        # Got the account! Move on to the GotAccount state:
        self.demand('GotAccount')

    def enterGotAccount(self):
        # We're done here! Move on to the Off state, which will also call our callback.
        # We'll also pass our play token and our account fields to the callback:
        self.demand('Off', True, self.playToken, self.account)


class ClientOperationManager:
    notify = DirectNotifyGlobal.directNotify.newCategory('ClientOperationManager')

    def __init__(self, acceptor):
        self.acceptor = acceptor

        # A dictionary of client channels to operations:
        self.channel2operation = {}

    def runOperation(self, client, operationType, callback, *args):
        # Get the client channel:
        channel = client.getChannel()

        # Check if an operation is already running for this client:
        operation = self.channel2operation.get(channel)
        if operation:
            # We can only run one operation at a time. Warn the user:
            self.notify.warning('An operation (%s) is already running for client %s' % (operation.name, channel))
            return

        # Create the new operation and start it:
        newOperation = operationType(self, client, callback)
        self.channel2operation[channel] = newOperation
        newOperation.request('Start', *args)


class ClientAccountManager(ClientOperationManager):
    notify = DirectNotifyGlobal.directNotify.newCategory('ClientAccountManager')

    def __init__(self, acceptor):
        ClientOperationManager.__init__(self, acceptor)

        # Create our dbm:
        self.dbm = semidbm.open('databases/accounts', 'c')

    def handleLogin(self, client, callback, playToken, fields=[]):
        # LoginAccountFSM will handle the rest:
        self.runOperation(client, LoginAccountFSM, callback, playToken, fields)
