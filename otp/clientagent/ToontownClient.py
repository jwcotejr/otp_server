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
        print('handleClientLoginToontown')
