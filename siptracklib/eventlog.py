from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import permission

class EventLogTree(treenodes.BaseNode):
    class_id = 'ELT'
    class_name = 'event log tree'
    class_data_len = 0

class EventLog(treenodes.BaseNode):
    class_id = 'EL'
    class_name = 'event log'
    class_data_len = 1

    def __init__(self, parent, logtext = None):
        super(EventLog, self).__init__(parent)
        self._logtext = logtext

    def _created(self):
        self.oid = self.transport.add(self.parent.oid, self._logtext)

    def _loaded(self, node_data):
        super(EventLog, self)._loaded(node_data)
        self._logtext = node_data['data'][0]

    def _get_logtext(self):
        return self._logtext

    def _set_logtext(self, val):
        raise Exception('event logs are readonly')
    logtext = property(_get_logtext, _set_logtext)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(EventLogTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(EventLog)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
