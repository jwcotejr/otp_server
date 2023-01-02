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

        # Check if we need to create our initial entries in the database:
        otpGlobals = self.mongodb.otp.globals.find_one({'_id': 'doid'})
        if otpGlobals is None:
            # We need to create our initial entry:
            self.mongodb.otp.globals.insert_one({
                '_id': 'doid',
                'seq': self.getMinId()
            })

    def assignDoId(self):
        obj = self.mongodb.otp.globals.find_one_and_update(
            {'_id': 'doid'},  # Filter.
            {'$inc': {'seq': 1}},  # Update.
            {'returnOriginal': False}  # Options.
        )

        doId = obj.get('seq')
        return doId

    def handleCreate(self, dcClass, fields):
        doId = self.assignDoId()
        self.mongodb.otp.objects.insert_one({
            '_id': doId,
            'dclass': dcClass.getName(),
            'fields': fields
        })
        return doId

    @staticmethod
    def createFromConfig(backendConfig, generateMin, generateMax):
        # Get our config values:
        server = backendConfig['server']

        # Create our MongoDatabase backend:
        return MongoDatabase(server, generateMin, generateMax)
