from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import password
from siptracklib import counter

def suggest_templates(base_node, template_type):
    templates = []
    for oid in base_node.transport_root.cmd.template.suggestTemplates(base_node.oid, template_type):
        template = base_node.root.getOID(oid)
        if template:
            templates.append(template)
    templates.sort()
    return templates

class BaseTemplate(treenodes.BaseNode):
    class_id = 'TMPL'
    class_name = 'template'
    class_data_len = 2
    valid_rule_types = ['TMPLRULETEXT', 'TMPLRULEFIXED', 'TMPLRULEREGMATCH',
            'TMPLRULEBOOL', 'TMPLRULEPASSWORD', 'TMPLRULEASSIGNNET',
            'TMPLRULESUBDEV', 'TMPLRULEINT', 'TMPLRULEDELATTR']

    def __init__(self, parent, inheritance_only = None,
            inherited_templates = None):
        super(BaseTemplate, self).__init__(parent)
        self.inheritance_only = inheritance_only
        self._inherited_templates = treenodes.NodeList(self, inherited_templates)

    def _loaded(self, node_data):
        super(BaseTemplate, self)._loaded(node_data)
        self.inheritance_only = node_data['data'][0]
        self._inherited_templates.set(node_data['data'][1])

    def _created(self):
        """Called when an object has been newly created."""
        inherited_templates = self._inherited_templates.oids
        self.oid = self.transport.add(self.parent.oid,
                self.inheritance_only,
                inherited_templates)

    def apply(self, node, arguments = {}, overwrite = False, skip_rules = []):
        return self.transport.apply(self.oid, node.oid, arguments, overwrite,
                skip_rules)

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

    def setInheritanceOnly(self, inheritance_only):
        self.transport.setInheritanceOnly(self.oid, inheritance_only)
        self.inheritance_only = inheritance_only

    def setInheritedTemplates(self, inherited_templates):
        inherited_template_oids = [node.oid for node in inherited_templates]
        self.transport.setInheritedTemplates(self.oid, inherited_template_oids)
        self._inherited_templates.setNodes(inherited_templates)

    def _get_inherited_templates(self):
        return self._inherited_templates.get()
    def _set_inherited_templates(self, val):
        return
    inherited_templates = property(_get_inherited_templates, _set_inherited_templates)

    def _copySelf(self, target):
        return target.add(self.class_name, self.inheritance_only, self.inherited_templates)

class DeviceTemplate(BaseTemplate):
    class_id = 'DTMPL'
    class_name = 'device template'

class NetworkTemplate(BaseTemplate):
    class_id = 'NTMPL'
    class_name = 'network template'

class TemplateRulePassword(treenodes.BaseNode):
    class_id = 'TMPLRULEPASSWORD'
    class_name = 'template rule password'
    class_data_len = 3
    apply_arguments = 1

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

    def _copySelf(self, target):
        return target.add(self.class_name, self.username, self.description, self.key)

class TemplateRuleAssignNetwork(treenodes.BaseNode):
    class_id = 'TMPLRULEASSIGNNET'
    class_name = 'template rule assign network'
    class_data_len = 0
    apply_arguments = 0

    def __init__(self, parent):
        super(TemplateRuleAssignNetwork, self).__init__(parent)

    def _loaded(self, node_data):
        super(TemplateRuleAssignNetwork, self)._loaded(node_data)

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid)

    def _copySelf(self, target):
        return target.add(self.class_name)

class TemplateRuleSubdevice(treenodes.BaseNode):
    class_id = 'TMPLRULESUBDEV'
    class_name = 'template rule subdevice'
    class_data_len = 3
    apply_arguments = 2

    def __init__(self, parent, num_devices = None, device_template = None,
            sequence_offset = None):
        super(TemplateRuleSubdevice, self).__init__(parent)
        self.num_devices = num_devices
        self.device_template = device_template
        self.sequence_offset = sequence_offset

    def _loaded(self, node_data):
        super(TemplateRuleSubdevice, self)._loaded(node_data)
        self.num_devices = node_data['data'][0]
        device_template_oid = node_data['data'][1]
        if len(device_template_oid) > 0:
            self.device_template = self.root.getOID(device_template_oid)
        self.sequence_offset = node_data['data'][2]

    def _created(self):
        """Called when an object has been newly created."""
        device_template_oid = ''
        if self.device_template:
            device_template_oid = self.device_template.oid
        self.oid = self.transport.add(self.parent.oid, self.num_devices,
                device_template_oid, self.sequence_offset)

    def setNumDevices(self, num_devices):
        self.transport.setNumDevices(self.oid, num_devices)
        self.num_devices = num_devices

    def setDeviceTemplate(self, device_template):
        device_template_oid = ''
        if device_template:
            device_template_oid = device_template.oid
        self.transport.setDeviceTemplate(self.oid, device_template_oid)
        self.device_template = device_template

    def setSequenceOffset(self, sequence_offset):
        self.transport.setNumDevices(self.oid, sequence_offset)
        self.sequence_offset = sequence_offset

    def _copySelf(self, target):
        return target.add(self.class_name, self.num_devices, self.device_template, self.sequence_offset)

class TemplateRuleText(treenodes.BaseNode):
    class_id = 'TMPLRULETEXT'
    class_name = 'template rule text'
    class_data_len = 2
    apply_arguments = 1

    def __init__(self, parent, attr_name = None, versions = None):
        super(TemplateRuleText, self).__init__(parent)
        self.attr_name = attr_name
        self.versions = versions

    def _loaded(self, node_data):
        super(TemplateRuleText, self)._loaded(node_data)
        self.attr_name = node_data['data'][0]
        self.versions = node_data['data'][1]

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self.attr_name,
                self.versions)

    def _copySelf(self, target):
        return target.add(self.class_name, self.attr_name, self.versions)

class TemplateRuleFixed(treenodes.BaseNode):
    class_id = 'TMPLRULEFIXED'
    class_name = 'template rule fixed'
    class_data_len = 4
    apply_arguments = 0

    def __init__(self, parent, attr_name = None, value = None,
            variable_expansion = False, versions = None):
        super(TemplateRuleFixed, self).__init__(parent)
        self.attr_name = attr_name
        self.value = value
        self.variable_expansion = variable_expansion
        self.versions = versions

    def _loaded(self, node_data):
        super(TemplateRuleFixed, self)._loaded(node_data)
        self.attr_name = node_data['data'][0]
        self.value = node_data['data'][1]
        self.variable_expansion = node_data['data'][2]
        self.versions = node_data['data'][3]

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self.attr_name,
                self.value, self.variable_expansion, self.versions)

    def _copySelf(self, target):
        return target.add(self.class_name, self.attr_name, self.value, self.variable_expansion, self.versions)

class TemplateRuleRegmatch(treenodes.BaseNode):
    class_id = 'TMPLRULEREGMATCH'
    class_name = 'template rule regmatch'
    class_data_len = 3
    apply_arguments = 1

    def __init__(self, parent, attr_name = None, regexp = None,
            versions = None):
        super(TemplateRuleRegmatch, self).__init__(parent)
        self.attr_name = attr_name
        self.regexp = regexp
        self.versions = versions

    def _loaded(self, node_data):
        super(TemplateRuleRegmatch, self)._loaded(node_data)
        self.attr_name = node_data['data'][0]
        self.regexp = node_data['data'][1]
        self.versions = node_data['data'][2]

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self.attr_name,
                self.regexp, self.versions)

    def _copySelf(self, target):
        return target.add(self.class_name, self.attr_name, self.regexp, self.versions)

class TemplateRuleBool(treenodes.BaseNode):
    class_id = 'TMPLRULEBOOL'
    class_name = 'template rule bool'
    class_data_len = 3
    apply_arguments = 1

    def __init__(self, parent, attr_name = None, default_value = None,
            versions = None):
        super(TemplateRuleBool, self).__init__(parent)
        self.attr_name = attr_name
        self.default_value = default_value
        self.versions = versions

    def _loaded(self, node_data):
        super(TemplateRuleBool, self)._loaded(node_data)
        self.attr_name = node_data['data'][0]
        self.default_value = node_data['data'][1]
        self.versions = node_data['data'][2]

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self.attr_name,
                self.default_value, self.versions)

    def _copySelf(self, target):
        return target.add(self.class_name, self.attr_name, self.default_value, self.versions)

class TemplateRuleInt(treenodes.BaseNode):
    class_id = 'TMPLRULEINT'
    class_name = 'template rule int'
    class_data_len = 3
    apply_arguments = 1

    def __init__(self, parent, attr_name = None, default_value = None,
            versions = None):
        super(TemplateRuleInt, self).__init__(parent)
        self.attr_name = attr_name
        self.default_value = default_value
        self.versions = versions

    def _loaded(self, node_data):
        super(TemplateRuleInt, self)._loaded(node_data)
        self.attr_name = node_data['data'][0]
        self.default_value = node_data['data'][1]
        self.versions = node_data['data'][2]

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self.attr_name,
                self.default_value, self.versions)

    def _copySelf(self, target):
        return target.add(self.class_name, self.attr_name, self.default_value, self.versions)

class TemplateRuleDeleteAttribute(treenodes.BaseNode):
    class_id = 'TMPLRULEDELATTR'
    class_name = 'template rule delete attribute'
    class_data_len = 1
    apply_arguments = 0

    def __init__(self, parent, attr_name = None):
        super(TemplateRuleDeleteAttribute, self).__init__(parent)
        self.attr_name = attr_name

    def _loaded(self, node_data):
        super(TemplateRuleDeleteAttribute, self)._loaded(node_data)
        self.attr_name = node_data['data'][0]

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self.attr_name)

    def _copySelf(self, target):
        return target.add(self.class_name, self.attr_name)

class TemplateRuleFlushNodes(treenodes.BaseNode):
    class_id = 'TMPLRULEFLUSHNODES'
    class_name = 'template rule flush nodes'
    class_data_len = 2
    apply_arguments = 0

    def __init__(self, parent, include = None, exclude = None):
        super(TemplateRuleFlushNodes, self).__init__(parent)
        self.include = include
        self.exclude = exclude

    def _loaded(self, node_data):
        super(TemplateRuleFlushNodes, self)._loaded(node_data)
        self.include = node_data['data'][0]
        self.exclude = node_data['data'][1]

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self.include,
                self.exclude)

    def _copySelf(self, target):
        return target.add(self.class_name, self.include, self.exclude)

class TemplateRuleFlushAssociations(treenodes.BaseNode):
    class_id = 'TMPLRULEFLUSHASSOC'
    class_name = 'template rule flush associations'
    class_data_len = 2
    apply_arguments = 0

    def __init__(self, parent, include = None, exclude = None):
        super(TemplateRuleFlushAssociations, self).__init__(parent)
        self.include = include
        self.exclude = exclude

    def _loaded(self, node_data):
        super(TemplateRuleFlushAssociations, self)._loaded(node_data)
        self.include = node_data['data'][0]
        self.exclude = node_data['data'][1]

    def _created(self):
        """Called when an object has been newly created."""
        self.oid = self.transport.add(self.parent.oid, self.include,
                self.exclude)

    def _copySelf(self, target):
        return target.add(self.class_name, self.include, self.exclude)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(DeviceTemplate)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(TemplateRulePassword)
o.registerChild(TemplateRuleAssignNetwork)
o.registerChild(TemplateRuleSubdevice)
o.registerChild(TemplateRuleText)
o.registerChild(TemplateRuleFixed)
o.registerChild(TemplateRuleRegmatch)
o.registerChild(TemplateRuleBool)
o.registerChild(TemplateRuleInt)
o.registerChild(TemplateRuleDeleteAttribute)
o.registerChild(TemplateRuleFlushNodes)
o.registerChild(TemplateRuleFlushAssociations)

o = object_registry.registerClass(NetworkTemplate)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(TemplateRuleText)
o.registerChild(TemplateRuleFixed)
o.registerChild(TemplateRuleRegmatch)
o.registerChild(TemplateRuleBool)
o.registerChild(TemplateRuleInt)
o.registerChild(TemplateRuleDeleteAttribute)
o.registerChild(TemplateRuleFlushNodes)
o.registerChild(TemplateRuleFlushAssociations)

o = object_registry.registerClass(TemplateRulePassword)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleAssignNetwork)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleSubdevice)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleText)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleFixed)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleRegmatch)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleBool)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleInt)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleDeleteAttribute)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleFlushNodes)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleFlushAssociations)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

