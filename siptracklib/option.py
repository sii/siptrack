from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import password
from siptracklib import counter
from siptracklib import template
from siptracklib import confignode
from siptracklib import permission
from siptracklib import errors

class OptionTree(treenodes.BaseNode):
    class_id = 'OT'
    class_name = 'option tree'
    class_data_len = 0

    def __init__(self, parent):
        super(OptionTree, self).__init__(parent)

class OptionCategory(treenodes.BaseNode):
    class_id = 'OC'
    class_name = 'option category'
    class_data_len = 0
    
    def __init__(self, parent):
        super(OptionCategory, self).__init__(parent)

    def getOptionTree(self):
        return self.getParent('option tree')

class OptionValue(treenodes.BaseNode):
    class_id = 'OV'
    class_name = 'option value'
    class_data_len = 1

    def __init__(self, parent):
        super(OptionValue, self).__init__(parent)
        self._value = ''
    
    def _loaded(self, node_data):
        super(OptionValue, self)._loaded(node_data)
        self._value = node_data['data'][0]

    def _get_value(self):
        return self._value

    def _set_value(self, val):
        self._value = val
        self.transport.set(self.oid, val)
    value = property(_get_value, _set_value)

    def _created(self):
        self.oid = self.transport.add(self.parent.oid, self._value)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(OptionTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(OptionCategory)

o = object_registry.registerClass(OptionCategory)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(OptionValue)

o = object_registry.registerClass(OptionValue)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(OptionValue)

