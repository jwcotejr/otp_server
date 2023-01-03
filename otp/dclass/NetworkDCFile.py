from panda3d.direct import DCFile


class NetworkDCFile(DCFile):
    """
    Extends Panda3D's DCFile object to add support for handling DcObjectTypes.
    """

    def __init__(self):
        DCFile.__init__(self)

        # Our DC file names to read:
        self.__dcFileNames = []

        # DcObjectType dictionaries:
        self.__dclassesByObjectType = {}
        self.__objectTypesByName = {}

    def addDcFile(self, dcFileName):
        """
        Adds a DC file name to our list to be read.
        """
        if dcFileName not in self.__dcFileNames:
            self.__dcFileNames.append(dcFileName)

    def readDcFiles(self):
        """
        Reads all DC files in our list into the DCFile object.
        """
        for dcFileName in self.__dcFileNames:
            self.read(dcFileName)

        # Handle our DcObjectTypes:
        self.handleDcObjectTypes()

    def handleDcObjectTypes(self):
        dcObjectType = 0

        # Check all base classes in our DC file for the "DcObjectType" field:
        for n in range(self.getNumClasses()):
            dcClass = self.getClass(n)
            for i in range(dcClass.getNumFields()):
                field = dcClass.getField(i)
                if field.getName() == "DcObjectType":
                    # Found one! Increment dcObjectType and add it to our dictionaries:
                    dcObjectType += 1
                    self.__dclassesByObjectType[dcObjectType] = dcClass
                    self.__objectTypesByName[dcClass.getName()] = dcObjectType

        def isInheritedDcObjectClass(dcClass):
            """
            If a class in our DC file has a parent class, check if the parent
            class is in our DcObjectType dictionaries, and return the result.
            """
            isDcObject = False
            for n in range(dcClass.getNumParents()):
                parent = dcClass.getParent(n)
                isDcObject = parent.getName() in self.__objectTypesByName
                if not isDcObject and parent.getNumParents() > 0:
                    # Check the parent of this parent:
                    isDcObject = isInheritedDcObjectClass(parent)

            return isDcObject

        # Now we check for any classes in our DC file that might have
        # inherited from a class that is in our DcObjectType dictionaries:
        for n in range(self.getNumClasses()):
            dcClass = self.getClass(n)
            isDcObject = isInheritedDcObjectClass(dcClass)
            if isDcObject:
                # Found one! Increment dcObjectType and add it to our dictionaries:
                dcObjectType += 1
                self.__dclassesByObjectType[dcObjectType] = dcClass
                self.__objectTypesByName[dcClass.getName()] = dcObjectType
