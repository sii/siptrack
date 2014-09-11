from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import permission

class Counter(treenodes.BaseNode):
    class_id = 'CNT'
    class_name = 'counter'
    class_data_len = 1

    def __init__(self, parent):
        super(Counter, self).__init__(parent)
        self._value = 0

    def _loaded(self, node_data):
        super(Counter, self)._loaded(node_data)
        self._value = node_data['data'][0]

    def _get_value(self):
        return self._value

    def _set_value(self, val):
        self._value = val
        self.transport.set(self.oid, val)
    value = property(_get_value, _set_value)

class CounterLoop(treenodes.BaseNode):
    class_id = 'CNTLOOP'
    class_name = 'counter loop'
    class_data_len = 2

    def __init__(self, parent, values = None):
        super(CounterLoop, self).__init__(parent)
        self._value = None
        self._values = values

    def _loaded(self, node_data):
        super(CounterLoop, self)._loaded(node_data)
        self._value = node_data['data'][0]
        self._values = node_data['data'][1]

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self._values)
        pass

    def _get_value(self):
        return self._value

    def _set_value(self, val):
        self._value = val
        self.transport.set(self.oid, val)
    value = property(_get_value, _set_value)

    def _get_values(self):
        return self._values

    def _set_values(self, val):
        self._values = val
        self.transport.setValues(self.oid, val)
    values = property(_get_values, _set_values)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(Counter)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(CounterLoop)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
