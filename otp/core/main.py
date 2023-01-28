from direct.task.TaskManagerGlobal import taskMgr

from otp.config.Config import Config
from otp.core import Globals, ServiceFactory
from otp.dclass.NetworkDCFile import NetworkDCFile
from otp.messagedirector.MessageDirector import MessageDirector


# Load our config:
# TODO: Allow this to be specified via an argument?
Globals.ServerConfig = Config('config/config.json')

# Create our global DC file:
Globals.ServerDCFile = NetworkDCFile()

# Add our DC files specified in the config into the global DC file:
for path in Globals.ServerConfig.get('general', {}).get('dc-files', []):
    Globals.ServerDCFile.addDcFile(path)

# Read our DC files:
Globals.ServerDCFile.readDcFiles()

# If the Message Director is defined in the config, create it first:
mdConfig = Globals.ServerConfig.get('messagedirector', {})
if mdConfig:
    mdHost = mdConfig['host']
    mdPort = mdConfig['port']
    MessageDirector(mdHost, mdPort)

# Now, create all of our services:
for serviceConfig in Globals.ServerConfig.get('services', []):
    serviceName = serviceConfig['type']
    ServiceFactory.createService(serviceName, serviceConfig)

# We're good to go. Let's start the task manager:
taskMgr.run()
