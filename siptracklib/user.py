from bisect import bisect_left

from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import password
from siptracklib import errors


# Python3 compatibility hack
try:
    unicode('')
except NameError:
    unicode = str

class BaseUserManager(treenodes.BaseNode):
    def listUsers(self):
        return self.listChildren(include = ['user local', 'user ldap', 'user active directory'])

    def listGroups(self):
        return self.listChildren(include = ['user group', 'user group ldap', 'user group active directory'])

    def getUserByName(self, username):
        """
        Return list of users matching username.

        Example: user_manager.getUserByName('stemid')[0].username
        """
        return [x for x in self.listUsers() if x.username == username]

class UserManagerLocal(BaseUserManager):
    class_id = 'UM'
    class_name = 'user manager local'
    class_data_len = 0

    def __init__(self, parent):
        super(UserManagerLocal, self).__init__(parent)
        self._value = 0

class UserManagerLDAP(BaseUserManager):
    class_id = 'UML'
    class_name = 'user manager ldap'
    class_data_len = 5

    def __init__(self, parent, connection_type = None,
            server = None, port = None, base_dn = None, valid_groups = None):
        super(UserManagerLDAP, self).__init__(parent)
        self.connection_type = connection_type
        self.server = server
        self.port = port
        self.base_dn = base_dn
        self.valid_groups = valid_groups

    def _created(self):
        if type(self.connection_type) not in [unicode, str]:
            raise errors.SiptrackError('invalid connection type in UserManagerLDAP object')
        if type(self.server) not in [unicode, str]:
            raise errors.SiptrackError('invalid server in UserManagerLDAP object')
        if type(self.port) not in [unicode, str]:
            raise errors.SiptrackError('invalid port in UserManagerLDAP object')
        if type(self.base_dn) not in [unicode, str]:
            raise errors.SiptrackError('invalid base dn in UserManagerLDAP object')
        if not isinstance(self.valid_groups, list):
            raise errors.SiptrackError('invalid valid groups in UserManagerLDAP object')
        self.oid = self.transport.add(self.parent.oid, self.connection_type,
                self.server, self.port, self.base_dn, self.valid_groups)

    def _loaded(self, node_data):
        super(UserManagerLDAP, self)._loaded(node_data)
        self.connection_type = node_data['data'][0]
        self.server = node_data['data'][1]
        self.port = node_data['data'][2]
        self.base_dn = node_data['data'][3]
        self.valid_groups = node_data['data'][4]

    def syncUsers(self, purge_missing_users = False):
        self.transport.syncUsers(self.oid, purge_missing_users)
        self.fetched_children = False

    def setConnectionType(self, connection_type):
        self.transport.setConnectionType(self.oid, connection_type)
        self.connection_type = connection_type

    def setServer(self, server):
        self.transport.setServer(self.oid, server)
        self.server = server

    def setPort(self, port):
        self.transport.setPort(self.oid, port)
        self.port = port

    def setBaseDN(self, base_dn):
        self.transport.setBaseDN(self.oid, base_dn)
        self.base_dn = base_dn

    def setValidGroups(self, valid_groups):
        self.transport.setValidGroups(self.oid, valid_groups)
        self.valid_groups = valid_groups

class UserManagerActiveDirectory(BaseUserManager):
    class_id = 'UMAD'
    class_name = 'user manager active directory'
    class_data_len = 4

    def __init__(self, parent, server = None, base_dn = None,
                 valid_groups = None, user_domain = None):
        super(UserManagerActiveDirectory, self).__init__(parent)
        self.server = server
        self.base_dn = base_dn
        self.valid_groups = valid_groups
        self.user_domain = user_domain

    def _created(self):
        if type(self.server) not in [unicode, str]:
            raise errors.SiptrackError('invalid server in UserManagerActiveDirectory object')
        if type(self.base_dn) not in [unicode, str]:
            raise errors.SiptrackError('invalid base dn in UserManagerActiveDirectory object')
        if not isinstance(self.valid_groups, list):
            raise errors.SiptrackError('invalid valid groups in UserManagerActiveDirectory object')
        if type(self.user_domain) not in [unicode, str]:
            raise errors.SiptrackError('invalid user domain in UserManagerActiveDirectory object')
        self.oid = self.transport.add(self.parent.oid,
                self.server, self.base_dn, self.valid_groups, self.user_domain)

    def _loaded(self, node_data):
        super(UserManagerActiveDirectory, self)._loaded(node_data)
        self.server = node_data['data'][0]
        self.base_dn = node_data['data'][1]
        self.valid_groups = node_data['data'][2]
        self.user_domain = node_data['data'][3]

    def syncUsers(self, username, password, purge_missing_users = False):
        self.transport.syncUsers(self.oid, username, password, purge_missing_users)
        self.fetched_children = False

    def setServer(self, server):
        self.transport.setServer(self.oid, server)
        self.server = server

    def setBaseDN(self, base_dn):
        self.transport.setBaseDN(self.oid, base_dn)
        self.base_dn = base_dn

    def setValidGroups(self, valid_groups):
        self.transport.setValidGroups(self.oid, valid_groups)
        self.valid_groups = valid_groups

    def setUserDomain(self, user_domain):
        self.transport.setUserDomain(self.oid, user_domain)
        self.user_domain = user_domain

class BaseUserGroup(treenodes.BaseNode):
    class_data_len = 1

    def __init__(self, parent, users = None):
        super(BaseUserGroup, self).__init__(parent)
        self._users = treenodes.NodeList(self, users)

    def _loaded(self, node_data):
        super(BaseUserGroup, self)._loaded(node_data)
        self._users.set(node_data['data'][0])

    def _created(self):
        """Called when an object has been newly created."""
        users = self._users.oids
        self.oid = self.transport.add(self.parent.oid, users)

    def _get_users(self):
        return self._users.get()
    def _set_users(self, val):
        return
    users = property(_get_users, _set_users)

class UserGroup(BaseUserGroup):
    class_id = 'UG'
    class_name = 'user group'
    class_data_len = 1

    def setUsers(self, users):
        u = [u.oid for u in users]
        self.transport.setUsers(self.oid, u)
        self._users.setNodes(users)

class UserGroupLDAP(BaseUserGroup):
    class_id = 'UGL'
    class_name = 'user group ldap'
    class_data_len = 1

class UserGroupActiveDirectory(BaseUserGroup):
    class_id = 'UGAD'
    class_name = 'user group active directory'
    class_data_len = 1

class BaseUser(treenodes.BaseNode):
    def __init__(self, parent, username = None, password = None,
            administrator = None):
        super(BaseUser, self).__init__(parent)
        self.username = username
        self.password = password
        self.administrator = administrator

    def _created(self):
        if self.username == None:
            raise errors.SiptrackError('invalid username in user object')
        if self.password == None:
            raise errors.SiptrackError('invalid password in user object')
        if self.administrator == None:
            raise errors.SiptrackError('invalid administrator value in user object')
        self.oid = self.transport.add(self.parent.oid, self.username,
                self.password, self.administrator)
        self.password = None

    def _loaded(self, node_data):
        super(BaseUser, self)._loaded(node_data)
        self.username = node_data['data'][0]
        self.administrator = node_data['data'][1]

    def setUsername(self, username):
        self.transport.setUsername(self.oid, username)
        self.username = username

    def setPassword(self, new_password, old_password):
        self.transport.setPassword(self.oid, new_password, old_password)

    def resetPassword(self, password):
        self.transport.resetPassword(self.oid, password)

    def setAdministrator(self, value):
        self.transport.setAdministrator(self.oid, value)
        self.administrator = value

    def connectPasswordKey(self, password_key, user_password = None,
            password_key_key = None):
        self.transport.connectPasswordKey(self.oid, password_key.oid,
                user_password, password_key_key)

class UserLocal(BaseUser):
    class_id = 'U'
    class_name = 'user local'
    class_data_len = 2

class UserLDAP(BaseUser):
    class_id = 'UL'
    class_name = 'user ldap'
    class_data_len = 2

class UserActiveDirectory(BaseUser):
    class_id = 'UAD'
    class_name = 'user active directory'
    class_data_len = 2

# Add the objects in this module to the object registry.
o = object_registry.registerClass(UserManagerLocal)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(UserLocal)
o.registerChild(UserGroup)

o = object_registry.registerClass(UserManagerLDAP)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(UserLDAP)
o.registerChild(UserGroup)
o.registerChild(UserGroupLDAP)

o = object_registry.registerClass(UserManagerActiveDirectory)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(UserActiveDirectory)
o.registerChild(UserGroup)
o.registerChild(UserGroupActiveDirectory)

o = object_registry.registerClass(UserLocal)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(password.SubKey)
o.registerChild(password.PasswordKey)
o.registerChild(password.PublicKey)
o.registerChild(password.PendingSubKey)
o.registerChild(password.PasswordTree)

o = object_registry.registerClass(UserLDAP)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(password.SubKey)
o.registerChild(password.PasswordKey)
o.registerChild(password.PublicKey)
o.registerChild(password.PendingSubKey)
o.registerChild(password.PasswordTree)

o = object_registry.registerClass(UserActiveDirectory)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(password.SubKey)
o.registerChild(password.PasswordKey)
o.registerChild(password.PublicKey)
o.registerChild(password.PendingSubKey)
o.registerChild(password.PasswordTree)

o = object_registry.registerClass(UserGroup)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(UserGroupLDAP)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(UserGroupActiveDirectory)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
