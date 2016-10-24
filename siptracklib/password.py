from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import permission

class PasswordTree(treenodes.BaseNode):
    class_id = 'PT'
    class_name = 'password tree'
    class_data_len = 0

class PasswordCategory(treenodes.BaseNode):
    class_id = 'PC'
    class_name = 'password category'
    class_data_len = 0
    
class Password(treenodes.BaseNode):
    class_id = 'P'
    class_name = 'password'
    class_data_len = 2

    def __init__(self, parent, password = None, key = None):
        super(Password, self).__init__(parent)
        self.password = password
        self._key = key
        self._key_oid = None
        self._fetched_key = False

    def _created(self):
        if self.password == None:
            raise errors.SiptrackError('invalid password in password object')
        key_oid = self.getObjectOID(self._key)
        self.oid = self.transport.add(self.parent.oid, self.password, key_oid)

    def _loaded(self, node_data):
        super(Password, self)._loaded(node_data)
        self.password = node_data['data'][0]
        self._key_oid = node_data['data'][1]

    def _get_key(self):
        if not self._key and not self._fetched_key:
            self._fetched_key = True
            try:
                self._key = self.root.getOID(self._key_oid)
            except:
                pass
        return self._key

    def _set_key(self, val):
        return
    key = property(_get_key, _set_key)

    def setPassword(self, new_password):
        self.transport.setPassword(self.oid, new_password)

    def setPasswordKey(self, new_password_key):
        pk_oid = ''
        if new_password_key:
            pk_oid = new_password_key.oid
        self.transport.setPasswordKey(self.oid, pk_oid)

class PasswordKey(treenodes.BaseNode):
    class_id = 'PK'
    class_name = 'password key'
    class_data_len = 0

    def __init__(self, parent, key = None):
        super(PasswordKey, self).__init__(parent)
        self.key = key

    def _created(self):
        if self.key == None:
            raise errors.SiptrackError('invalid key in password key object')
        self.oid = self.transport.add(self.parent.oid, self.key)

    def changeKey(self, new_key):
        self.transport.changeKey(self.oid, new_key)

    def isValidPassword(self, test_password):
        self.transport.isValidPassword(self.oid, test_password)


class SubKey(treenodes.BaseNode):
    class_id = 'SK'
    class_name = 'sub key'
    class_data_len = 1

    def __init__(self, parent, password_key = None, key = None):
        super(SubKey, self).__init__(parent)
        self.key = key
        self._password_key = password_key

    def _created(self):
        if self._password_key == None:
            raise errors.SiptrackError('invalid password key in sub key object')
        if self.key == None:
            raise errors.SiptrackError('invalid key in sub key object')
        self.oid = self.transport.add(self.parent.oid,
                self._password_key.oid, self.key)
        self.key = None

    def _loaded(self, node_data):
        super(SubKey, self)._loaded(node_data)
        self._password_key_oid = node_data['data'][0]

    def changeKey(self, new_key):
        self.transport.changeKey(self.oid, new_key)

    def _get_password_key(self):
        if self._password_key is None:
            self._password_key = self.root.getOID(self._password_key_oid)
        return self._password_key

    def _set_password_key(self, val):
        return
    password_key = property(_get_password_key, _set_password_key)

class PublicKey(treenodes.BaseNode):
    class_id = 'PUK'
    class_name = 'public key'
    class_data_len = 0

class PendingSubKey(treenodes.BaseNode):
    class_id = 'PSK'
    class_name = 'pending sub key'
    class_data_len = 0

# Add the objects in this module to the object registry.
o = object_registry.registerClass(PasswordTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
o.registerChild(PasswordCategory)
o.registerChild(PasswordKey)
o.registerChild(Password)

o = object_registry.registerClass(PasswordCategory)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
o.registerChild(Password)
o.registerChild(PasswordCategory)

o = object_registry.registerClass(Password)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(PasswordKey)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(SubKey)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(Password)
o.registerChild(PasswordKey)

o = object_registry.registerClass(PublicKey)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(PendingSubKey)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

