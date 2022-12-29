from otp.database.MongoDatabase import MongoDatabase


backends = {
    'mongodb': MongoDatabase
}


def createBackend(backendName, backendConfig, generateMin, generateMax):
    backendCtor = backends[backendName]
    return backendCtor.createFromConfig(backendConfig, generateMin, generateMax)
