from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import template
from siptracklib import errors
from siptracklib.network import ipv4
from siptracklib.network import ipv6
from siptracklib import confignode
from siptracklib import permission

valid_protocols = ['ipv4', 'ipv6']

class NetworkTree(treenodes.BaseNode):
    class_id = 'NT'
    class_name = 'network tree'
    class_data_len = 1

    def __init__(self, parent, protocol = None):
        super(NetworkTree, self).__init__(parent)
        self.protocol = protocol

    def _created(self):
        if self.protocol == None:
            raise errors.SiptrackError('invalid protocol in network tree')
        self.oid = self.transport.add(self.parent.oid, self.protocol)

    def _loaded(self, node_data):
        super(NetworkTree, self)._loaded(node_data)
        self.protocol = node_data['data'][0]

    def listNetworks(self, include_missing = False):
        children = self.listChildren(include = ['%s network' % (self.protocol)])
        if include_missing:
            missing = self.findMissingNetworks()
            all = list(children) + list(missing)
            all.sort()
            children = iter(all)
        return children

    def listRanges(self):
        children = self.listChildren(include = ['%s network range' % (self.protocol)])
        return children
    listNetworkRanges = listRanges

    def addNetwork(self, *args, **kwargs):
        return self.add('%s network' % (self.protocol), *args, **kwargs)

    def addRange(self, *args, **kwargs):
        return self.add('%s network range' % (self.protocol), *args, **kwargs)
    addNetworkRange = addRange

    def getNetwork(self, address_string, create_if_missing = True):
        address = self.address(address_string)
        oid = self.transport.networkExists(self.oid, address.transportable())
        if oid is False:
            if create_if_missing:
                return self.addNetwork(address)
            return None
        return self.root.getOID(oid)

    def getRange(self, range_string, create_if_missing = True):
        range = self.range(range_string)
        oid = self.transport.rangeExists(self.oid, range.transportable())
        if oid is False:
            if create_if_missing:
                return self.addRange(range)
            return None
        return self.root.getOID(oid)

    def getNetworkOrRange(self, string, create_if_missing = True):
        if self.isValidAddress(string):
            return self.getNetwork(string, create_if_missing)
        elif self.isValidRange(string):
            return self.getRange(string, create_if_missing)
        else:
            raise errors.SiptrackError('invalid address/range string')

    def address(self, address_string):
        if self.protocol == 'ipv4':
            return ipv4.address_from_string(address_string)
        elif self.protocol == 'ipv6':
            return ipv6.address_from_string(address_string)
        else:
            raise errors.SiptrackError('unknown protocol in network tree')

    def range(self, range_string):
        if self.protocol == 'ipv4':
            return ipv4.range_from_string(range_string)
        elif self.protocol == 'ipv6':
            return ipv6.range_from_string(range_string)
        else:
            raise errors.SiptrackError('unknown protocol in network tree')

    def getNetworkTree(self):
        return self

    def findMissingNetworks(self):
        """Return a list of unallocated subnets of the network tree.
        
        The list consist of UnallocatedNetwork objects.
        """
        missing = self.transport.findMissingNetworks(self.oid)
        if self.protocol == 'ipv4':
            return ipv4.parse_missing_networks_list(missing)
        elif self.protocol == 'ipv6':
            return ipv6.parse_missing_networks_list(missing)
        else:
            raise errors.SiptrackError('unknown protocol in network tree')

    def isValidAddress(self, address):
        if self.protocol == 'ipv4':
            return ipv4.is_valid_address_string(address)
        elif self.protocol == 'ipv6':
            return ipv6.is_valid_address_string(address)
        else:
            raise errors.SiptrackError('unknown protocol in network tree')

    def isValidRange(self, range):
        if self.protocol == 'ipv4':
            return ipv4.is_valid_range_string(range)
        elif self.protocol == 'ipv6':
            return ipv6.is_valid_range_string(range)
        else:
            raise errors.SiptrackError('unknown protocol in network tree')

# Add the objects in this module to the object registry.
o = object_registry.registerClass(NetworkTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(ipv4.Network)
o.registerChild(ipv4.NetworkRange)
o.registerChild(ipv6.Network)
o.registerChild(ipv6.NetworkRange)
o.registerChild(template.NetworkTemplate)
o.registerChild(confignode.ConfigValue)
o.registerChild(permission.Permission)
