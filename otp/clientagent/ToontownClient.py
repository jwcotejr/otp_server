from otp.clientagent.Client import Client
from otp.clientagent import ClientMessages
from otp.core.Globals import ClientState
from otp.core import Util


class ToontownClient(Client):

    def handlePreAuth(self, dgi):
        msgType = dgi.getUint16()

        if msgType == ClientMessages.CLIENT_LOGIN_TOONTOWN:
            self.handleClientLoginToontown(dgi)
        else:
            print(msgType)

    def handleClientLoginToontown(self, dgi):
        playToken = dgi.getString()
        serverVersion = dgi.getString()
        hashVal = dgi.getUint32()
        tokenType = dgi.getInt32()
        wantMagicWords = dgi.getString()

        # Check if the client is the expected version:
        if serverVersion != self.acceptor.getServerVersion():
            self.sendDisconnect(125, 'Client version mismatch')
            return

        # Check if the client has the expected DC hash:
        if hashVal != self.acceptor.getDcHash():
            self.sendDisconnect(125, 'DC hash mismatch')
            return

        # Check if the client is sending the expected token type:
        if tokenType != ClientMessages.CLIENT_LOGIN_3_DISL_TOKEN:
            self.sendDisconnect(122, 'Token type mismatch')
            return

        # The account manager will handle the rest:
        self.acceptor.accountManager.handleLogin(
            self,
            self.sendClientLoginToontownResp,
            playToken,
            ['CREATED'])

    def sendClientLoginToontownResp(self, playToken, accountId, fields):
        # Un-sandbox the client:
        self.state = ClientState.ESTABLISHED

        # Set the account ID:
        self.accountId = accountId

        # Get the account connection channel and subscribe to it:
        accountConnectionChannel = Util.GetAccountConnectionChannel(accountId)
        self.subscribeChannel(accountConnectionChannel)

        # Set our channel to the account channel:
        accountChannel = accountId << 32
        self.setChannel(accountChannel)
