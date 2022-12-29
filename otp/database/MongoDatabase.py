from otp.database.DatabaseBackend import DatabaseBackend

from pymongo import MongoClient, uri_parser


class MongoDatabase(DatabaseBackend):

    def __init__(self, server, generateMin, generateMax):
        DatabaseBackend.__init__(self, generateMin, generateMax)

        # Get our database from the URI:
        database = uri_parser.parse_uri(server)['database']

        # Create our Mongo Client:
        self.mongoClient = MongoClient(server)

        # Get our MongoDB:
        self.mongodb = self.mongoClient[database]

    @staticmethod
    def createFromConfig(backendConfig, generateMin, generateMax):
        # Get our config values:
        server = backendConfig['server']

        # Create our MongoDatabase backend:
        return MongoDatabase(server, generateMin, generateMax)
