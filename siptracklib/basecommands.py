"""Basic command definitions.

Commands are all subclasses of the Command object. They can contain:
aliases   - list of string with command aliases.
options   - list of Option objects, the commands commandline options.
arguments - list of Argument objects, the commands commandline arguments.
a 'run' method, this is called with the options/arguments that are defined
as regular method parameters.

The class docstring is used as the help output for the command.

Underscores ('_') in class names are converted to dashes ('-') in the
actual commands for the user. Similarly, dashes in option names are
converted to underscores before being sent to the run method.
"""

# NOTE:
# Evidently xmlrpclib converts incoming strings first to unicode, then to
# plain ascii strings if possible. We want unicode all over, so we need to
# check if inbound arguments are regular strings, and convert them to unicode
# if they are, and it's necessary.

from __future__ import print_function

import os
import sys
import subprocess

import siptracklib
from siptracklib.commands import Command, Option, Argument
from siptracklib.errors import SiptrackError, SiptrackCommandError
from siptracklib.utils import (cprint, read_password, object_by_attribute,
        fetch_device_path)
from siptracklib import cmdconnect
from siptracklib import utils
from siptracklib import errors

def show_version():
    """Print program version information."""
    cprint('siptrack %s' % (siptracklib.__version__))
    cprint('Written by Simon Ekstrand.')
    cprint('')
    cprint(siptracklib.__copyright__)

class cmd_version(Command):
    """Display version information."""
    aliases = ['ver']
    connected = False

    def run(self):
        show_version()

        return 0

class cmd_help(Command):
    """Display general help or help on a specific command.

    Use 'siptrack help commands' for a list of all commands.
    """
    aliases = ['?']
    arguments = [
        Argument('topic', optional = True, help = 'Help for a specific topic.')
    ]
    connected = False

    def run(self, topic = None):
        from siptracklib import help
        if not topic:
            help.show_global_help()
        else:
            help.show_topic_help(topic)

        return 0

class cmd_ping(Command):
    """Send a transport ping to the server.

    The returned value is a current local unix timestamp from the server.
    """

    def run(self):
        cprint('Server said: %s' % (self.transport.cmd.ping()))

        return 0

class cmd_oid_type(Command):
    """Show what class type a node is."""
    
    arguments = [
        Argument('oid', help = 'The id of node to move.'),
    ]

    def run(self, oid):
        node = self.object_store.getOID(oid)

        cprint(node.class_name)

        return 0

class cmd_grep(Command):
    """Find devices."""
    aliases = ['rgrep', 'search']
    arguments = [
        Argument('searchstring', help = 'Searchstring.'),
    ]
    options = [
        Option('password', 'p', take_argument = False,
                help = 'Display only first matched password.\n    Enables using <user@>searchstring.'),
        Option('show-hidden', 'H', take_argument = False,
                help = 'Show hidden settings.'),
        Option('search-all', 'a', take_argument = False,
                help = 'Search all attributes and networks (default is to only search devices names).'),
        Option('regexp', 'r', take_argument = False,
                help = 'Use regexp search, slower (automatically used with -a).'),
        Option('max-results', 'm', take_argument = True,
                help = 'Max returned results, default 500.'),
    ]

    def _displayAttributes(self, device, show_hidden):
        if len(device.attributes) > 0:
            for attr in device.attributes:
                if not show_hidden and attr.attributes.get('hidden', False) is True:
                    continue
                if attr.atype == 'text' and len(attr.value.strip()) == 0:
                    continue
                cprint('%-20s %s' % (attr.name.lower() + ':', attr.value))
            print

    def _displayNetworks(self, device):
        networks = [str(network) for network in device.listNetworks(include_ranges=False, include_interfaces=True)]
        if len(networks) > 0:
            cprint('IP-addresses:')
            cprint('  %s' % (' '.join(networks)))
            print

    def _calcPasswordColumnWidths(self, passwords):
        l_username = 20
        l_description = 20
        l_password = 30
        for password in passwords:
            if len(password.attributes.get('username', '')) > l_username:
                l_username = len(password.attributes.get('username'))
            if len(password.attributes.get('description', '')) > l_description:
                l_description = len(password.attributes.get('description'))
            if len(password.password) > l_password:
                l_password = len(password.password)
        return l_username, l_description, l_password

    def _displayPasswords(self, device):
        passwords = list(device.listChildren(include = ['password']))
        if len(passwords) > 0:
            l_username, l_description, l_password = self._calcPasswordColumnWidths(passwords)
            sep_str = '  +%s+%s+%s+' % ('-' * l_username, '-' * l_description, '-' * l_password)
            out_str_fmt = '  |%%-%ds|%%-%ds|%%-%ds|' % (l_username, l_description, l_password)
            print('Passwords:')
            print(sep_str)
            print(out_str_fmt % ('username', 'description',
                    'password'))
            print(sep_str)
            for password in passwords:
                print(out_str_fmt % (
                        password.attributes.get('username', ''),
                        password.attributes.get('description', ''),
                        password.password))
            print(sep_str)
            print()

    def _displayUserPassword(self, username, device):
        passwords = list(device.listChildren(include = ['password']))
        if not username and len(passwords) > 1:
            raise errors.SiptrackError('matched to many passwords')
        for password in passwords:
            if password.attributes.get('username') == username:
                print(password.password)
                break

    def _displayAssociatedDevices(self, device):
        assoc_devices = device.listAssociations(include = ['device'])
        assoc_devices += device.listReferences(include = ['device'])
        if len(assoc_devices) > 0:
            cprint('Associated devices:')
            for node in assoc_devices:
                node_path = []
                cur = node
                while cur.class_name == 'device':
                    node_path.insert(0, cur)
                    cur = cur.parent
                names = [n.attributes.get('name', 'UNKNOWN') for n in node_path]
                cprint('  %15s: %s' % (node.attributes.get('class', ' - '),
                    ' / '.join(names)))

            print()
    
    def _displayDisabled(self, device):
        if device.attributes.get('disabled', False) is True:
            cprint('THIS DEVICE IS CURRENTLY DISABLED')

    def run(self, searchstring, password = False, show_hidden = False,
            search_all = False, regexp = False, max_results = 500):
        self.transport.cmd.setSessionTimeout(60 * 60) # One hour.
        if search_all:
            regexp = True
        attr_limit = []
        if not search_all:
            attr_limit = ['name']
        username = None
        if password:
            if '@' in searchstring:
                username, searchstring = searchstring.split('@', 1)
        devices = utils.search_device(self.object_store, searchstring,
                attr_limit, not regexp, max_results)
        if password:
            if len(devices) == 0:
                raise errors.SiptrackError('no devices matched')
            if len(devices) > 1:
                raise errors.SiptrackError('matched to many devices')
            device = devices[0]
            self._displayUserPassword(username, device)
        else:
            device = utils.select_device_from_list(devices)
            self._displayDisabled(device)
            self._displayAttributes(device, show_hidden)
            self._displayNetworks(device)
            self._displayAssociatedDevices(device)
            self._displayPasswords(device)

class cmd_list_tree(Command):
    """Show the whole object tree."""
    options = [
        Option('display-attributes', 'a', take_argument = False,
                help = 'Display attributes.')
    ]

    def run(self, display_attributes = False):
        self.view_tree.fetch(max_depth = -1)
        exclude = ['attribute']
        if display_attributes:
            exclude = []
        for depth, node in self.view_tree.traverse(exclude = exclude,
                include_depth = True):
            cprint('%s%s' % (depth * '    ', node.describe()))

        return 0

class cmd_json_dump_tree(Command):
    """Dump a json representation of the whole object tree."""

    def run(self):
        import json
        self.view_tree.fetch(max_depth = -1)
        data = []
        for depth, node in self.view_tree.traverse(include_depth = True):
            data.append(node.dictDescribe())
        cprint(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))
        return 0

class cmd_cmp_json_dumps(Command):
    """Compare two dumped json trees."""

    arguments = [
        Argument('file1',
            help = 'JSON dump file.'),
        Argument('file2',
            help = 'JSON dump file.'),
    ]

    def run(self, file1, file2):
        import json
        import time
        data_1 = json.loads(open(file1, 'r').read())
        oids_1 = {}
        for n in data_1:
            oids_1[n['oid']] = n
#        oids_1 = {n['oid']: n for n in data_1}
        data_2 = json.loads(open(file2, 'r').read())
        oids_2 = {}
        for n in data_2:
            oids_2[n['oid']] = n
#        oids_2 = {n['oid']: n for n in data_2}
        print(len(oids_1), len(oids_2))
        for oid, node in oids_1.iteritems():
            if oid not in oids_2:
                print('IN 1', oid, node['cls'], time.ctime(node['ctime']))
        for oid, node in oids_2.iteritems():
            if oid not in oids_1:
                print('IN 2', oid, node['cls'], time.ctime(node['ctime']))
        return 0

class cmd_connect(Command):
    """SSH/RDP connection to a device."""
    connected = True
    arguments = [
        Argument('device',
            help = 'The device to connect to, can include an optional [username@].'),
    ]
    options = [
        Option('search-all', 'a', take_argument = False,
                help = 'Search all attributes and networks (default is to only search devices names).'),
        Option('console', '0', take_argument = False,
                help = 'Attach to console for rdp connections.'),
        Option('regexp', 'r', take_argument = False,
                help = 'Use regexp search, slower (automatically used with -a).'),
    ]

    def run(self, device, search_all = False, console = False, regexp = False):
        if search_all:
            regexp = True
        cmdconnect.cmd_connect(self.object_store,
                device, search_all, not regexp, console, self.cm.config)

        return 0

class cmd_gtkconnect(Command):
    """GTK SSH/RDP connection to a device."""
    connected = False
    options = [
        Option('daemonize', 'd', take_argument = False,
                help = 'Run this siptrack/gtkconnect instance in the background.')
    ]

    def run(self, daemonize = False):
        try:
            import pygtk
        except ImportError:
            raise errors.SiptrackError('pygtk >= 2.0 required')
        try:
            pygtk.require('2.0')
        except AssertionError:
            raise errors.SiptrackError('pygtk >= 2.0 required')
        import cmdgtkconnect
        cmdgtkconnect.cmd_gtkconnect(self.cm, daemonize)

        return 0

class cmd_connect_fork(Command):
    """SSH/RDP connection to a device.
    
    This command is used by cmd_connect when a unix ssh connection has
    been requested in a new terminal.
    """
    connected = False
    hidden = True
    arguments = [
        Argument('username',
            help = 'Username used to connect to the device.'),
        Argument('hostname',
            help = 'Hostname of the device being connected to.'),
        Argument('pid',
            help = 'The pid of the calling process.'),
        Argument('ssh',
            help = 'Path to ssh binary.'),
    ]

    def run(self, username, hostname, pid, ssh):
        cmdconnect.cmd_connect_fork(username, hostname, pid, ssh)

        return 0

class cmd_edit_config(Command):
    """Open an editor for the siptrack config file."""
    connected = False
    unix_editor_path = ['/etc/alternatives/editor',
            '/etc/alternatives/editor']
    windows_editor_path = [os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'notepad.exe'),
                           os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'system32', 'notepad.exe')]

    def _getEditor(self, editor_paths):
        editor = None
        if not editor:
            editor = os.environ.get('EDITOR', None)
        for path in editor_paths:
            if editor:
                break
            if os.path.exists(path):
                editor = path
        return editor

    def _callEdit(self, editor_paths):
        editor = self._getEditor(editor_paths)
        if not editor:
            print('No editor found.')
            return
        editorcmd = [editor, utils.get_user_config_file()]
        subprocess.Popen(editorcmd)

    def run(self):
        if sys.platform == 'win32':
            self._callEdit(self.windows_editor_path)
        else:
            self._callEdit(self.unix_editor_path)
        return 0

class cmd_show_config(Command):
    """Display which configuration files siptrack is using."""
    connected = False

    def run(self):
        print(' '.join(utils.get_default_config_files()))

        return 0

class cmd_show_config_var(Command):
    """Display a siptrack config variable."""
    connected = False
    hidden = True
    options = [
        Option('section', 's', take_argument = True,
            help = 'Config section (default: DEFAULT).')
    ]
    arguments = [
        Argument('variable',
            help = 'Config variable.'),
    ]

    def run(self, variable, section = 'DEFAULT'):
        print(self.cm.config.get(variable, sections = [section]))
        return 0

class cmd_copy_password_clipboard(Command):
    """Copy a devices password to the clipboard."""
    connected = True
    aliases = ['cc']
    arguments = [
        Argument('device',
            help = 'The device to search for, can include an optional [username@].'),
    ]
    options = [
        Option('search-all', 'a', take_argument = False,
                help = 'Search all attributes and networks (default is to only search devices names).'),
        Option('regexp', 'r', take_argument = False,
                help = 'Use regexp search, slower (automatically used with -a).'),
    ]

    def run(self, device, search_all = False, regexp = False):
        if search_all:
            regexp = True
        cmdconnect.cmd_copy_password_clipboard(self.object_store,
                device, search_all, not regexp, self.cm.config)

        return 0

class cmd_get_device_config(Command):
    """Get a device configuration."""
    connected = True
    aliases = []
    arguments = [
        Argument('device_name',
            help = 'The device.'),
        Argument('config_name',
            help = 'Configuration name.'),
    ]
    options = [
        Option('timestamp', 't', take_argument = True,
                help = 'Fetch config for a specific timestamp, otherwise fetches latest'),
    ]

    def run(self, device_name, config_name, timestamp = None):
        devices = self.object_store.search(device_name, include=['device'], attr_limit=['name'])
        if len(devices) == 0:
            raise errors.SiptrackError('no devices matched')
        if len(devices) > 1:
            raise errors.SiptrackError('matched to many devices')
        device = devices[0]
        match = None
        for config in device.listChildren(include=['device config']):
            if config.name == config_name:
                match = config
                break
        if not match:
            raise errors.SiptrackError('matched device but no config with that name found')
        if timestamp:
            res = config.getTimestampConfig(int(timestamp))
        else:
            res = config.getLatestConfig()
            if res:
                res, _ = res
        if not res:
            raise errors.SiptrackError('no config data submitted')
        print(res)
        return 0

class cmd_submit_device_config(Command):
    """Submit a device configuration. Reads data from stdin."""
    connected = True
    aliases = []
    arguments = [
        Argument('device_name',
            help = 'The device.'),
        Argument('config_name',
            help = 'Configuration name.'),
    ]

    def _getSTDINData(self):
        ret = ''
        for data in sys.stdin.read():
            ret += data
        return ret

    def run(self, device_name, config_name):
        devices = self.object_store.search(device_name, include=['device'], attr_limit=['name'])
        if len(devices) == 0:
            raise errors.SiptrackError('no devices matched')
        if len(devices) > 1:
            raise errors.SiptrackError('matched to many devices')
        device = devices[0]
        match = None
        for config in device.listChildren(include=['device config']):
            if config.name == config_name:
                match = config
                break
        if not match:
            config = device.add('device config', config_name, 50)
        data = self._getSTDINData()
        config.addConfig(data)
        return 0


class cmd_list(Command):
    """List devices."""

    aliases = []
    arguments = [
        Argument('searchstring', help = 'Searchstring.'),
    ]
    options = [
        Option('search-all', 'a', take_argument = False,
                help = 'Search all attributes and networks (default is to only search devices names).'),
        Option('regexp', 'r', take_argument = False,
                help = 'Use regexp search, slower (automatically used with -a).'),
        Option('max-results', 'm', take_argument = True,
                help = 'Max returned results, default 500.'),
    ]


    def run(self, searchstring, **kw):
        search_all = kw.get('search_all', False)
        regexp = kw.get('regexp', False)
        max_results = kw.get('max_results', 500)

        attr_limit = []
        if not search_all:
            attr_limit = ['name']
        else:
            regexp = True

        devices = utils.search_device(
            self.object_store,
            searchstring,
            attr_limit,
            regexp,
            max_results
        )

        for device in devices:
            print('{device_name}'.format(
                device_name=device.attributes.get('name', '[UNNAMED]')
            ))