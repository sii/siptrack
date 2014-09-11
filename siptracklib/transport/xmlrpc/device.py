from siptracklib.transport.xmlrpc import baserpc

class DeviceRPC(baserpc.BaseRPC):
    command_path = 'device'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

    def delete(self, oid, prune_networks):
        return self.send('delete', oid, prune_networks)

    def autoassignNetwork(self, oid):
        return self.send('autoassign_network', oid)

class DeviceTreeRPC(baserpc.BaseRPC):
    command_path = 'device.tree'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

class DeviceCategoryRPC(baserpc.BaseRPC):
    command_path = 'device.category'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

