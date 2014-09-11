from siptracklib.transport.xmlrpc import baserpc

class ViewTreeRPC(baserpc.BaseRPC):
    command_path = 'view.tree'

    def getUserManager(self):
        return self.send('get_user_manager')

    def setUserManager(self, user_manager_oid):
        return self.send('set_user_manager', user_manager_oid)

class ViewRPC(baserpc.BaseRPC):
    command_path = 'view'

    def add(self):
        return self.send('add')

