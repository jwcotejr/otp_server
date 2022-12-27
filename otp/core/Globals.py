from enum import Enum


# The possible states for our connected clients:
ClientState = Enum('ClientState', ['NEW', 'ESTABLISHED'], start=0)
