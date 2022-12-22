from otp.net.NetworkAcceptor import NetworkAcceptor


class ChannelTracker:

    def __init__(self, channelMin, channelMax):
        self.currentChannel = channelMin
        self.maxChannel = channelMax
        self.unusedChannels = []

    def allocateChannel(self):
        # Check if we have any unused channels:
        if len(self.unusedChannels):
            return self.unusedChannels.pop()

        # Increase the current channel:
        self.currentChannel += 1
        return self.currentChannel - 1

    def freeChannel(self, channel):
        # Add the channel to the unused channels list:
        self.unusedChannels.append(channel)


class ClientAgent(NetworkAcceptor):

    def __init__(self, host, port, serverVersion, dcHash, channelMin, channelMax):
        NetworkAcceptor.__init__(self, host, port)

        # Set our server version:
        self.serverVersion = serverVersion

        # Set our DC hash:
        self.dcHash = dcHash or dcFile.getHash()

        # Create our channel tracker:
        self.channelTracker = ChannelTracker(channelMin, channelMax)

    @staticmethod
    def createFromConfig(config):
        # Get our config values:
        host = config['host']
        port = config['port']
        serverVersion = config['server-version']
        dcHash = config.get('dc-hash')
        channelMin = config['channels']['min']
        channelMax = config['channels']['max']

        # Create our ClientAgent service:
        ClientAgent(host, port, serverVersion, dcHash, channelMin, channelMax)
