from siptracklib.transport.xmlrpc import baserpc

class ConfigRPC(baserpc.BaseRPC):
    command_path = 'config'

class ConfigSectionRPC(baserpc.BaseRPC):
    command_path = 'config.section'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

class ConfigNetworkAutoassignRPC(baserpc.BaseRPC):
    command_path = 'config.network_autoassign'

    def add(self, parent_oid, network_tree_oid, range_start, range_end):
        return self.send('add', parent_oid, network_tree_oid, range_start,
                range_end)

    def setValues(self, oid, network_tree_oid, range_start, range_end):
        return self.send('set_network', oid, network_tree_oid, range_start,
                range_end)

class ConfigValueRPC(baserpc.BaseRPC):
    command_path = 'config.value'

    def add(self, parent_oid, name, value):
        return self.send('add', parent_oid, name, value)

    def setName(self, oid, name):
        return self.send('set_name', oid, name)

    def setValue(self, oid, value):
        return self.send('set_value', oid, value)
