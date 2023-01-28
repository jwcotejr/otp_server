from panda3d.direct import DCPacker

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator

from otp.core import Globals, MsgTypes


class DatabaseInterface:
    notify = DirectNotifyGlobal.directNotify.newCategory('DatabaseInterface')

    def __init__(self, acceptor):
        self.acceptor = acceptor

        # Our current context:
        self.__contextCounter = 0

        # A dictionary of contexts to callbacks:
        self._callbacks = {}

    def getContext(self):
        """
        Increments our context and returns the value.
        """
        self.__contextCounter = (self.__contextCounter + 1) & 0xFFFFFFFF
        return self.__contextCounter

    def createStoredObject(self, sender, control, objectType, fields={}, callback=None):
        """
        Creates an object of the specified type in the specified database.

        sender specifies the client connection that is sending this request. (Required)
        control specifies the control channel of the target database. (Required)
        objectType specifies the type of object to be created. (Required)
        fields is a dictionary containing any fields we want stored in the object on creation. (Optional)
        callback will be called with callback(doId) if specified. On failure, doId is 0. (Optional)
        """

        # Save the callback:
        context = self.getContext()
        self._callbacks[context] = callback

        # Get the DC class from the object type:
        dcClass = Globals.ServerDCFile.getClassByObjectType(objectType)
        if not dcClass:
            # This is an invalid object type! Throw an error:
            self.notify.error('Invalid object type in createStoredObject: %s' % objectType)

        # Pack up/count valid fields:
        values = {}
        for fieldName, value in fields.items():
            # Get our DC field:
            dcField = dcClass.getFieldByName(fieldName)
            if not dcField:
                # This is an invalid field name! Throw an error:
                self.notify.error('Invalid field %s for class %s in createStoredObject!' % (fieldName, dcClass.getName()))

            fieldPacker = DCPacker()
            fieldPacker.beginPack(dcField)
            dcField.packArgs(fieldPacker, value)
            fieldPacker.endPack()
            values[fieldName] = fieldPacker

        # Now generate and send the datagram:
        datagram = sender.createRoutedDatagram(MsgTypes.DBSERVER_CREATE_STORED_OBJECT, [control])
        datagram.addUint32(context)
        datagram.addString('')
        datagram.addUint16(objectType)
        datagram.addUint16(len(values))
        for field in values.keys():
            datagram.addString(field)

        for value in values.values():
            datagram.addBlob(value.getBytes())

        sender.sendUpstream(datagram)

    def handleCreateStoredObjectResp(self, dgi):
        context = dgi.getUint32()
        retCode = dgi.getUint8()
        if retCode != 0:
            # The database creation has failed! Set our doId to 0:
            doId = 0
        else:
            # The database creation was successful! Get our doId:
            doId = dgi.getUint32()

        if context not in self._callbacks:
            # Got an invalid context! Warn the user:
            self.notify.warning('Got DBSERVER_CREATE_STORED_OBJECT_RESP with invalid context %s' % context)
            return

        # Call our callback, and delete it from our dictionary:
        if self._callbacks[context]:
            self._callbacks[context](doId)

        del self._callbacks[context]

    def getStoredValues(self, sender, control, doId, fieldNames, callback):
        """
        Queries stored object (doId) for stored values from database.
        """

        # Save the callback:
        context = self.getContext()
        self._callbacks[context] = callback

        # We always want to query for DcObjectType, since it is used by
        # handleGetStoredValuesResp to get the DC class for unpacking fields:
        if 'DcObjectType' not in fieldNames:
            fieldNames.append('DcObjectType')

        # Now generate and send the datagram:
        datagram = sender.createRoutedDatagram(MsgTypes.DBSERVER_GET_STORED_VALUES, [control])
        datagram.addUint32(context)
        datagram.addUint32(doId)
        datagram.addUint16(len(fieldNames))
        for fieldName in fieldNames:
            datagram.addString(fieldName)

        sender.sendUpstream(datagram)

    def handleGetStoredValuesResp(self, dgi):
        context = dgi.getUint32()
        doId = dgi.getUint32()
        numFields = dgi.getUint16()

        fieldNames = []
        for _ in range(numFields):
            fieldName = dgi.getString()
            fieldNames.append(fieldName)

        if context not in self._callbacks:
            # Got an invalid context! Warn the user:
            self.notify.warning('Got DBSERVER_GET_STORED_VALUES_RESP with invalid context %s' % context)
            return

        retCode = dgi.getUint8()
        if retCode != 0:
            # The database query has failed! Set dcClass and fields to None:
            dcClass = None
            fields = None
        else:
            # The database query was successful! Get our DC class and fields:
            packedValues = {}
            for fieldName in fieldNames:
                packedValue = dgi.getBlob()
                packedValues[fieldName] = packedValue

            dcClass = None
            packedObjectType = packedValues.get('DcObjectType')
            if packedObjectType:
                objectTypeDg = PyDatagram(packedObjectType)
                objectTypeDgi = PyDatagramIterator(objectTypeDg)
                objectType = objectTypeDgi.getString()
                if not objectType:
                    # We don't have an object type! Throw an error:
                    self.notify.error('Got DBSERVER_GET_STORED_VALUES_RESP for doId %s without a DcObjectType!' % doId)

                dcClass = Globals.ServerDCFile.getClassByName(objectType)
                if not dcClass:
                    # This is an invalid object type! Throw an error:
                    self.notify.error('Invalid object type in handleGetStoredValuesResp: %s' % objectType)
            else:
                # We don't have an object type! Throw an error:
                self.notify.error('Got DBSERVER_GET_STORED_VALUES_RESP for doId %s without a DcObjectType!' % doId)

            fields = {}
            for fieldName, packedValue in packedValues.items():
                found = dgi.getUint8()
                if not found:
                    self.notify.warning('Field %s not found in DBSERVER_GET_STORED_VALUES_RESP' % fieldName)
                    continue

                # Get our DC field:
                dcField = dcClass.getFieldByName(fieldName)
                if not dcField:
                    # This is an invalid field name! Throw an error:
                    self.notify.error('Invalid field %s for class %s in handleGetStoredValuesResp!' % (fieldName, dcClass.getName()))

                # Unpack the value for this field:
                fieldReader = DCPacker()
                fieldReader.setUnpackData(packedValue)
                fieldReader.beginUnpack(dcField)
                value = dcField.unpackArgs(fieldReader)
                if not fieldReader.endUnpack():
                    # We were unable to unpack this field! Throw an error:
                    self.notify.error('Failed to unpack field: %s' % fieldName)

                # Add the unpacked value for this field to our dictionary:
                fields[fieldName] = value

        # Call our callback, and delete it from our dictionary:
        if self._callbacks[context]:
            self._callbacks[context](dcClass, fields)

        del self._callbacks[context]

    def handleServerDatagram(self, msgType, dgi):
        """
        Handles a datagram coming from the Message Director.
        """
        # Handle the message:
        if msgType == MsgTypes.DBSERVER_CREATE_STORED_OBJECT_RESP:
            self.handleCreateStoredObjectResp(dgi)
        elif msgType == MsgTypes.DBSERVER_GET_STORED_VALUES_RESP:
            self.handleGetStoredValuesResp(dgi)
