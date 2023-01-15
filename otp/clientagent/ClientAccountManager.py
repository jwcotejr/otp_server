import semidbm


class ClientAccountManager:

    def __init__(self, acceptor):
        self.acceptor = acceptor

        # Create our dbm:
        self.dbm = semidbm.open('databases/accounts', 'c')
