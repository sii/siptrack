from siptracklib.transport.xmlrpc import baserpc

class PermissionRPC(baserpc.BaseRPC):
    command_path = 'permission'

    def add(self, parent_oid, read_access, write_access, users,
            groups, all_users, recursive):
        return self.send('add', parent_oid, read_access, write_access,
                users, groups, all_users, recursive)

