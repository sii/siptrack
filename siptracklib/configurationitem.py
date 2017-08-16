from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import password
from siptracklib import counter
from siptracklib import template
from siptracklib import confignode
from siptracklib import deviceconfig
from siptracklib import permission
from siptracklib import errors

class CITree(treenodes.BaseNode):
    class_id = 'CIT'
    class_name = 'ci tree'
    class_data_len = 0

    def __init__(self, parent):
        super(CITree, self).__init__(parent)

    def getCITree(self):
        return self


class CICategory(treenodes.BaseNode):
    class_id = 'CIC'
    class_name = 'ci category'
    class_data_len = 0
    
    def __init__(self, parent):
        super(DeviceCategory, self).__init__(parent)

    def getCITree(self):
        return self.getParent('ci tree')


class ConfigurationItem(treenodes.BaseNode):
    class_id = 'CI'
    class_name = 'configuration item'
    class_data_len = 0


    def __init__(self, parent):
        super(ConfigurationItem, self).__init__(parent)


    def _created(self):
        self.oid = self.transport.add(self.parent.oid)


    def _loaded(self, node_data):
        super(ConfigurationItem, self)._loaded(node_data)


    def getCITree(self):
        return self.getParent('ci tree')

    def _checkSafeParent(self, node):
        while node:
            if node == self:
                return False
            node = node.parent
        return True

    def _copySelf(self, target):
        return target.add('configuration item')

def suggest_templates(base_node, target_class_id):
    templates = []
    for oid in base_node.transport_root.cmd.device.template.suggestTemplates(base_node.oid, target_class_id):
        template = base_node.root.getOID(oid)
        if template:
            templates.append(template)
    templates.sort()
    return templates


class CITemplate(treenodes.BaseNode):
    class_id = 'CITMPL'
    class_name = 'ci template'
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
o.registerChild(deviceconfig.DeviceConfig)
o.registerChild(deviceconfig.DeviceConfigTemplate)

