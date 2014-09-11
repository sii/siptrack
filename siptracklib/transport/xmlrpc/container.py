from siptracklib.transport.xmlrpc import baserpc

class ContainerRPC(baserpc.BaseRPC):
    command_path = 'container'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

class ContainerTreeRPC(baserpc.BaseRPC):
    command_path = 'container.tree'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

class AttributeRPC(baserpc.BaseRPC):
    command_path = 'container.attribute'

    def add(self, parent_oid, name, atype, value):
        return self.send('add', parent_oid, name, atype, value)

    def setValue(self, oid, value):
        return self.send('set_value', oid, value)

