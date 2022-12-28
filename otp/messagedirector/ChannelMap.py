class ChannelMap:

    def __init__(self):
        self.channels = {}

    def subscribe(self, participant, channel):
        # Check if we need to make some entries in our dictionary:
        if channel not in self.channels:
            self.channels[channel] = [participant]
            return

        # Add the participant to the list:
        self.channels[channel].append(participant)

    def unsubscribe(self, participant, channel):
        # Remove the participant from the list:
        self.channels[channel].remove(participant)

    def getParticipantsFromChannel(self, channel):
        # Check if we have an entry for the channel:
        if channel not in self.channels:
            return []

        # Return the list of participants:
        return self.channels[channel]
