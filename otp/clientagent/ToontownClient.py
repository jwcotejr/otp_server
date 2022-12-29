from otp.clientagent.Client import Client
from otp.clientagent import ClientMessages


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
