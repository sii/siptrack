import hashlib

from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import errors

class AttributeBase(treenodes.BaseNode):

    def __init__(self, parent, name = None, atype = None, value = None):
        super(AttributeBase, self).__init__(parent)
        self._valid_attributes = [
            'attribute',
            'versioned attribute',
            'encrypted attribute'
        ]

        self.name = name
        self.atype = atype
        self._value = value


    def __lt__(self, other):
        if not isinstance(other, treenodes.BaseNode):
            return False
        if not other.class_name in self._valid_attributes:
            return False
        if self.name < other.name:
            return True
        return False


    def __eq__(self, other):
        if not isinstance(other, treenodes.BaseNode):
            return False
        if not other.class_name in self._valid_attributes:
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
        data = super(AttributeBase, self).dictDescribe()
        data['name'] = self.name
        data['atype'] = self.atype
        v = self.value
        if type(v) in [int, long, bool]:
            v = str(v)
        elif type(v) == unicode:
            v = v.encode('utf-8')
        data['value'] = hashlib.md5(v).hexdigest()
        return data



class Attribute(AttributeBase):
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

class VersionedAttribute(AttributeBase):
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
        super(VersionedAttribute, self).__init__(
            parent,
            name,
            atype,
            value,
            max_versions
        )

        self.max_versions = max_versions
        self.values = []
        if value is not None:
            self.values = [value]


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


class EncryptedAttribute(AttributeBase):

    class_id = 'ENCA'
    class_name = 'encrypted attribute'
    class_data_len = 3
    sort_type = 'attribute'

    def __init__(self, parent, name = None, atype = None, value = None):
        super(EncryptedAttribute, self).__init__(parent, name, atype, value)


    def getParentNode(self):
        parent = self
        while parent.class_id == self.class_id:
            parent = parent.parent
        return parent


    def _created(self):
        self.oid = self.transport.add(
            self.parent.oid,
            self.name,
            self.atype,
            self.value
        )


    def _loaded(self, node_data):
        super(EncryptedAttribute, self)._loaded(node_data)
        self.name = node_data['data'][0]
        self.atype = node_data['data'][1]
        self._value = node_data['data'][2]


    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val
        self.transport.setValue(self.oid, val)

    
    def _copySelf(self, target):
        return target.add(
            'encrypted attribute',
            self.name,
            self.atype,
            self._value
        )


# Add the objects in this module to the object registry.
o = object_registry.registerClass(Attribute)
o.registerChild(Attribute)
o.registerChild(VersionedAttribute)

o = object_registry.registerClass(VersionedAttribute)
o.registerChild(Attribute)
o.registerChild(VersionedAttribute)

o = object_registry.registerClass(EncryptedAttribute)
o.registerChild(Attribute)
o.registerChild(VersionedAttribute)
