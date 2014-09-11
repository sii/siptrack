from siptracklib.transport.xmlrpc import baserpc

class TemplateRPC(baserpc.BaseRPC):
    command_path = 'template'

    def suggestTemplates(self, base_oid, template_type):
        return self.send('suggest_templates', base_oid, template_type)

class BaseTemplateRPC(baserpc.BaseRPC):
    command_path = 'template' # Override in subclass.

    def add(self, parent_oid, template_type, inherited_templates):
        return self.send('add', parent_oid, template_type,
                inherited_templates)

    def apply(self, oid, apply_oid, arguments, overwrite, skip_rules):
        return self.send('apply', oid, apply_oid, arguments, overwrite,
                skip_rules)

    def combinedRules(self, oid):
        return self.send('combined_rules', oid)

    def suggestTemplates(self, base_oid, template_type):
        return self.send('suggest_templates', base_oid, template_type)

    def setTemplateType(self, oid, template_type):
        return self.send('set_template_type', oid,
                template_type)

    def setInheritanceOnly(self, oid, inheritance_only):
        return self.send('set_inheritance_only', oid, inheritance_only)

    def setInheritedTemplates(self, oid, inherited_templates):
        return self.send('set_inherited_templates', oid, inherited_templates)

class DeviceTemplateRPC(BaseTemplateRPC):
    command_path = 'template.device' # Override in subclass.

class NetworkTemplateRPC(BaseTemplateRPC):
    command_path = 'template.network' # Override in subclass.

class TemplateRuleRPC(baserpc.BaseRPC):
    command_path = 'template.rule'

class TemplateRulePasswordRPC(baserpc.BaseRPC):
    command_path = 'template.rule.password'

    def add(self, parent_oid, username, description, key_oid):
        return self.send('add', parent_oid, username, description, key_oid)

class TemplateRuleAssignNetworkRPC(baserpc.BaseRPC):
    command_path = 'template.rule.assign_network'

    def add(self, parent_oid):
        return self.send('add', parent_oid)

class TemplateRuleSubdeviceRPC(baserpc.BaseRPC):
    command_path = 'template.rule.subdevice'

    def add(self, parent_oid, num_devices, device_template_oid,
            sequence_offset):
        return self.send('add', parent_oid, num_devices,
                device_template_oid, sequence_offset)

    def setNumDevices(self, oid, num_devices):
        return self.send('set_num_devices', oid, num_devices)

    def setDeviceTemplate(self, device_template_oid):
        return self.send('set_device_template', oid, device_template_oid)

    def setSequenceOffset(self, oid, sequence_offset):
        return self.send('set_sequence_offset', oid, sequence_offset)

class TemplateRuleTextRPC(baserpc.BaseRPC):
    command_path = 'template.rule.text'

    def add(self, parent_oid, attr_name, versions):
        return self.send('add', parent_oid, attr_name, versions)

class TemplateRuleFixedRPC(baserpc.BaseRPC):
    command_path = 'template.rule.fixed'

    def add(self, parent_oid, attr_name, value, variable_expansion, versions):
        return self.send('add', parent_oid, attr_name, value,
                variable_expansion, versions)

class TemplateRuleRegmatchRPC(baserpc.BaseRPC):
    command_path = 'template.rule.regmatch'

    def add(self, parent_oid, attr_name, regexp, versions):
        return self.send('add', parent_oid, attr_name, regexp,
                versions)

class TemplateRuleBoolRPC(baserpc.BaseRPC):
    command_path = 'template.rule.bool'

    def add(self, parent_oid, attr_name, default_value, versions):
        return self.send('add', parent_oid, attr_name, default_value,
                versions)

class TemplateRuleIntRPC(baserpc.BaseRPC):
    command_path = 'template.rule.int'

    def add(self, parent_oid, attr_name, default_value, versions):
        return self.send('add', parent_oid, attr_name, default_value,
                versions)

class TemplateRuleDeleteAttributeRPC(baserpc.BaseRPC):
    command_path = 'template.rule.delete_attribute'

    def add(self, parent_oid, attr_name):
        return self.send('add', parent_oid, attr_name)

class TemplateRuleFlushNodesRPC(baserpc.BaseRPC):
    command_path = 'template.rule.flush_nodes'

    def add(self, parent_oid, include, exclude):
        return self.send('add', parent_oid, include, exclude)

class TemplateRuleFlushAssociationsRPC(baserpc.BaseRPC):
    command_path = 'template.rule.flush_associations'

    def add(self, parent_oid, include, exclude):
        return self.send('add', parent_oid, include, exclude)

