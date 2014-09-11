from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import container
from siptracklib import attribute
from siptracklib import counter
from siptracklib import device
from siptracklib import network
from siptracklib import password
from siptracklib import user
from siptracklib import confignode
from siptracklib import permission
from siptracklib import event

class ViewTree(treenodes.BaseNode):
    """A view tree, contains a list of view.

    There is generally only one viewtree (oid 0).
    """
    class_id = 'VT'
    class_name = 'view tree'
    class_data_len = 1

    def __init__(self, parent):
        super(ViewTree, self).__init__(parent)
        self._user_manager_oid = None

    def _created(self):
        """There is one and only one view tree, no more can be made."""
        raise errors.SiptrackError('sorry, can\'t create view trees')

    def _loaded(self, node_data):
        super(ViewTree, self)._loaded(node_data)
        self._user_manager_oid = node_data['data'][0]

    def delete(self):
        raise errors.SiptrackError('sorry, can\'t remove the view tree')

    def _get_user_manager(self):
        if self._user_manager_oid is None:
            self._user_manager_oid = self.transport.getUserManager()
        return self.root.getOID(self._user_manager_oid)

    def _set_user_manager(self, val):
        self.transport.setUserManager(val.oid)
    user_manager = property(_get_user_manager, _set_user_manager)

class View(treenodes.BaseNode):
    """A network/device/everything view.

    A view is the main toplevel object type. It contains everything from
    networks to devices to counters etc.
    """
    class_id = 'V'
    class_name = 'view'
    class_data_len = 0

    def __init__(self, parent):
        super(View, self).__init__(parent)

    def _created(self):
        self.oid = self.transport.add()
        nt = self.add('network tree', 'ipv4')
        nt.attributes['name'] = 'ipv4'
        nt = self.add('network tree', 'ipv6')
        nt.attributes['name'] = 'ipv6'
        dt = self.add('device tree')
        dt.attributes['name'] = 'default'
        dt = self.add('password tree')
        dt.attributes['name'] = 'default'

# Add the objects in this module to the object registry.
o = object_registry.registerClass(ViewTree)
o.registerChild(View)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(user.UserManagerLocal)
o.registerChild(user.UserManagerLDAP)
o.registerChild(user.UserManagerActiveDirectory)
o.registerChild(confignode.ConfigValue)
o.registerChild(permission.Permission)
o.registerChild(event.CommandQueue)
o.registerChild(event.EventTrigger)

o = object_registry.registerClass(View)
o.registerChild(container.ContainerTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(network.NetworkTree)
o.registerChild(counter.Counter)
o.registerChild(counter.CounterLoop)
o.registerChild(device.DeviceTree)
o.registerChild(password.PasswordKey)
o.registerChild(password.PasswordTree)
o.registerChild(confignode.ConfigNetworkAutoassign)
o.registerChild(confignode.ConfigValue)
o.registerChild(permission.Permission)

