from siptracklib.transport.xmlrpc import baserpc

class CounterRPC(baserpc.BaseRPC):
    command_path = 'counter'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

    def set(self, oid, value):
        return self.send('set', oid, value)

    def get(self, oid):
        return self.send('get', oid)

    def inc(self, oid):
        return self.send('inc', oid)

class CounterLoopRPC(baserpc.BaseRPC):
    command_path = 'counter.loop'

    def add(self, parent_oid, values):
        return self.send('add', parent_oid, values)

    def set(self, oid, value):
        return self.send('set', oid, value)

    def get(self, oid):
        return self.send('get', oid)

    def inc(self, oid):
        return self.send('inc', oid)

    def setValues(self, oid, values):
        return self.send('set_values', oid, values)
