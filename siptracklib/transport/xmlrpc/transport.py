"""A siptrack xmlrpc transport.

Used for communicating with siptrack servers via xmlrpc.
"""
import xmlrpclib
import socket
import time

from siptracklib.errors import SiptrackError, AlreadyExists, NonExistent, InvalidLocation
import siptracklib.errors

from siptracklib.transport.xmlrpc import root
from siptracklib.transport.xmlrpc import container
from siptracklib.transport.xmlrpc import attribute
from siptracklib.transport.xmlrpc import counter
from siptracklib.transport.xmlrpc import device
from siptracklib.transport.xmlrpc import network
from siptracklib.transport.xmlrpc import password
from siptracklib.transport.xmlrpc import view
from siptracklib.transport.xmlrpc import user
from siptracklib.transport.xmlrpc import template
from siptracklib.transport.xmlrpc import confignode
from siptracklib.transport.xmlrpc import permission
from siptracklib.transport.xmlrpc import event
from siptracklib.transport.xmlrpc import option

transport_class_id_mapping = {
        'CT'  : ['container', 'tree'],
        'C'   : ['container'],
        'CNT' : ['counter'],
        'CNTLOOP' : ['counter', 'loop'],
        'DT'  : ['device', 'tree'],
        'DC'  : ['device', 'category'],
        'D'   : ['device'],
        'OT'  : ['option', 'tree'],
        'OC'  : ['option', 'category'],
        'OV'  : ['option', 'value'],
        'O'   : ['option'],
        'TMPL'  : ['template'],
        'DTMPL'  : ['template', 'device'],
        'NTMPL'  : ['template', 'network'],
        'TMPLRULE'  : ['template', 'rule'],     # Nothing actually exists here..
        'TMPLRULEPASSWORD'  : ['template', 'rule', 'password'],
        'TMPLRULEASSIGNNET'  : ['template', 'rule', 'assign_network'],
        'TMPLRULESUBDEV'  : ['template', 'rule', 'subdevice'],
        'TMPLRULETEXT'  : ['template', 'rule', 'text'],
        'TMPLRULEFIXED'  : ['template', 'rule', 'fixed'],
        'TMPLRULEREGMATCH'  : ['template', 'rule', 'regmatch'],
        'TMPLRULEBOOL'  : ['template', 'rule', 'bool'],
        'TMPLRULEINT'  : ['template', 'rule', 'int'],
        'TMPLRULEDELATTR'  : ['template', 'rule', 'delete_attribute'],
        'TMPLRULEFLUSHNODES'  : ['template', 'rule', 'flush_nodes'],
        'TMPLRULEFLUSHASSOC'  : ['template', 'rule', 'flush_associations'],
        'P'   : ['password'],
        'PK'  : ['password', 'key'],
        'SK'  : ['password', 'subkey'],
        'PT'  : ['password', 'tree'],
        'PC'  : ['password', 'category'],
        'U'   : ['user', 'local'],
        'UL'  : ['user', 'ldap'],
        'UAD'  : ['user', 'ad'],
        'UM'  : ['user', 'manager', 'local'],
        'UML' : ['user', 'manager', 'ldap'],
        'UMAD' : ['user', 'manager', 'ad'],
        'UG'  : ['user', 'group'],
        'UGL'  : ['user', 'group', 'ldap'],
        'UGAD'  : ['user', 'group', 'ad'],
        'VT'  : ['view', 'tree'],
        'V'   : ['view'],
        'NT'  : ['network', 'tree'],
        'IP4N'  : ['network', 'ipv4'],
        'IP4NR'  : ['network', 'range', 'ipv4'],
        'IP6N'  : ['network', 'ipv6'],
        'IP6NR'  : ['network', 'range', 'ipv6'],
        'CA'  : ['attribute'],
        'VA'  : ['attribute', 'versioned'],
        'CFGS'  : ['config', 'section'],
        'CFGNETAUTO'  : ['config', 'network_autoassign'],
        'CFGVALUE'  : ['config', 'value'],
        'PERM'   : ['permission'],
        'C'   : ['command'],
        'CQ'   : ['command', 'queue'],
        'ET'   : ['event', 'trigger'],
        'ETRP'   : ['event', 'trigger', 'rule', 'python'],
        }

class Transport(object):
    """A siptrack xmlrpc transport.

    Used for communicating with siptrack servers via xmlrpc.
    XMLRPCTransport is the base class that should be used in communcation.
    It contains a number of methods that should be used to speak with the
    siptrack server.

    A connection is not made to the server when this class is instantiated.
    instance.connect() must be used to connect to the server, before any
    commands are sent.
    """
    def __init__(self, hostname = None, port = None, use_ssl = None):
        self.hostname = hostname
        self.port = port
        self.use_ssl = use_ssl
        self._connection = None
        self.session_id = None
        self.username = None
        self.password = None
        self.debug = False

        self.cmd = root.RootRPC(self)
        self.cmd.container = container.ContainerRPC(self)
        self.cmd.container.tree = container.ContainerTreeRPC(self)
        self.cmd.counter = counter.CounterRPC(self)
        self.cmd.counter.loop = counter.CounterLoopRPC(self)
        self.cmd.device = device.DeviceRPC(self)
        self.cmd.device.tree = device.DeviceTreeRPC(self)
        self.cmd.device.category = device.DeviceCategoryRPC(self)
        self.cmd.template = template.TemplateRPC(self)
        self.cmd.template.device = template.DeviceTemplateRPC(self)
        self.cmd.template.network = template.NetworkTemplateRPC(self)
        self.cmd.template.rule = template.TemplateRuleRPC(self)
        self.cmd.template.rule.password = template.TemplateRulePasswordRPC(self)
        self.cmd.template.rule.assign_network = template.TemplateRuleAssignNetworkRPC(self)
        self.cmd.template.rule.subdevice = template.TemplateRuleSubdeviceRPC(self)
        self.cmd.template.rule.text = template.TemplateRuleTextRPC(self)
        self.cmd.template.rule.fixed = template.TemplateRuleFixedRPC(self)
        self.cmd.template.rule.regmatch = template.TemplateRuleRegmatchRPC(self)
        self.cmd.template.rule.bool = template.TemplateRuleBoolRPC(self)
        self.cmd.template.rule.int = template.TemplateRuleIntRPC(self)
        self.cmd.template.rule.delete_attribute = template.TemplateRuleDeleteAttributeRPC(self)
        self.cmd.template.rule.flush_nodes = template.TemplateRuleFlushNodesRPC(self)
        self.cmd.template.rule.flush_associations = template.TemplateRuleFlushAssociationsRPC(self)
        self.cmd.password = password.PasswordRPC(self)
        self.cmd.password.key = password.PasswordKeyRPC(self)
        self.cmd.password.subkey = password.SubKeyRPC(self)
        self.cmd.password.tree = password.PasswordTreeRPC(self)
        self.cmd.password.category = password.PasswordCategoryRPC(self)
        self.cmd.option = user.OptionRPC(self)
        self.cmd.option.tree = user.OptionTreeRPC(self)
        self.cmd.option.category = user.OptionCategoryRPC(self)
        self.cmd.option.value = user.OptionValueRPC(self)
        self.cmd.user = user.UserRPC(self)
        self.cmd.user.local = user.UserLocalRPC(self)
        self.cmd.user.ldap = user.UserLDAPRPC(self)
        self.cmd.user.ad = user.UserActiveDirectoryRPC(self)
        self.cmd.user.manager = user.UserManagerRPC(self)
        self.cmd.user.manager.local = user.UserManagerLocalRPC(self)
        self.cmd.user.manager.ldap = user.UserManagerLDAPRPC(self)
        self.cmd.user.manager.ad = user.UserManagerActiveDirectoryRPC(self)
        self.cmd.user.group = user.UserGroupRPC(self)
        self.cmd.user.group.ldap = user.UserGroupLDAPRPC(self)
        self.cmd.user.group.ad = user.UserGroupActiveDirectoryRPC(self)
        self.cmd.view = view.ViewRPC(self)
        self.cmd.view.tree = view.ViewTreeRPC(self)
        self.cmd.network = network.NetworkRPC(self)
        self.cmd.network.tree = network.NetworkTreeRPC(self)
        self.cmd.network.ipv4 = network.NetworkIPV4RPC(self)
        self.cmd.network.ipv6 = network.NetworkIPV6RPC(self)
        self.cmd.network.range = network.NetworkRangeRPC(self)
        self.cmd.network.range.ipv4 = network.NetworkRangeIPV4RPC(self)
        self.cmd.network.range.ipv6 = network.NetworkRangeIPV6RPC(self)
        self.cmd.attribute = attribute.AttributeRPC(self)
        self.cmd.attribute.versioned = attribute.VersionedAttributeRPC(self)
        self.cmd.config = confignode.ConfigRPC(self)
        self.cmd.config.section = confignode.ConfigSectionRPC(self)
        self.cmd.config.network_autoassign = confignode.ConfigNetworkAutoassignRPC(self)
        self.cmd.config.value = confignode.ConfigValueRPC(self)
        self.cmd.permission = permission.PermissionRPC(self)
        self.cmd.command = event.CommandRPC(self)
        self.cmd.command.queue = event.CommandQueueRPC(self)
        self.cmd.event = event.EventRPC(self)
        self.cmd.event.trigger = event.EventTriggerRPC(self)
        self.cmd.event.trigger.rule = event.EventTriggerRuleRPC(self)
        self.cmd.event.trigger.rule.python = event.EventTriggerRulePythonRPC(self)

    def _sendCommand(self, command, *args):
        """Send a command to the siptrack server, with error handling.
        
        Sends a command to the server and does some basic error
        conversion. Ie. based on xmlrpc fault codes different siptrack
        exceptions are raised.
        If an unhandled fault code is encountered the exception is
        re-raised.
        """
        try:
            # You're really supposed to call the server command by doing:
            # self._connection.command(args), but that's sort of hard here.
            start = time.time()
            ret = getattr(self._connection, command)(*args)
            end = time.time()
            if self.debug:
                print 'RPC CALL %s: %s' % (command, end - start)
            return ret
        except xmlrpclib.Fault, e:
            faultcode = e.faultCode
            faultstring = e.faultString
            # Generic error.
            if faultcode == 1:
                raise SiptrackError(faultstring)
            # Invalid session ID.
            elif faultcode == 99:
                raise SiptrackError('Invalid session id.')
            # Generic client error (invalid input etc).
            elif faultcode == 101:
                raise SiptrackError('CLIENT ERROR: %s' % (faultstring))
            # Object already exists error.
            elif faultcode == 102:
                raise AlreadyExists(faultstring)
            # Object doesn't exist error.
            elif faultcode == 103:
                raise NonExistent(faultstring)
            # Invalid location error.
            elif faultcode == 104:
                raise InvalidLocation(faultstring)
            # Invalid username/password for login.
            elif faultcode == 105:
                raise siptracklib.errors.InvalidLoginError(faultstring)
            elif faultcode == 106:
                raise siptracklib.errors.PermissionDenied(faultstring)
            # Twisted xmlrpc error codes.
            elif faultcode in [8001, 8002]:
                raise SiptrackError('XMLRPC ERROR: %s' % (faultstring))
            # If the predefined error codes didn't match, the server
            # probably had problems of some kind.
            else:
                raise

    def section(self, class_id):
        """Return the transport section matching the given class_id."""
        if class_id not in transport_class_id_mapping:
            return self.cmd
        section_ids = transport_class_id_mapping[class_id]
        section = self.cmd
        for section_id in section_ids:
            section = getattr(section, section_id)
        return section

    def connect(self, username = None, password = None, session_id = None,
            verify_session_id = False):
        """Connect to the server."""
        # encoding in xmlrpclib defaults to utf-8.
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        if self.use_ssl:
            scheme = 'https'
        else:
            scheme = 'http'
        connect_string = '%s://%s:%s/' % (scheme, self.hostname, self.port)
        self._connection = xmlrpclib.ServerProxy(connect_string)
        try:
            if session_id:
                self.session_id = session_id
                if verify_session_id:
                    # hello returns 0 for invalid session ids.
                    if self.cmd.hello() == 0:
                        self.session_id = None
            if not self.session_id:
                if self.username is None or self.password is None:
                    raise siptracklib.errors.InvalidLoginError()
                self.cmd.login(self.username, self.password)
        except socket.error, e:
            raise SiptrackError('Unable to connect to siptrack server: %s' % (
                e.args[1]))
        except socket.gaierror, e:
            raise SiptrackError('Unable to connect to siptrack server: %s' % (
                e.args[1]))
        return self.session_id

    def reconnect(self):
        self.session_id = None
        self.session_id = self.connect()

    def disconnect(self):
        """ Disconnect from the server.

        Ends the current session and resets the connection.
        """
        if self._connection is None:
            return
        self.cmd.logout()
        self._connection = None

    def _makeBinary(self, string):
        """Create a binary object for sending with xmlrpclib."""
        return xmlrpclib.Binary(string)

