from siptracklib.transport.xmlrpc import baserpc

class CommandQueueRPC(baserpc.BaseRPC):
    command_path = 'command.queue'

class CommandRPC(baserpc.BaseRPC):
    command_path = 'command'

    def setFreetext(self, oid, value):
        return self.send('set_freetext', oid, value)

class EventRPC(baserpc.BaseRPC):
    command_path = 'event'

class EventTriggerRPC(baserpc.BaseRPC):
    command_path = 'event.trigger'

class EventTriggerRuleRPC(baserpc.BaseRPC):
    command_path = 'event.trigger.rule'

class EventTriggerRulePythonRPC(baserpc.BaseRPC):
    command_path = 'event.trigger.rule.python'

    def setCode(self, oid, value):
        return self.send('set_code', oid, value)

