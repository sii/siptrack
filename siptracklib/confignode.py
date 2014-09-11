from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import permission

class ConfigNetworkAutoassign(treenodes.BaseNode):
    class_id = 'CFGNETAUTO'
    class_name = 'config network autoassign'
    class_data_len = 3

    def __init__(self, parent, network_tree = None, range_start = None,
            range_end = None):
        super(ConfigNetworkAutoassign, self).__init__(parent)
        self._network_tree = network_tree
        self._range_start = range_start
        self._range_end = range_end

    def _loaded(self, node_data):
        super(ConfigNetworkAutoassign, self)._loaded(node_data)
        self._network_tree = self.root.getOID(node_data['data'][0])
        self._range_start = node_data['data'][1]
        self._range_end = node_data['data'][2]

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self._network_tree.oid,
                self._range_start, self._range_end)

    def _get_network_tree(self):
        return self._network_tree
    def _set_network_tree(self, val):
        self.transport.setValues(self.oid, val, self.range_start,
                self.range_end)
        self._network_tree = val
    network_tree = property(_get_network_tree, _set_network_tree)

    def _get_range_start(self):
        return self._range_start
    def _set_range_start(self, val):
        self.transport.setValues(self.oid, self.network_tree.oid,
                val, self.range_end)
        self._range_start = val
    range_start = property(_get_range_start, _set_range_start)

    def _get_range_end(self):
        return self._range_end
    def _set_range_end(self, val):
        self.transport.setValues(self.oid, self.network_tree.oid,
                self.range_start, val)
        self._range_end = val
    range_end = property(_get_range_end, _set_range_end)

class ConfigValue(treenodes.BaseNode):
    class_id = 'CFGVALUE'
    class_name = 'config value'
    class_data_len = 2

    def __init__(self, parent, name = None, value = None):
        super(ConfigValue, self).__init__(parent)
        self._name = name
        self._value = value

    def _loaded(self, node_data):
        super(ConfigValue, self)._loaded(node_data)
        self._name = node_data['data'][0]
        self._value = node_data['data'][1]

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self._name,
                self._value)

    def _get_name(self):
        return self._name

    def _set_name(self, val):
        self.transport.setName(self.oid, val)
        self._name = val
    name = property(_get_name, _set_name)

    def _get_value(self):
        return self._value

    def _set_value(self, val):
        self.transport.setValue(self.oid, val)
        self._value = val
    value = property(_get_value, _set_value)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(ConfigNetworkAutoassign)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(ConfigValue)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

