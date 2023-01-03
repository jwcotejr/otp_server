from panda3d.direct import DCPacker

from direct.directnotify import DirectNotifyGlobal

from otp.core import MsgTypes


class DatabaseInterface:
    notify = DirectNotifyGlobal.directNotify.newCategory('DatabaseInterface')

    def __init__(self, client):
        self.client = client

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

    def createObject(self, control, objectType, fields={}, callback=None):
        """
        Creates an object of the specified type in the specified database.

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
            self.notify.error('Invalid object type in createObject: %s' % objectType)

        # Pack up/count valid fields:
        values = {}
        for fieldName, value in fields.items():
            # Get our DC field:
            dcField = dcClass.getFieldByName(fieldName)
            if not dcField:
                # This is an invalid field name! Throw an error:
                self.notify.error('Invalid field %s for class %s in createObject!' % (fieldName, dcClass.getName()))

            fieldPacker = DCPacker()
            fieldPacker.beginPack(dcField)
            dcField.packArgs(fieldPacker, value)
            fieldPacker.endPack()
            values[fieldName] = fieldPacker

        # Now generate and send the datagram:
        datagram = self.client.createRoutedDatagram(MsgTypes.DBSERVER_CREATE_STORED_OBJECT, [control])
        datagram.addUint32(context)
        datagram.addString('')
        datagram.addUint16(objectType)
        datagram.addUint16(len(values))
        for field in values.keys():
            datagram.addString(field)

        for value in values.values():
            datagram.addBlob(value.getBytes())

        self.client.sendUpstream(datagram)
