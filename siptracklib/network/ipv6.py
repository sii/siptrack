import socket
import struct

from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import template
from siptracklib import confignode
from siptracklib import permission
from siptracklib import errors
from siptracklib.external import ipaddr

class Network(treenodes.BaseNode):
    class_id = 'IP6N'
    class_name = 'ipv6 network'
    class_data_len = 1
    sort_type = 'ipv6 network'

    def __init__(self, parent, address = None):
        """Init.

        address can be eith an address string (nn.nn.nn.nn/mm) or an
        Address object.
        """
        super(Network, self).__init__(parent)
        self.address = address

    def __repr__(self):
        return '<ipv6.Network(oid(%s):%s)>' % (self.oid, self.address)

    def __str__(self):
        return '%s' % (str(self.address))

    def __lt__(self, other):
        if not (isinstance(other, treenodes.BaseNode) or \
                isinstance(other, UnallocatedNetwork)) or \
                not other.class_name in ['ipv6 network', 'ipv6 network unallocated']:
            return super(Network, self).__lt__(other)
        if self.address < other.address:
            return True
        return False

    def __eq__(self, other):
        if not (isinstance(other, treenodes.BaseNode) or \
                isinstance(other, UnallocatedNetwork)) or \
                not other.class_name in ['ipv6 network', 'ipv6 network unallocated']:
            return super(Network, self).__eq__(other)
        if self.address == other.address:
            return True
        return False

    def describe(self):
        return '%s:%s:%s' % (self.class_name, self.oid, self.address)

    def _created(self):
        if self.address is None:
            raise errors.SiptrackError('invalid address in network object')
        self.address = ipaddr.IPNetwork(self.address, version=6, mask_address=True)
        # Use self.address.printableCIDR() rather then the (original)
        # self.address string so that /32 is added if necessary.
        self.oid = self.transport.add(self.parent.oid,
                str(self.address))

    def _loaded(self, node_data):
        super(Network, self)._loaded(node_data)
        self.address = ipaddr.IPNetwork(node_data['data'][0], version=6)

    def addressFromString(self, address):
        return ipaddr.IPNetwork(address, version=6)

    def listNetworks(self, include_missing = False):
        if include_missing:
            children = self.listChildren(include = ['ipv6 network'])
            missing = self.findMissingNetworks()
            all = list(children) + list(missing)
            all.sort()
            return iter(all)
        else:
            return self.listChildren(include = ['ipv6 network'])

    def listNetworkRanges(self):
        return self.listChildren(include = ['ipv6 network range'])

    def addNetwork(self, *args, **kwargs):
        return self.add('ipv6 network', *args, **kwargs)

    def listDevices(self):
        """List referenced devices."""
        for node in self.listLinks(include = ['device']):
            yield node

    def getNetworkTree(self):
        return self.getParent('network tree')

    def delete(self, recursive):
        self.transport.delete(self.oid, recursive)
        self._purge()

    def isHost(self):
        if self.address.first == self.address.last:
            return True
        return False

    def strAddress(self):
        return str(self.address.first)

    def strNetmask(self):
        return str(self.address.netmask)

    def strNetmaskCIDR(self):
        return self.address.prefixlen

    def size(self):
        return self.address.numhosts

    def numAllocatedSubnets(self):
        return len(self.listChildren(include = ['ipv6 network']))

    def numAllocatedHosts(self):
        used = 0
        for obj in self.listChildren(include = ['ipv6 network']):
            used += obj.size()
        return used

    def numFreeHosts(self):
        return self.size() - self.numAllocatedHosts()

    def prune(self):
        """Deletes the network if it has no associations.

        Useful to call if a network has been disassociated from a device
        and it should be removed if no device is still using it.
        """
        if self.transport.prune(self.oid):
            self._purge()

    def findMissingNetworks(self):
        """Return a list of unallocated subnets of the current network.
        
        The list consist of UnallocatedNetwork objects.
        """
        missing = self.transport.findMissingNetworks(self.oid)
        return parse_missing_networks_list(missing)

class UnallocatedNetwork(object):
    class_id = 'IP6NUNALLOC'
    class_name = 'ipv6 network unallocated'
    unallocated = True
    sort_type = 'ipv6 network'

    def __init__(self, address):
        self.address = address

    def __repr__(self):
        return '<ipv6.UnallocatedNetwork(%s)>' % (str(self.address))

    def __str__(self):
        return '%s' % (str(self.address))

    def __lt__(self, other):
        if not (isinstance(other, treenodes.BaseNode) or \
                isinstance(other, UnallocatedNetwork)) or \
                not other.class_name in ['ipv6 network', 'ipv6 network unallocated']:
            return super(UnallocatedNetwork, self).__lt__(other)
        if self.address < other.address:
            return True
        return False

    def __eq__(self, other):
        if not (isinstance(other, treenodes.BaseNode) or \
                isinstance(other, UnallocatedNetwork)) or \
                not other.class_name in ['ipv6 network', 'ipv6 network unallocated']:
            return super(UnallocatedNetwork, self).__eq__(other)
        if self.address == other.address:
            return True
        return False

    def describe(self):
        return '%s:%s:%s' % (self.class_name, self.oid, self.address)

    def _created(self):
        pass

    def _loaded(self, node_data):
        pass

    def addressFromString(self, address):
        return address_from_string(address)

    def getNetworkTree(self):
        return self.getParent('network tree')

    def isHost(self):
        if self.address.first == self.address.last:
            return True
        return False

    def strAddress(self):
        return str(self.address)

    def strNetmask(self):
        return str(self.address.netmask)

    def strNetmaskCIDR(self):
        return self.address.prefixlen

class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def clone(self):
        return Range(self.start, self.end)

    def __repr__(self):
        return '<IPV4.Range(%s, %s)>' % (self.start, self.end)

    def __str__(self):
        return self.printable()

    def __lt__(self, other):
        """True if the current address is a subnet of 'other'."""
        if self.start >= other.start and self.end <= other.end:
            if self.start > other.start or self.end < other.end:
                return True
        return False

    def __le__(self, other):
        """True if the current address is a subnet of, or equal to, 'other'."""
        if self.start >= other.start and self.end <= other.end:
            return True
        return False

    def __eq__(self, other):
        """True if the addresses are identical."""
        if self.start == other.start and self.end == other.end:
            return True
        return False
    
    def __ne__(self, other):
        """True if the address are not identical."""
        if self.start != other.start or self.end != other.end:
            return True
        return False
    
    def __gt__(self, other):
        """True if the current address is a supernet of 'other'."""
        if other.start >= self.start and other.end <= self.end:
            if other.start > self.start or other.end < self.end:
                return True
        return False
    
    def __ge__(self, other):
        """True if the current address is a supernet of, or equal to, 'other'."""
        if other.start >= self.start and other.end <= self.end:
            return True
        return False

    def printable(self):
        return '%s - %s' % (str(self.start), str(self.end))

    def transportable(self):
        return '%s %s' % (str(self.start), str(self.end))
    
    def printableStart(self):
        return str(self.start)
    
    def printableEnd(self):
        return str(self.end)
    
class NetworkRange(treenodes.BaseNode):
    class_id = 'IP6NR'
    class_name = 'ipv6 network range'
    class_data_len = 1
    sort_type = 'ipv6 network range'

    def __init__(self, parent, range = None):
        """Init.

        address can be eith an address string (nn.nn.nn.nn mm.mm.mm.mm) or a
        Range object.
        """
        super(NetworkRange, self).__init__(parent)
        self.range = range

    def __repr__(self):
        return '<ipv6.NetworkRange(%s:%s)>' % (self.oid, self.range)

    def __str__(self):
        return '%s' % (self.range.printable())

    def __lt__(self, other):
        if not isinstance(other, treenodes.BaseNode) or \
                not other.class_name in ['ipv6 network range']:
            return super(NetworkRange, self).__lt__(other)
        if self.range.start < other.range.start:
            return True
        return False

    def __eq__(self, other):
        if not isinstance(other, treenodes.BaseNode) or \
                not other.class_name in ['ipv6 network range']:
            return super(NetworkRange, self).__eq__(other)
        if self.range == other.range:
            return True
        return False

    def describe(self):
        return '%s:%s:%s' % (self.class_name, self.oid, self.range)

    def _created(self):
        if self.range is None:
            raise errors.SiptrackError('invalid range in network range object')
        self.range = self.rangeFromString(self.range)
        self.oid = self.transport.add(self.parent.oid,
                self.range.transportable())

    def _loaded(self, node_data):
        super(NetworkRange, self)._loaded(node_data)
        self.address = self.rangeFromString(node_data['data'][0])

    def rangeFromString(self, range):
        return range_from_string(range)

    def getNetworkTree(self):
        return self.getParent('network tree')

    def delete(self):
        self.transport.delete(self.oid)
        self._purge()

    def strStart(self):
        return self.range.printableStart()

    def strEnd(self):
        return self.range.printableEnd()

    def prune(self):
        if self.transport.prune(self.oid):
            self._purge()

    def isHost(self):
        return False

    def listDevices(self):
        """List referenced devices."""
        for node in self.references:
            if node.class_name == 'device':
                yield node

    # We keep an address so comparissons etc. to Network objects
    # don't break.
    def _get_address(self):
        return self.range

    def _set_address(self, val):
        self.range = val
    address = property(_get_address, _set_address)

def parse_missing_networks_list(missing):
    for addr_string in missing:
        address = ipaddr.IPNetwork(addr_string, version=6)
        network = UnallocatedNetwork(address)
        yield network

def is_valid_address_string(address):
    try:
        a = ipaddr.IPNetwork(address, version=6)
    except:
        return False
    return True

def address_from_string(address, mask = True, validate = True):
    """Return an Address object matching an address string.

    The address string must be an ipv6 address in cidr notion, ie.
    nn.nn.nn.nn/mm.

    If an Address object is passed in it is returned untouched.
    """
    return ipaddr.IPNetwork(address)

def is_valid_range_string(range):
    try:
        a = range_from_string(range)
    except:
        return False
    return True

def range_from_string(range):
    """Return a Range object matching an range string.

    The range string must be two ipv6 address, start and end.
    End must be equal to or higher than start

    If a Range object is passed in it is returned untouched.
    """
    if type(range) not in [str, unicode]:
        return range
    split = range.split()
    if len(split) != 2:
        raise errors.SiptrackError('invalid range string')
    return Range(split[0], split[1])

# Add the objects in this module to the object registry.
o = object_registry.registerClass(Network)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(Network)
o.registerChild(NetworkRange)
o.registerChild(template.NetworkTemplate)
o.registerChild(confignode.ConfigValue)
o.registerChild(permission.Permission)

o = object_registry.registerClass(NetworkRange)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(confignode.ConfigValue)
o.registerChild(permission.Permission)
