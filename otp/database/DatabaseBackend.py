class DatabaseBackend:

    def __init__(self, generateMin, generateMax):
        # Our minimum and maximum database object IDs:
        self.generateMin = generateMin
        self.generateMax = generateMax

    def getMinId(self):
        """
        Returns the minimum database object ID.
        """
        return self.generateMin

    def getMaxId(self):
        """
        Returns the maximum database object ID.
        """
        return self.generateMax
