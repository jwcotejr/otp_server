# Sent by the server when it is dropping the connection deliberately.
CLIENT_GO_GET_LOST = 4

# new toontown specific login message, adds last logged in, and if child account has parent acount
CLIENT_LOGIN_TOONTOWN = 125

# The following is a different set of numbers from above.
# These are the sub-message types for CLIENT_LOGIN_2.
CLIENT_LOGIN_3_DISL_TOKEN = 4  # SSL encoded blob from DISL system.
