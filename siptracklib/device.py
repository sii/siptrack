from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import password
from siptracklib import counter
from siptracklib import template
from siptracklib import confignode
from siptracklib import permission
from siptracklib import errors

class DeviceTree(treenodes.BaseNode):
    class_id = 'DT'
    class_name = 'device tree'
    class_data_len = 0

    def __init__(self, parent):
        super(DeviceTree, self).__init__(parent)

    def getDeviceTree(self):
        return self

    def listNetworks(self, include_ranges = True):
        names = ['ipv4 network', 'ipv6 network']
        if include_ranges:
            names += ['ipv4 network range', 'ipv6 network range']
        networks = self.listLinks(include=names)
        networks.sort()
        return networks

class DeviceCategory(treenodes.BaseNode):
    class_id = 'DC'
    class_name = 'device category'
    class_data_len = 0
    
    def __init__(self, parent):
        super(DeviceCategory, self).__init__(parent)

    def getDeviceTree(self):
        return self.getParent('device tree')

    def listNetworks(self, include_ranges = True):
        names = ['ipv4 network', 'ipv6 network']
        if include_ranges:
            names += ['ipv4 network range', 'ipv6 network range']
        networks = self.listLinks(include=names)
        networks.sort()
        return networks

class Device(treenodes.BaseNode):
    class_id = 'D'
    class_name = 'device'
    class_data_len = 0

    def __init__(self, parent):
        super(Device, self).__init__(parent)

    def _created(self):
        self.oid = self.transport.add(self.parent.oid)

    def _loaded(self, node_data):
        super(Device, self)._loaded(node_data)

    def delete(self, prune_networks = True):
        self.transport.delete(self.oid, prune_networks)
        self._purge()

    def listNetworks(self, include_ranges = True):
        names = ['ipv4 network']
        if include_ranges:
            names += ['ipv4 network range']
        ipv4_networks = self.listLinks(include=names)
        ipv4_networks.sort()
        names = ['ipv6 network']
        if include_ranges:
            names += ['ipv6 network range']
        ipv6_networks = self.listLinks(include=names)
        ipv6_networks.sort()
        networks = ipv4_networks + ipv6_networks
        return networks

    def autoassignNetwork(self):
        oid = self.transport.autoassignNetwork(self.oid)
        network = self.root.getOID(oid)
        return network

    def getDeviceTree(self):
        return self.getParent('device tree')

    def _checkSafeParent(self, node):
        while node:
            if node == self:
                return False
            node = node.parent
        return True

    def _copySelf(self, target):
        return target.add('device')

def suggest_templates(base_node, target_class_id):
    templates = []
    for oid in base_node.transport_root.cmd.device.template.suggestTemplates(base_node.oid, target_class_id):
        template = base_node.root.getOID(oid)
        if template:
            templates.append(template)
    templates.sort()
    return templates

class Template(treenodes.BaseNode):
    class_id = 'DTMPL'
    class_name = 'device template'
    class_data_len = 2
    valid_rule_types = ['DTMPLRULEPASSWORD', 'DTMPLRULEASSIGNNET',
            'DTMPLRULESUBDEV']

    def __init__(self, parent, attribute_template = None,
            applies_to = []):
        super(Template, self).__init__(parent)
        self.attribute_template = attribute_template
        self.applies_to = applies_to

    def _loaded(self, node_data):
        super(Template, self)._loaded(node_data)
        if node_data['data'][0]:
            self.attribute_template = self.root.getOID(node_data['data'][0])
        else:
            self.attribute_template = None
        self.applies_to = node_data['data'][1]

    def _created(self):
        """Called when an object has been newly created."""
        attr_tmpl_oid = ''
        if self.attribute_template:
            attr_tmpl_oid = self.attribute_template.oid
        self.oid = self.transport.add(self.parent.oid,
                attr_tmpl_oid,
                self.applies_to)

    def apply(self, node, arguments = {}, overwrite = False):
        return self.transport.apply(self.oid, node.oid, arguments, overwrite)

    def combinedRules(self):
        data = self.transport.combinedRules(self.oid)
        # data[0] : node data for the matched rules.
        # data[1] : list of matching rules oids.
        self.root.loadChildren(data[0])
        for oid in data[1]:
            yield self.root.getOID(oid)

    def rules(self):
        for rule in self.listChildren():
            if rule.class_name in self.valid_rule_types:
                yield rule

    def setAttributeTemplate(self, attribute_template):
        oid = ''
        if attribute_template:
            oid = attribute_template.oid
        self.transport.setAttributeTemplate(self.oid, attribute_template.oid)
        self.attribute_template = attribute_template

    def setAppliesTo(self, applies_to):
        self.transport.setAppliesTo(self.oid, applies_to)
        self.applies_to = applies_to

class TemplateRulePassword(treenodes.BaseNode):
    class_id = 'DTMPLRULEPASSWORD'
    class_name = 'device template rule password'
    class_data_len = 3

    def __init__(self, parent, username = None, description = None, key = None):
        super(TemplateRulePassword, self).__init__(parent)
        self.username = username
        self.description = description
        self.key = key

    def _loaded(self, node_data):
        super(TemplateRulePassword, self)._loaded(node_data)
        self.username = node_data['data'][0]
        self.description = node_data['data'][1]
        key_oid = node_data['data'][2]
        if len(key_oid) > 0:
            self.key = self.root.getOID(key_oid)

    def _created(self):
        """Called when an object has been newly created."""
        key_oid = ''
        if self.key:
            key_oid = self.key.oid
        self.oid = self.transport.add(self.parent.oid, self.username,
                self.description, key_oid)

class TemplateRuleAssignNetwork(treenodes.BaseNode):
    class_id = 'DTMPLRULEASSIGNNET'
    class_name = 'device template rule assign network'
    class_data_len = 0

    def __init__(self, parent):
        super(TemplateRuleAssignNetwork, self).__init__(parent)

    def _loaded(self, node_data):
        super(TemplateRuleAssignNetwork, self)._loaded(node_data)

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid)

class TemplateRuleSubdevice(treenodes.BaseNode):
    class_id = 'DTMPLRULESUBDEV'
    class_name = 'device template rule subdevice'
    class_data_len = 0

    def __init__(self, parent, num_devices = None, device_template = None):
        super(TemplateRuleSubdevice, self).__init__(parent)
        self.num_devices = num_devices
        self.device_template = device_template

    def _loaded(self, node_data):
        super(TemplateRuleSubdevice, self)._loaded(node_data)
        self.num_devices = node_data['data'][0]
        device_template_oid = node_data['data'][1]
        if len(device_template_oid) > 0:
            self.device_template = self.root.getOID(device_template_oid)

    def _created(self):
        """Called when an object has been newly created."""
        device_template_oid = ''
        if self.device_template:
            device_template_oid = self.device_template.oid
        self.oid = self.transport.add(self.parent.oid, self.num_devices,
                device_template_oid)

    def setNumDevices(self, num_devices):
        self.transport.setNumDevices(self.oid, num_devices)
        self.num_devices = num_devices

    def setDeviceTemplate(self, device_template):
        device_template_oid = ''
        if device_template:
            device_template_oid = device_template.oid
        self.transport.setDeviceTemplate(self.oid, device_template_oid)
        self.device_template = device_template

# Add the objects in this module to the object registry.
o = object_registry.registerClass(DeviceTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(Device)
o.registerChild(DeviceCategory)
o.registerChild(template.DeviceTemplate)
o.registerChild(confignode.ConfigNetworkAutoassign)
o.registerChild(confignode.ConfigValue)
o.registerChild(permission.Permission)

o = object_registry.registerClass(DeviceCategory)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(Device)
o.registerChild(DeviceCategory)
o.registerChild(template.DeviceTemplate)
o.registerChild(confignode.ConfigNetworkAutoassign)
o.registerChild(confignode.ConfigValue)
o.registerChild(permission.Permission)

o = object_registry.registerClass(Device)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(Device)
o.registerChild(password.Password)
o.registerChild(confignode.ConfigNetworkAutoassign)
o.registerChild(confignode.ConfigValue)
o.registerChild(permission.Permission)

