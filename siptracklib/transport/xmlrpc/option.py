from siptracklib.transport.xmlrpc import baserpc

class OptionRPC(baserpc.BaseRPC):
    command_path = 'option'

class OptionTreeRPC(baserpc.BaseRPC):
    command_path = 'option.tree'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

class OptionCategoryRPC(baserpc.BaseRPC):
    command_path = 'option.category'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

class OptionValueRPC(baserpc.BaseRPC):
    command_path = 'option.value'

    def add(self, parent_oid, value):
        return self.send('add', parent_oid, value)

    def set(self, oid, value):
        return self.send('set', oid, value)
