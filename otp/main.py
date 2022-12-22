from panda3d.direct import DCFile

from direct.task.TaskManagerGlobal import taskMgr

from otp.config.Config import Config
from otp.messagedirector.MessageDirector import MessageDirector
from otp.core import ServiceFactory

import builtins


# Create our global task manager:
builtins.taskMgr = taskMgr

# Load our config:
# TODO: Allow this to be specified via an argument?
builtins.config = Config('config/config.json')

# Create our global DC file:
builtins.dcFile = DCFile()

# Now, read our DC files specified in the config into the global DC file:
for path in config.get('general', {}).get('dc-files', []):
    dcFile.read(path)

# If the Message Director is defined in the config, create it first:
mdConfig = config.get('messagedirector', {})
if mdConfig:
    mdHost = mdConfig['host']
    mdPort = mdConfig['port']
    MessageDirector(mdHost, mdPort)

# Now, create all of our services:
for serviceConfig in config.get('services', []):
    serviceName = serviceConfig['type']
    ServiceFactory.createService(serviceName, serviceConfig)

# We're good to go. Let's start the task manager:
taskMgr.run()
