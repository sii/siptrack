from siptracklib.transport.xmlrpc import baserpc

class PasswordTreeRPC(baserpc.BaseRPC):
    command_path = 'password.tree'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

class PasswordCategoryRPC(baserpc.BaseRPC):
    command_path = 'password.category'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

class PasswordRPC(baserpc.BaseRPC):
    command_path = 'password'

    def add(self, parent_oid, password, key_oid):
        return self.send('add', parent_oid, password, key_oid)

    def setPassword(self, oid, new_password):
        return self.send('set_password', oid, new_password)

    def setPasswordKey(self, oid, new_password_key_oid):
        return self.send('set_password_key', oid, new_password_key_oid)

class PasswordKeyRPC(baserpc.BaseRPC):
    command_path = 'password.key'

    def add(self, parent_oid, key):
        return self.send('add', parent_oid, key)

    def changeKey(self, oid, new_key):
        return self.send('change_key', oid, new_key)

class SubKeyRPC(baserpc.BaseRPC):
    command_path = 'password.subkey'

    def add(self, parent_oid, password_key_oid, key):
        return self.send('add', parent_oid, password_key_oid, key)

    def changeKey(self, oid, new_key):
        return self.send('change_key', oid, new_key)
