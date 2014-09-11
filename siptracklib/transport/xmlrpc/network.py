from siptracklib.transport.xmlrpc import baserpc

class NetworkRPC(baserpc.BaseRPC):
    command_path = 'network'

class NetworkRangeRPC(baserpc.BaseRPC):
    command_path = 'network.range'

class NetworkIPV4RPC(baserpc.BaseRPC):
    command_path = 'network.ipv4'

    def add(self, parent_oid, address):
        return self.send('add', parent_oid, address)

    def delete(self, oid, recursive):
        return self.send('delete', oid, recursive)

    def prune(self, oid):
        return self.send('prune', oid)

    def findMissingNetworks(self, oid):
        return self.send('find_missing_networks', oid)

class NetworkRangeIPV4RPC(baserpc.BaseRPC):
    command_path = 'network.range.ipv4'

    def add(self, parent_oid, address):
        return self.send('add', parent_oid, address)

    def prune(self, oid):
        return self.send('prune', oid)

class NetworkIPV6RPC(baserpc.BaseRPC):
    command_path = 'network.ipv6'

    def add(self, parent_oid, address):
        return self.send('add', parent_oid, address)

    def delete(self, oid, recursive):
        return self.send('delete', oid, recursive)

    def prune(self, oid):
        return self.send('prune', oid)

    def findMissingNetworks(self, oid):
        return self.send('find_missing_networks', oid)

class NetworkRangeIPV6RPC(baserpc.BaseRPC):
    command_path = 'network.range.ipv6'

    def add(self, parent_oid, address):
        return self.send('add', parent_oid, address)

    def prune(self, oid):
        return self.send('prune', oid)

class NetworkTreeRPC(baserpc.BaseRPC):
    command_path = 'network.tree'

    def add(self, parent_oid, protocol):
        return self.send('add', parent_oid, protocol)

    def networkExists(self, network_tree_oid, address):
        return self.send('network_exists', network_tree_oid, address)

    def rangeExists(self, network_tree_oid, range):
        return self.send('range_exists', network_tree_oid, range)

    def findMissingNetworks(self, oid):
        return self.send('find_missing_networks', oid)

