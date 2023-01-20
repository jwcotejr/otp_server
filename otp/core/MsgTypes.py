CHANNEL_CLIENT_BROADCAST = 4014

# Control Transactions
CONTROL_MESSAGE = 4001
CONTROL_SET_CHANNEL = 2001
CONTROL_REMOVE_CHANNEL = 2002

# direct-to-database-server transactions
DBSERVER_CREATE_STORED_OBJECT = 1003
DBSERVER_CREATE_STORED_OBJECT_RESP = 1004

DBSERVER_GET_STORED_VALUES = 1012
DBSERVER_GET_STORED_VALUES_RESP = 1013

# The ID number of the database server.  The above direct-to-dbserver
# transactions are sent to this ID.
DBSERVER_ID = 4003

DBSERVER_ACCOUNT_OBJECT_TYPE = 1
