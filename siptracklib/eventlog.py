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
    class_data_len = 2

    def __init__(self, parent, event_type = None, event_data = None):
        super(EventLog, self).__init__(parent)
        self._event_type = event_type
        self._event_data = event_data

    def _created(self):
        self.oid = self.transport.add(self.parent.oid, self._event_type, self._event_data)

    def _loaded(self, node_data):
        super(EventLog, self)._loaded(node_data)
        self._event_type = node_data['data'][0]
        self._event_data = node_data['data'][1]

    def _get_event_type(self):
        return self._event_type
    def _set_event_type(self, val):
        raise Exception('event logs are readonly')
    event_type = property(_get_event_type, _set_event_type)

    def _get_event_data(self):
        return self._event_data
    def _set_event_data(self, val):
        raise Exception('event logs are readonly')
    event_data = property(_get_event_data, _set_event_data)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(EventLogTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(EventLog)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
