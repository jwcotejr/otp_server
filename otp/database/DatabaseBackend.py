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


class DatabaseBackend:

    def __init__(self, generateMin, generateMax):
        # Create our generate range:
        self.generateRange = GenerateRange(generateMin, generateMax)
