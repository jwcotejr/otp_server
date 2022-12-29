from otp.net.NetworkConnector import NetworkConnector


class GenerateRange:

    def __init__(self, min, max):
        self.min = min
        self.max = max
        self.current = None

    def getMin(self):
        return self.min

    def getMax(self):
        return self.max

    def setCurrent(self, current):
        self.current = current

    def getCurrent(self):
        return self.current


class DatabaseServer(NetworkConnector):

    def __init__(self, control, generateMin, generateMax, mdHost, mdPort):
        NetworkConnector.__init__(self, mdHost, mdPort)

        # Control channel that we will subscribe to:
        self.control = control

        # Create our generate range:
        self.generateRange = GenerateRange(generateMin, generateMax)

    @staticmethod
    def createFromConfig(serviceConfig):
        # Do we have a Message Director?
        mdConfig = config.get('messagedirector', {})
        if not mdConfig:
            # If we don't have a Message Director, we cannot create a Database Server.
            raise Exception('Cannot create a Database Server without a Message Director!')

        # Get our config values:
        control = serviceConfig['control']
        generateMin = serviceConfig['generate']['min']
        generateMax = serviceConfig['generate']['max']
        mdHost = mdConfig['host']
        mdPort = mdConfig['port']

        # Create our DatabaseServer service:
        DatabaseServer(control, generateMin, generateMax, mdHost, mdPort)
