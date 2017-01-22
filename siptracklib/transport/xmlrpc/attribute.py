from siptracklib.transport.xmlrpc import baserpc

class AttributeRPC(baserpc.BaseRPC):
    command_path = 'attribute'

    def add(self, parent_oid, name, atype, value):
        return self.send('add', parent_oid, name, atype, value)

    def setValue(self, oid, value):
        return self.send('set_value', oid, value)

class VersionedAttributeRPC(baserpc.BaseRPC):
    command_path = 'attribute.versioned'

    def add(self, parent_oid, name, atype, value, max_versions):
        if value is not None:
            return self.send('add', parent_oid, name, atype, max_versions, value)
        else:
            return self.send('add', parent_oid, name, atype, max_versions)

    def setValue(self, oid, value):
        return self.send('set_value', oid, value)

class EncryptedAttributeRPC(baserpc.BaseRPC):
    command_path = 'attribute.encrypted'

    def add(self, parent_oid, name, atype, value):
        return self.send('add', parent_oid, name, atype, value)

    def setValue(self, oid, value):
        return self.send('set_value', oid, value)
