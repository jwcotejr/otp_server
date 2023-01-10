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

        # Subscribe to our control channel:
        self.subscribeChannel(self.control)

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
        elif msgType == MsgTypes.DBSERVER_GET_STORED_VALUES:
            self.handleGetStoredValues(dgi, channel)

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
        dcClass = dcFile.getClassByObjectType(objectType)
        if not dcClass:
            # This is an invalid object type! Warn the user:
            self.notify.warning('Invalid object type in DBSERVER_CREATE_STORED_OBJECT: %s' % objectType)

            # Send a response message to our sender informing them we have failed here:
            self.sendCreateStoredObjectResp(channel, context, False)

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
                self.sendCreateStoredObjectResp(channel, context, False)

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
                self.sendCreateStoredObjectResp(channel, context, False)

                # We're done here:
                return

            # Add the unpacked value for this field to our dictionary:
            values[fieldName] = value

        # Iterate through this DC class's inherited fields:
        for n in range(dcClass.getNumInheritedFields()):
            # Get the inherited field:
            dcField = dcClass.getInheritedField(n)

            # If this DC field is already in our values dictionary, we can skip over it:
            if dcField.getName() in values.keys():
                continue

            # Skip the field if it is molecular:
            if dcField.asMolecularField() is not None:
                continue

            # We should not be expecting a non-db field:
            if not dcField.isDb():
                # Warn the user:
                self.notify.warning('Non-DB field in DBSERVER_CREATE_STORED_OBJECT: %s' % dcField.getName())

                # Send a response message to our sender informing them we have failed here:
                self.sendCreateStoredObjectResp(channel, context, False)

                # We're done here:
                return

            # If the field is "DcObjectType", set its value to the name of the DC class:
            if dcField.getName() == "DcObjectType":
                values[dcField.getName()] = dcClass.getName()
                continue

            # Check if the field is required:
            if not dcField.isRequired():
                continue

            # Skip the field if it doesn't have a default value:
            if not dcField.hasDefaultValue():
                # Warn the user:
                self.notify.warning('No default value for field %s in DBSERVER_CREATE_STORED_OBJECT!' % dcField.getName())
                continue

            # Get the default value of the field:
            dcPacker = DCPacker()
            dcPacker.setUnpackData(dcField.getDefaultValue())
            dcPacker.beginUnpack(dcField)
            value = dcField.unpackArgs(dcPacker)
            if not dcPacker.endUnpack():
                # We were unable to unpack the default value for this field! Warn the user:
                self.notify.warning('Failed to unpack default value for field: %s' % dcField.getName())

                # Send a response message to our sender informing them we have failed here:
                self.sendCreateStoredObjectResp(channel, context, False)

                # We're done here:
                return

            # Add the unpacked default value of the field to our dictionary:
            values[dcField.getName()] = value

        # Create the object in our database, and get the resulting doId:
        doId = self.backend.handleCreate(dcClass, values)

        # Send a response message to our sender informing them the operation has succeeded:
        self.sendCreateStoredObjectResp(channel, context, True, doId)

    def sendCreateStoredObjectResp(self, channel, context, success, doId=0):
        # Create our response datagram:
        datagram = self.createRoutedDatagram(MsgTypes.DBSERVER_CREATE_STORED_OBJECT_RESP, [channel])

        # Add our context:
        datagram.addUint32(context)

        # If this operation was successful, we send a return code of 0.
        # Otherwise, we send a return code of 1:
        datagram.addUint8(0 if success else 1)

        # If this operation was successful, we also send the doId of the created object:
        if success:
            datagram.addUint32(doId)

        # Send the datagram to the Message Director:
        self.sendUpstream(datagram)

    def handleGetStoredValues(self, dgi, channel):
        # Get the context:
        context = dgi.getUint32()

        # Get the doId of the object:
        doId = dgi.getUint32()

        # Get the number of fields:
        numFields = dgi.getUint16()

        # Get the field names:
        fieldNames = []
        for _ in range(numFields):
            fieldName = dgi.getString()
            fieldNames.append(fieldName)

        # Get the object from the database:
        obj = self.backend.handleGet(doId)
        if not obj:
            # No object with this doId exists in the database! Warn the user:
            self.notify.warning('Got DBSERVER_GET_STORED_VALUES for nonexistent object with doId %s' % doId)

            # Send a response message to our sender informing them we have failed here:
            self.sendGetStoredValuesResp(channel, context, doId, numFields, fieldNames, False)

            # We're done here:
            return

        # Get the DC class from the object:
        className = obj.get('dclass')
        if not className:
            # The database entry for this object does not define a dclass name! Warn the user:
            self.notify.warning('Got DBSERVER_GET_STORED_VALUES for doId %s that does not define a class name!' % doId)

            # Send a response message to our sender informing them we have failed here:
            self.sendGetStoredValuesResp(channel, context, doId, numFields, fieldNames, False)

            # We're done here:
            return

        dcClass = dcFile.getClassByName(className)
        if not dcClass:
            # Unable to find a matching DC class with this name! Perhaps it doesn't
            # exist in our DC file, or the database entry is invalid? Warn the user:
            self.notify.warning('Got DBSERVER_GET_STORED_VALUES for doId %s with invalid class name %s' % (
                doId, className))

            # Send a response message to our sender informing them we have failed here:
            self.sendGetStoredValuesResp(channel, context, doId, numFields, fieldNames, False)

            # We're done here:
            return

        # Lists for the field values, and whether they were found in the database or not:
        values = []
        found = []

        # Get the field values:
        fields = obj.get('fields', {})
        for fieldName in fieldNames:
            # Get our DC field:
            dcField = dcClass.getFieldByName(fieldName)
            if not dcField:
                # This is an invalid field name! Warn the user:
                self.notify.warning('Invalid field %s for class %s in DBSERVER_GET_STORED_VALUES!' % (
                    fieldName, dcClass.getName()))

                # Send a response message to our sender informing them we have failed here:
                self.sendGetStoredValuesResp(channel, context, doId, numFields, fieldNames, False)

                # We're done here:
                return

            # Pack the value if it exists:
            value = fields.get(fieldName)
            if value:
                fieldPacker = DCPacker()
                fieldPacker.beginPack(dcField)
                dcField.packArgs(fieldPacker, value)
                if not fieldPacker.endPack():
                    # We were unable to pack this field! Warn the user:
                    self.notify.warning('Failed to pack value %s for field %s in DBSERVER_GET_STORED_VALUES!' % (
                        value, dcField.getName()))

                    # Send a response message to our sender informing them we have failed here:
                    self.sendGetStoredValuesResp(channel, context, doId, numFields, fieldNames, False)

                    # We're done here:
                    return

                values.append(fieldPacker.getBytes())
                found.append(1)
            else:
                values.append(b'')
                found.append(0)

        # Send a response message to our sender informing them the operation has succeeded:
        self.sendGetStoredValuesResp(channel, context, doId, numFields, fieldNames, True, values, found)

    def sendGetStoredValuesResp(self, channel, context, doId, numFields, fieldNames, success, values=[], found=[]):
        # Create our response datagram:
        datagram = self.createRoutedDatagram(MsgTypes.DBSERVER_GET_STORED_VALUES_RESP, [channel])

        # Add our context:
        datagram.addUint32(context)

        # Add the doId of the object we ran this query on:
        datagram.addUint32(doId)

        # Add the number of fields we were querying for:
        datagram.addUint16(numFields)

        # Add all of our field names:
        for i in range(numFields):
            fieldName = fieldNames[i]
            datagram.addString(fieldName)

        # If this operation was successful, we send a return code of 0.
        # Otherwise, we send a return code of 1:
        datagram.addUint8(0 if success else 1)

        # We only need to add the following if this query was successful:
        if success:
            # Add our field values:
            for i in range(numFields):
                value = values[i]
                datagram.addBlob(value)

            # Add our found values:
            for i in range(numFields):
                foundValue = found[i]
                datagram.addUint8(foundValue)

        # Send the datagram to the Message Director:
        self.sendUpstream(datagram)

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
