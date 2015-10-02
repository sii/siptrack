from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import permission

class DeviceConfig(treenodes.BaseNode):
    class_id = 'DCON'
    class_name = 'device config'
    class_data_len = 2

    def __init__(self, parent, name = None, max_versions = None):
        super(DeviceConfig, self).__init__(parent)
        self._name = name
        self._max_versions = max_versions

    def _loaded(self, node_data):
        super(DeviceConfig, self)._loaded(node_data)
        self._name = node_data['data'][0]
        self._max_versions = node_data['data'][1]

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self._name,
                self._max_versions)

    def _get_name(self):
        return self._name

    def _set_name(self, val):
        self.transport.setName(self.oid, val)
        self._name = val
    name = property(_get_name, _set_name)

    def _get_max_versions(self):
        return self._max_versions

    def _set_max_versions(self, val):
        self.transport.setMaxVersions(self.oid, val)
        self._max_versions = val
    max_versions = property(_get_max_versions, _set_max_versions)

    def addConfig(self, data):
        return self.transport.addConfig(self.oid, data)

    def getLatestConfig(self):
        return self.transport.getLatestConfig(self.oid)

    def getAllConfigs(self):
        return self.transport.getAllConfigs(self.oid)

    def getTimestampConfig(self, timestamp):
        return self.transport.getTimestampConfig(self.oid, timestamp)

    def getStats(self):
        return self.transport.getStats(self.oid)

class DeviceConfigTemplate(treenodes.BaseNode):
    class_id = 'DCTMPL'
    class_name = 'device config template'
    class_data_len = 0

    def __init__(self, parent, template = None):
        super(DeviceConfigTemplate, self).__init__(parent)
        self._template = template

    def _loaded(self, node_data):
        super(DeviceConfigTemplate, self)._loaded(node_data)

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self._template)

    def _get_template(self):
        return self.transport.getTemplate(self.oid)

    def _set_template(self, template):
        self.transport.setTemplate(self.oid, template)
        self._template = template
    template = property(_get_template, _set_template)

    def expand(self, keywords = None):
        if not keywords:
            keywords = {}
        return self.transport.expand(self.oid, keywords)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(DeviceConfig)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(DeviceConfigTemplate)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

