from otp.database.DatabaseBackend import DatabaseBackend


class MongoDatabase(DatabaseBackend):

    def __init__(self, server, generateMin, generateMax):
        DatabaseBackend.__init__(self, generateMin, generateMax)

    @staticmethod
    def createFromConfig(backendConfig, generateMin, generateMax):
        # Get our config values:
        server = backendConfig['server']

        # Create our MongoDatabase backend:
        return MongoDatabase(server, generateMin, generateMax)
