from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute

class Permission(treenodes.BaseNode):
    class_id = 'PERM'
    class_name = 'permission'
    class_data_len = 6

    def __init__(self, parent, read_access = None, write_access = None,
            users = None, groups = None, all_users = None,
            recursive = None):
        super(Permission, self).__init__(parent)
        self.read_access = read_access
        self.write_access = write_access
        self._users = treenodes.NodeList(self, users)
        self._groups = treenodes.NodeList(self, groups)
        self.all_users = all_users
        self.recursive = recursive

    def _loaded(self, node_data):
        super(Permission, self)._loaded(node_data)
        self.read_access = node_data['data'][0]
        self.write_access = node_data['data'][1]
        self._users.set(node_data['data'][2])
        self._groups.set(node_data['data'][3])
        self.all_users = node_data['data'][4]
        self.recursive = node_data['data'][5]

    def _created(self):
        """Called when an object has been newly created."""
        users = self._users.oids
        groups = self._groups.oids
        self.oid = self.transport.add(self.parent.oid, self.read_access,
                self.write_access, users, groups, self.all_users,
                self.recursive)

    def _get_users(self):
        return self._users.get()
    def _set_users(self, val):
        return
    users = property(_get_users, _set_users)

    def _get_groups(self):
        return self._groups.get()
    def _set_groups(self, val):
        return
    groups = property(_get_groups, _set_groups)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(Permission)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

