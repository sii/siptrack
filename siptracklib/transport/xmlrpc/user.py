from siptracklib.transport.xmlrpc import baserpc

class UserRPC(baserpc.BaseRPC):
    command_path = 'user'

class UserManagerRPC(baserpc.BaseRPC):
    command_path = 'user.manager'

class BaseUserRPC(baserpc.BaseRPC):
    def add(self, parent_oid, username, password, administrator):
        return self.send('add', parent_oid, username, password,
                administrator)

    def setUsername(self, oid, username):
        return self.send('set_username', oid, username)

    def setPassword(self, oid, new_password, old_password):
        return self.send('set_password', oid, new_password, old_password)

    def resetPassword(self, oid, password):
        return self.send('reset_password', oid, password)

    def setAdministrator(self, oid, value):
        return self.send('set_administrator', oid, value)

    def connectPasswordKey(self, user_oid, password_key_oid,
            user_password = None, password_key_key = None):
        if user_password is None:
            user_password = False
        if password_key_key is None:
            password_key_key = False
        return self.send('connect_password_key', user_oid, password_key_oid,
                user_password, password_key_key)

class UserLocalRPC(BaseUserRPC):
    command_path = 'user.local'

class UserLDAPRPC(BaseUserRPC):
    command_path = 'user.ldap'

class UserActiveDirectoryRPC(BaseUserRPC):
    command_path = 'user.ad'

class UserManagerLocalRPC(baserpc.BaseRPC):
    command_path = 'user.manager.local'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

class UserManagerLDAPRPC(baserpc.BaseRPC):
    command_path = 'user.manager.ldap'

    def add(self, parent_oid, connection_type, server, port, base_dn,
            valid_groups):
        return self.send('add', parent_oid, connection_type, server,
                port, base_dn, valid_groups)

    def syncUsers(self, oid, purge_missing_users):
        return self.send('sync_users', oid, purge_missing_users)

    def setConnectionType(self, oid, connection_type):
        return self.send('set_connection_type', oid, connection_type)

    def setServer(self, oid, server):
        return self.send('set_server', oid, server)

    def setPort(self, oid, port):
        return self.send('set_port', oid, port)

    def setBaseDN(self, oid, base_dn):
        return self.send('set_base_dn', oid, base_dn)

    def setValidGroups(self, oid, valid_groups):
        return self.send('set_valid_groups', oid, valid_groups)

class UserManagerActiveDirectoryRPC(baserpc.BaseRPC):
    command_path = 'user.manager.ad'

    def add(self, parent_oid, server, base_dn,
            valid_groups, user_domain):
        return self.send('add', parent_oid, server,
                base_dn, valid_groups, user_domain)

    def syncUsers(self, oid, username, password, purge_missing_users):
        return self.send('sync_users', oid, username, password, purge_missing_users)

    def setServer(self, oid, server):
        return self.send('set_server', oid, server)

    def setBaseDN(self, oid, base_dn):
        return self.send('set_base_dn', oid, base_dn)

    def setValidGroups(self, oid, valid_groups):
        return self.send('set_valid_groups', oid, valid_groups)

class UserGroupRPC(baserpc.BaseRPC):
    command_path = 'user.group'

    def add(self, parent_oid, users):
        return self.send('add', parent_oid, users)

    def setUsers(self, oid, users):
        return self.send('set_users', oid, users)

class UserGroupLDAPRPC(baserpc.BaseRPC):
    command_path = 'user.group.ldap'

class UserGroupActiveDirectoryRPC(baserpc.BaseRPC):
    command_path = 'user.group.ad'

