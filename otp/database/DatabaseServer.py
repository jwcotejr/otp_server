from panda3d.direct import DCPacker

from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.directnotify import DirectNotifyGlobal

from otp.net.NetworkConnector import NetworkConnector
from otp.database import DBBackendFactory
from otp.core import MsgTypes


class DatabaseServer(NetworkConnector):
    notify = DirectNotifyGlobal.directNotify.newCategory('DatabaseServer')

    def __init__(self, control, generateMin, generateMax, backendConfig, mdHost, mdPort):
        NetworkConnector.__init__(self, mdHost, mdPort)

        # Control channel that we will subscribe to:
        self.control = control

        # Create our backend:
        backendName = backendConfig['type']
        self.backend = DBBackendFactory.createBackend(backendName, backendConfig, generateMin, generateMax)

        # Handle our DcObjectTypes:
        self.dclassesByObjectType = {}
        self.objectTypesByName = {}
        self.handleDcObjectTypes()

        # Subscribe to our control channel:
        self.subscribeChannel(self.control)

    def handleDcObjectTypes(self):
        dcObjectType = 0

        # Check all base classes in our DC file for the "DcObjectType" field:
        for n in range(dcFile.getNumClasses()):
            dcClass = dcFile.getClass(n)
            for i in range(dcClass.getNumFields()):
                field = dcClass.getField(i)
                if field.getName() == "DcObjectType":
                    # Found one! Increment dcObjectType and add it to our dictionaries:
                    dcObjectType += 1
                    self.dclassesByObjectType[dcObjectType] = dcClass
                    self.objectTypesByName[dcClass.getName()] = dcObjectType

        def isInheritedDcObjectClass(dcClass):
            """
            If a class in our DC file has a parent class, check if the parent
            class is in our DcObjectType dictionaries, and return the result.
            """
            isDcObject = False
            for n in range(dcClass.getNumParents()):
                parent = dcClass.getParent(n)
                isDcObject = parent.getName() in self.objectTypesByName
                if not isDcObject and parent.getNumParents() > 0:
                    # Check the parent of this parent:
                    isDcObject = isInheritedDcObjectClass(parent)

            return isDcObject

        # Now we check for any classes in our DC file that might have
        # inherited from a class that is in our DcObjectType dictionaries:
        for n in range(dcFile.getNumClasses()):
            dcClass = dcFile.getClass(n)
            isDcObject = isInheritedDcObjectClass(dcClass)
            if isDcObject:
                # Found one! Increment dcObjectType and add it to our dictionaries:
                dcObjectType += 1
                self.dclassesByObjectType[dcObjectType] = dcClass
                self.objectTypesByName[dcClass.getName()] = dcObjectType

    def createRoutedDatagram(self, msgType, channels=[]):
        """
        Creates a datagram that will be routed by the Message Director.
        """
        datagram = PyDatagram()
        datagram.addUint8(len(channels))  # Number of channels.

        for channel in channels:
            datagram.addUint64(channel)  # Destination channel.

        datagram.addUint64(self.control)  # Source channel.
        datagram.addUint16(msgType)  # Message type.
        return datagram

    def createHandledDatagram(self, msgType):
        """
        Creates a datagram that will be handled on the Message Director.
        """
        datagram = PyDatagram()
        datagram.addUint8(1)  # One channel.
        datagram.addUint64(MsgTypes.CONTROL_MESSAGE)  # Control message.
        datagram.addUint16(msgType)  # Message type.
        return datagram

    def subscribeChannel(self, channel):
        """
        Subscribes to a channel.
        """
        datagram = self.createHandledDatagram(MsgTypes.CONTROL_SET_CHANNEL)
        datagram.addUint64(channel)  # Channel we are subscribing to.

        # Send the datagram to the message director:
        self.sendUpstream(datagram)

    def handleServerDatagram(self, datagram):
        """
        Handles a datagram from the Message Director.
        """
        dgi = PyDatagramIterator(datagram)

        # Get the source channel:
        channel = dgi.getUint64()

        # Get the message type:
        msgType = dgi.getUint16()

        # Handle the message:
        if msgType == MsgTypes.DBSERVER_CREATE_STORED_OBJECT:
            self.handleCreateStoredObject(dgi, channel)

    def handleCreateStoredObject(self, dgi, channel):
        # Get the context:
        context = dgi.getUint32()

        # This value is unused:
        _ = dgi.getString()

        # Get the object type:
        objectType = dgi.getUint16()

        # Get the number of fields & packed values:
        numValues = dgi.getUint16()

        # Get the DC class from the object type:
        dcClass = self.dclassesByObjectType.get(objectType)
        if not dcClass:
            # This is an invalid object type! Warn the user:
            self.notify.warning('Invalid object type in DBSERVER_CREATE_STORED_OBJECT: %s' % objectType)

            # Send a response message to our sender informing them we have failed here:
            datagram = self.createRoutedDatagram(MsgTypes.DBSERVER_CREATE_STORED_OBJECT_RESP, [channel])
            datagram.addUint32(context)
            datagram.addUint8(1)
            self.sendUpstream(datagram)

            # We're done here:
            return

        # Dictionary for our field/value pairs:
        values = {}

        # Get our field names:
        for _ in range(numValues):
            # Get the string:
            fieldName = dgi.getString()

            # Add it to our values dictionary:
            values[fieldName] = None

        # Get our field values:
        for fieldName in values.keys():
            # Get our DC field:
            dcField = dcClass.getFieldByName(fieldName)
            if not dcField:
                # This is an invalid field name! Warn the user:
                self.notify.warning('Invalid field %s for class %s in DBSERVER_CREATE_STORED_OBJECT!' % (fieldName, dcClass.getName()))

                # Send a response message to our sender informing them we have failed here:
                datagram = self.createRoutedDatagram(MsgTypes.DBSERVER_CREATE_STORED_OBJECT_RESP, [channel])
                datagram.addUint32(context)
                datagram.addUint8(1)
                self.sendUpstream(datagram)

                # We're done here:
                return

            # Unpack the value for this field:
            dcPacker = DCPacker()
            dcPacker.setUnpackData(dgi.getBlob())
            dcPacker.beginUnpack(dcField)
            value = dcField.unpackArgs(dcPacker)
            if not dcPacker.endUnpack():
                # We were unable to unpack this field! Warn the user:
                self.notify.warning('Failed to unpack field: %s' % fieldName)

                # Send a response message to our sender informing them we have failed here:
                datagram = self.createRoutedDatagram(MsgTypes.DBSERVER_CREATE_STORED_OBJECT_RESP, [channel])
                datagram.addUint32(context)
                datagram.addUint8(1)
                self.sendUpstream(datagram)

                # We're done here:
                return

            values[fieldName] = value

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
        backendConfig = serviceConfig['backend']
        mdHost = mdConfig['host']
        mdPort = mdConfig['port']

        # Create our DatabaseServer service:
        DatabaseServer(control, generateMin, generateMax, backendConfig, mdHost, mdPort)
