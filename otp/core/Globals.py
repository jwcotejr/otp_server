from otp.config.Config import Config
from otp.dclass.NetworkDCFile import NetworkDCFile

from enum import Enum


# The global config:
ServerConfig: Config

# The global DC file:
ServerDCFile: NetworkDCFile

# The possible states for our connected clients:
ClientState: Enum = Enum('ClientState', ['NEW', 'ESTABLISHED'], start=0)
