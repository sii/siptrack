class BaseRPC(object):
    def __init__(self, transport):
        self.transport = transport

    def send(self, command, *args):
        if self.command_path:
            command = '%s.%s' % (self.command_path, command)
        return self.transport._sendCommand(command, self.transport.session_id,
                *args)

    def sendNoSID(self, command, *args):
        if self.command_path:
            command = '%s.%s' % (self.command_path, command)
        return self.transport._sendCommand(command, *args)

    def add(self, parent_oid, *args, **kwargs):
        return self.send('add', parent_oid, *args, **kwargs)

    def delete(self, oid):
        return self.send('delete', oid)

