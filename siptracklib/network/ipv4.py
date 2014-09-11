import socket
import struct

from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import template
from siptracklib import confignode
from siptracklib import permission
from siptracklib import errors

def dotted_quad_to_num(network):
    """Convert a 'dotted quad' string to an unsigned integer.

    '192.168.1.1' -> NUM
    The number is returned in host byte order.
    """
    try:
        return long(struct.unpack('>L',socket.inet_aton(network))[0])
    except socket.error, e:
        raise errors.SiptrackError('%s' % e)

def bitcount_to_num(netmask):
    """Return an unsigned integer with 'netmask' bits set.

    ie. convert a '/24' netmask count to an integer.
    The returned value is in host byte order.
    """
    res = 0L
    for n in range(netmask):
        res |= 1<<31 - n
    return res

def dotted_quad_cidr_to_num(network):
    """Convert the network string a.b.c.d/nn to network, netmask integers.

    Returns a tuple of the form (address-NUM, netmask-NUM) or (None, None)
    on error.
    """
    try:
        network, netmask = network.split('/')
    except ValueError:
        return (None, None)

    try:
        network = dotted_quad_to_num(network)
    except errors.SiptrackError:
        return (None, None)

    try:
        netmask = int(netmask)
    except ValueError:
        return (None, None)
    if netmask < 0 or netmask > 32:
        return (None, None)

    netmask = bitcount_to_num(netmask)
    network = network & netmask

    return (network, netmask)

class Address(object):
    def __init__(self, address, netmask, mask = True, validate = True):
        self.address = address
        self.netmask = netmask
        self._calcAddrData()

        if mask:
            self.address = self.network

        if validate:
            if not self._isValidNetmask(netmask):
                raise ValueError('invalid netmask')

    def clone(self):
        return Address(self.address, self.netmask, mask = False,
                validate = False)

    def _calcAddrData(self):
        self.network = self.address & self.netmask
        self.start = self.network
        self.broadcast = self.network + (0xffffffff - self.netmask)
        self.end = self.broadcast

    def __repr__(self):
        return '<IPV4.Address(%s, %s)>' % (self.address, self.netmask)

    def __str__(self):
        return self.printableCIDR()

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

    def _isValidNetmask(self, netmask):
        foundzero = False
        for n in range(32):
            pos = 31 - n
            val = (netmask >> pos) & 1
            if val == 0:
                foundzero = True
            if val == 1 and foundzero is True:
                return False
        return True

    def inc(self, step = 1):
        addr = self.clone()
        addr.address += step
        addr._calcAddrData()
        return addr

    def dec(self, step = 1):
        addr = self.clone()
        addr.address -= step
        addr._calcAddrData()
        return addr

    def isHigher(self, other):
        if self.address > other.address:
            return True
        return False

    def printableCIDR(self):
        return '%s/%s' % (self.numToDottedQuad(self.address),
                          self.numToBitcount(self.netmask))
    printable = printableCIDR
    transportable = printableCIDR

    def printableNonCIDR(self):
        return '%s %s' % (self.numToDottedQuad(self.address),
                          self.numToDottedQuad(self.netmask))

    def printablePretty(self):
        if self.netmask == 0xffffffff:
            return '%s' % (self.numToDottedQuad(self.address))
        else:
            return '%s/%s' % (self.numToDottedQuad(self.address),
                    self.numToBitcount(self.netmask))

    def numToDottedQuad(self, network):
        """Convert an unsigned integer into a 'dotted quad' string.

        NUM -> '192.168.1.1'
        The number must be given in host byte order.
        """
        return socket.inet_ntoa(struct.pack('>L', network))

    def host(self):
        """Return a string of Address.address/32."""
        return '%s/32' % (self.numToDottedQuad(self.address))

    def strAddress(self):
        return self.numToDottedQuad(self.address)

    def strNetmask(self):
        return self.numToDottedQuad(self.netmask)

    def strNetmaskCIDR(self):
        return str(self.numToBitcount(self.netmask))

    def numToBitcount(self, netmask):
        """Count the number of bits set in a netmask number.
    
        The number must be given in host byte order.
        No validation is done to verify that the given value is a real
        netmask.
        """
        bits = 0
        for n in range(32):
            if ((netmask >> n) & 1) == 1:
                bits += 1
        return bits

class Network(treenodes.BaseNode):
    class_id = 'IP4N'
    class_name = 'ipv4 network'
    class_data_len = 1
    sort_type = 'ipv4 network'

    def __init__(self, parent, address = None):
        """Init.

        address can be eith an address string (nn.nn.nn.nn/mm) or an
        Address object.
        """
        super(Network, self).__init__(parent)
        self.address = address

    def __repr__(self):
        return '<ipv4.Network(%s:%s)>' % (self.oid, self.address)

    def __str__(self):
        return '%s' % (self.address.printablePretty())

    def __lt__(self, other):
        if not (isinstance(other, treenodes.BaseNode) or \
                isinstance(other, UnallocatedNetwork)) or \
                not other.class_name in ['ipv4 network', 'ipv4 network unallocated']:
            return super(Network, self).__lt__(other)
        if self.address.address < other.address.address:
            return True
        return False

    def __eq__(self, other):
        if not (isinstance(other, treenodes.BaseNode) or \
                isinstance(other, UnallocatedNetwork)) or \
                not other.class_name in ['ipv4 network', 'ipv4 network unallocated']:
            return super(Network, self).__eq__(other)
        if self.address.address == other.address.address:
            return True
        return False

    def describe(self):
        return '%s:%s:%s' % (self.class_name, self.oid, self.address)

    def _created(self):
        if self.address is None:
            raise errors.SiptrackError('invalid address in network object')
        self.address = self.addressFromString(self.address)
        # Use self.address.printableCIDR() rather then the (original)
        # self.address string so that /32 is added if necessary.
        self.oid = self.transport.add(self.parent.oid,
                self.address.transportable())

    def _loaded(self, node_data):
        super(Network, self)._loaded(node_data)
        self.address = self.addressFromString(node_data['data'][0])

    def addressFromString(self, address):
        return address_from_string(address)

    def listNetworks(self, include_missing = False):
        if include_missing:
            children = self.listChildren(include = ['ipv4 network'])
            missing = self.findMissingNetworks()
            all = list(children) + list(missing)
            all.sort()
            return iter(all)
        else:
            return self.listChildren(include = ['ipv4 network'])

    def listNetworkRanges(self):
        return self.listChildren(include = ['ipv4 network range'])

    def addNetwork(self, *args, **kwargs):
        return self.add('ipv4 network', *args, **kwargs)

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
        if self.address.netmask == 0xffffffff:
            return True
        return False

    def strAddress(self):
        return self.address.strAddress()

    def strNetmask(self):
        return self.address.strNetmask()

    def strNetmaskCIDR(self):
        return self.address.strNetmaskCIDR()

    def size(self):
        return self.address.end - self.address.start + 1

    def numAllocatedSubnets(self):
        return len(self.listChildren(include = ['ipv4 network']))

    def numAllocatedHosts(self):
        used = 0
        for obj in self.listChildren(include = ['ipv4 network']):
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
    class_id = 'IP4NUNALLOC'
    class_name = 'ipv4 network unallocated'
    unallocated = True
    sort_type = 'ipv4 network'

    def __init__(self, address):
        self.address = address

    def __repr__(self):
        return '<ipv4.UnallocatedNetwork(%s)>' % (self.address)

    def __str__(self):
        return '%s' % (self.address.printablePretty())

    def __lt__(self, other):
        if not (isinstance(other, treenodes.BaseNode) or \
                isinstance(other, UnallocatedNetwork)) or \
                not other.class_name in ['ipv4 network', 'ipv4 network unallocated']:
            return super(UnallocatedNetwork, self).__lt__(other)
        if self.address.address < other.address.address:
            return True
        return False

    def __eq__(self, other):
        if not (isinstance(other, treenodes.BaseNode) or \
                isinstance(other, UnallocatedNetwork)) or \
                not other.class_name in ['ipv4 network', 'ipv4 network unallocated']:
            return super(UnallocatedNetwork, self).__eq__(other)
        if self.address.address == other.address.address:
            return True
        return False

    def describe(self):
        return '%s:%s' % (self.class_name, self.oid, self.address)

    def _created(self):
        pass

    def _loaded(self, node_data):
        pass

    def addressFromString(self, address):
        return address_from_string(address)

    def getNetworkTree(self):
        return self.getParent('network tree')

    def isHost(self):
        if self.address.netmask == 0xffffffff:
            return True
        return False

    def strAddress(self):
        return self.address.strAddress()

    def strNetmask(self):
        return self.address.strNetmask()

    def strNetmaskCIDR(self):
        return self.address.strNetmaskCIDR()

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
        return '%s - %s' % (self.numToDottedQuad(self.start),
                self.numToDottedQuad(self.end))

    def transportable(self):
        return '%s %s' % (self.numToDottedQuad(self.start),
                self.numToDottedQuad(self.end))
    
    def printableStart(self):
        return self.numToDottedQuad(self.start)
    
    def printableEnd(self):
        return self.numToDottedQuad(self.end)
    
    def numToDottedQuad(self, network):
        """Convert an unsigned integer into a 'dotted quad' string.

        NUM -> '192.168.1.1'
        The number must be given in host byte order.
        """
        return socket.inet_ntoa(struct.pack('>L', network))

class NetworkRange(treenodes.BaseNode):
    class_id = 'IP4NR'
    class_name = 'ipv4 network range'
    class_data_len = 1
    sort_type = 'ipv4 network range'

    def __init__(self, parent, range = None):
        """Init.

        address can be eith an address string (nn.nn.nn.nn mm.mm.mm.mm) or a
        Range object.
        """
        super(NetworkRange, self).__init__(parent)
        self.range = range

    def __repr__(self):
        return '<ipv4.NetworkRange(%s:%s)>' % (self.oid, self.range)

    def __str__(self):
        return '%s' % (self.range.printable())

    def __lt__(self, other):
        if not isinstance(other, treenodes.BaseNode) or \
                not other.class_name in ['ipv4 network range']:
            return super(NetworkRange, self).__lt__(other)
        if self.range.start < other.range.start:
            return True
        return False

    def __eq__(self, other):
        if not isinstance(other, treenodes.BaseNode) or \
                not other.class_name in ['ipv4 network range']:
            return super(NetworkRange, self).__eq__(other)
        if self.range == other.range:
            return True
        return False

    def describe(self):
        return '%s:%s:%s' % (self.class_name, self.oid, self.address)

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
        address = address_from_string(addr_string)
        network = UnallocatedNetwork(address)
        yield network

def is_valid_address_string(address):
    try:
        a = address_from_string(address)
    except:
        return False
    return True

def address_from_string(address, mask = True, validate = True):
    """Return an Address object matching an address string.

    The address string must be an ipv4 address in cidr notion, ie.
    nn.nn.nn.nn/mm.

    If an Address object is passed in it is returned untouched.
    """
    if type(address) == Address:
        return address
    # Make sure it's not confused with a range.
    if ' ' in address:
        raise errors.SiptrackError('invalid address string: %s' % address)
    if '/' in address:
        network, netmask = dotted_quad_cidr_to_num(address)
    else:
        network = dotted_quad_to_num(address)
        # 255.255.255.255
        netmask = 4294967295L
    if network is None or netmask is None:
        raise errors.SiptrackError('invalid address string: network/netmask is None')
    return Address(network, netmask, mask, validate)

def is_valid_range_string(range):
    try:
        a = range_from_string(range)
    except:
        return False
    return True

def range_from_string(range):
    """Return a Range object matching an range string.

    The range string must be two ipv4 address, start and end.
    End must be equal to or higher than start

    If a Range object is passed in it is returned untouched.
    """
    if type(range) == Range:
        return range
    split = range.split()
    if len(split) != 2:
        raise errors.SiptrackError('invalid range string')
    start = dotted_quad_to_num(split[0])
    end = dotted_quad_to_num(split[1])
    return Range(start, end)

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
