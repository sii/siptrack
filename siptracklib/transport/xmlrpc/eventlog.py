from siptracklib.transport.xmlrpc import baserpc

class EventLogTreeRPC(baserpc.BaseRPC):
    command_path = 'event.log.tree'

class EventLogRPC(baserpc.BaseRPC):
    command_path = 'event.log'

