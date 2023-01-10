from panda3d.direct import DCPacker

from direct.directnotify import DirectNotifyGlobal

from otp.core import MsgTypes


class DatabaseInterface:
    notify = DirectNotifyGlobal.directNotify.newCategory('DatabaseInterface')

    def __init__(self, acceptor):
        self.acceptor = acceptor

        # Our current context:
        self.__contextCounter = 0

        # A dictionary of contexts to callbacks:
        self._callbacks = {}
        self._dclasses = {}

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
        dcClass = dcFile.getClassByObjectType(objectType)
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

    def getStoredValues(self, sender, control, doId, objectType, fieldNames, callback):
        """
        Queries stored object (doId) for stored values from database.
        """

        # Save the callback:
        context = self.getContext()
        self._callbacks[context] = callback

        # Get the DC class from the object type:
        dcClass = dcFile.getClassByObjectType(objectType)
        if not dcClass:
            # This is an invalid object type! Throw an error:
            self.notify.error('Invalid object type in getStoredValues: %s' % objectType)

        # Save the DC class:
        self._dclasses[context] = dcClass

        # Now generate and send the datagram:
        datagram = sender.createRoutedDatagram(MsgTypes.DBSERVER_GET_STORED_VALUES, [control])
        datagram.addUint32(context)
        datagram.addUint32(doId)
        datagram.addUint16(len(fieldNames))
        for fieldName in fieldNames:
            datagram.addString(fieldName)

        sender.sendUpstream(datagram)

    def handleServerDatagram(self, msgType, dgi):
        """
        Handles a datagram coming from the Message Director.
        """
        # Handle the message:
        if msgType == MsgTypes.DBSERVER_CREATE_STORED_OBJECT_RESP:
            self.handleCreateStoredObjectResp(dgi)
