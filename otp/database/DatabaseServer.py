from otp.net.NetworkConnector import NetworkConnector


class DatabaseServer(NetworkConnector):

    def __init__(self, control, generateMin, generateMax, mdHost, mdPort):
        NetworkConnector.__init__(self, mdHost, mdPort)

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
