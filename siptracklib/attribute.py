from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import errors

class Attribute(treenodes.BaseNode):
    """A single attribute.

    Attributes are used by pretty much every other object type.
    They are used to store varying types of data.
    Arguments:
        name  : the attribute name.
        atype : the attribute type, one of:
            text   : a unicode string.
            binary : a string of binary data (no encoding/decoding performed)
            int    : an integer
            bool   : True/False
        value : a value matching the attributes type.
    """
    class_id = 'CA'
    class_name = 'attribute'
    class_data_len = 3
    sort_type = 'attribute'

    def __init__(self, parent, name = None, atype = None, value = None):
        super(Attribute, self).__init__(parent)
        self.name = name
        self.atype = atype
        self._value = value

    def __lt__(self, other):
        if not isinstance(other, treenodes.BaseNode):
            return False
        if not other.class_name in ['attribute', 'versioned attribute']:
            return False
        if self.name < other.name:
            return True
        return False

    def __eq__(self, other):
        if not isinstance(other, treenodes.BaseNode):
            return False
        if not other.class_name in ['attribute', 'versioned attribute']:
            return False
        if self.name == other.name:
            return True
        return False

    def describe(self):
        if self.atype in ['text', 'bool', 'int']:
            return '%s:%s:%s:%s:%s' % (self.class_name, self.oid, self.name,
                    self.atype, self.value)
        else:
            return '%s:%s:%s:%s' % (self.class_name, self.oid, self.name,
                    self.atype)

    def dictDescribe(self):
        data = super(Attribute, self).dictDescribe()
        data['name'] = self.name
        data['atype'] = self.atype
#        data['value'] = self.value
        return data

    def getParentNode(self):
        """Get the closest parent _non-attribute_ node."""
        parent = self
        while parent.class_id == 'CA':
            parent = parent.parent
        return parent

    def _created(self):
        self.oid = self.transport.add(self.parent.oid, self.name,
                self.atype, self.value)

    def _loaded(self, node_data):
        super(Attribute, self)._loaded(node_data)
        self.name = node_data['data'][0]
        self.atype = node_data['data'][1]
        self._value = node_data['data'][2]

    def _get_value(self):
        return self._value

    def _set_value(self, val):
        self._value = val
        self.transport.setValue(self.oid, val)
    value = property(_get_value, _set_value)

    def _copySelf(self, target):
        return target.add('attribute', self.name, self.atype, self.value)

class VersionedAttribute(treenodes.BaseNode):
    """A single attribute.

    Attributes are used by pretty much every other object type.
    They are used to store varying types of data.
    Arguments:
        name  : the attribute name.
        atype : the attribute type, one of:
            text   : a unicode string.
            binary : a string of binary data (no encoding/decoding performed)
            int    : an integer
            bool   : True/False
        value : a value matching the attributes type.
    """
    class_id = 'VA'
    class_name = 'versioned attribute'
    class_data_len = 4
    sort_type = 'attribute'

    def __init__(self, parent, name = None, atype = None,
            value = None, max_versions = 1):
        super(VersionedAttribute, self).__init__(parent)
        self.name = name
        self.atype = atype
        self.max_versions = max_versions
        self._value = value
        self.values = []
        if value is not None:
            self.values = [value]

    def __lt__(self, other):
        if not isinstance(other, treenodes.BaseNode):
            return False
        if not other.class_name in ['attribute', 'versioned attribute']:
            return False
        if self.name < other.name:
            return True
        return False

    def __eq__(self, other):
        if not isinstance(other, treenodes.BaseNode):
            return False
        if not other.class_name in ['attribute', 'versioned attribute']:
            return False
        if self.name == other.name:
            return True
        return False

    def describe(self):
        if self.atype in ['text', 'bool', 'int']:
            return '%s:%s:%s:%s:%s' % (self.class_name, self.oid, self.name,
                    self.atype, self.value)
        else:
            return '%s:%s:%s:%s' % (self.class_name, self.oid, self.name,
                    self.atype)

    def dictDescribe(self):
        data = super(VersionedAttribute, self).dictDescribe()
        data['name'] = self.name
        data['atype'] = self.atype
#        data['value'] = self.value
        return data

    def getParentNode(self):
        """Get the closest parent _non-attribute_ node."""
        parent = self
        while parent.class_id == 'VA':
            parent = parent.parent
        return parent

    def _created(self):
        self.oid = self.transport.add(self.parent.oid, self.name,
                self.atype, self._value, self.max_versions)

    def _loaded(self, node_data):
        super(VersionedAttribute, self)._loaded(node_data)
        self.name = node_data['data'][0]
        self.atype = node_data['data'][1]
        self.values = node_data['data'][2]
        self.max_versions = node_data['data'][3]

    def _get_value(self):
        return self.values[-1]

    def _set_value(self, val):
        self.transport.setValue(self.oid, val)
        self.values.append(val)
        if len(self.values) > self.max_versions:
            self.values.pop(0)
    value = property(_get_value, _set_value)

    def _copySelf(self, target):
        return target.add('versioned attribute', self.name, self.atype, self.value, self.max_versions)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(Attribute)
o.registerChild(Attribute)
o.registerChild(VersionedAttribute)

o = object_registry.registerClass(VersionedAttribute)
o.registerChild(Attribute)
o.registerChild(VersionedAttribute)

