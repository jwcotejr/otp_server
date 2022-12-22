from panda3d.direct import DCFile

from direct.task.TaskManagerGlobal import taskMgr

from otp.config.Config import Config

import builtins


# Create our global task manager:
builtins.taskMgr = taskMgr

# Load our config:
# TODO: Allow this to be specified via an argument?
builtins.config = Config('config/config.json')

# Create our global DC file:
builtins.dcFile = DCFile()

# Now, read our DC files specified in the config into the global DC file:
for path in config.get('dc-files', []):
    dcFile.read(path)

# We're good to go. Let's start the task manager:
taskMgr.run()
