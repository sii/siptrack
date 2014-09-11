from inspect import getdoc
import socket

import siptracklib
from siptracklib.errors import SiptrackError, SiptrackCommandError
from siptracklib.utils import cprint
from siptracklib import utils
from siptracklib import root
from siptracklib import config
from siptracklib import connections

class Argument(object):
    """A class for describing command arguments.

    An argument is considered any commandline argument that isn't prefixed
    with '-' or '--'.

    A command may only have optional and take_many set for it's last argument
    in the argument list.
    """
    def __init__(self, name, optional = False, type = None, help = None):
        self.name = name
        self.optional = optional
        self.type = type
        self.help = help

    def getName(self):
        """The argument name."""
        return self.name

    def isOptional(self):
        """If the argument is optional.

        This is only valid for the last option in the argument list.
        """
        return self.optional

    def getType(self):
        """Return the arguments type.
        
        Valid types are:
        * 'int'
        * 'float'
        * None - undefined
        """
        return self.type

    def getHelp(self):
        """Return the arguments help string."""
        return self.help

class Option(object):
    """A class for describing command options.

    An option is considered any commandline option that's prefixed
    with '-' or '--'.
    """
    def __init__(self, name, short_name = None, take_argument = False,
                 argument_type = None, multishot = False, help = None):
        self.name = name
        self.short_name = short_name
        self.take_argument = take_argument
        self.argument_type = argument_type
        self.help = help
        self.multishot = multishot

    def getName(self):
        """The option name.

        This is the '--' long option.
        """
        return self.name

    def getShortName(self):
        """The option short name.
        
        This is the '-' short option.
        """
        return self.short_name

    def takesArgument(self):
        """Whether or not an option takes an argument.
        
        Valid arguments would be:
        --name argument
        --name=argument
        -n argument
        """
        return self.take_argument

    def getArgumentType(self):
        """Return the arguments type.
        
        Valid types are:
        * int
        * float
        * None - undefined
        """
        return self.argument_type

    def isMultishot(self):
        """Check if this is a multishot option.
        
        If the option takes an argument:
        Multiple arguments given to multishot options are appended to a list
        of arguments rather then giving an error.
        Ie. the option can be given multiple times on the command line, with
        each argument being stored in a list.

        If the option doesn't take an argument:
        If the option has multishot set, each time the option is found on the
        command line a counter is incremented so the command knows how many
        times the option was passed. If multishot isn't set, giving the
        same option multiple times results in an error.
        """
        return self.multishot

    def getHelp(self):
        """Return the arguments help string."""
        return self.help

class Command(object):
    """A default command class.
    
    All commands subclass from this.
    """
    aliases = []
    arguments = []
    options = []
    connected = True
    hidden = False

    def __init__(self, cm = None):
        """Initialize a command object.
        
        Defaulting to None for hostname and port are ok since not all
        commands will be connecting to the server.
        """
        self.name = self.__class__.__name__.lower()[4:].replace('_', '-')
        self.cm = cm
        self.transport = None
        self.object_store = None
        self.view_tree = None

    def parseArgsAndRun(self, args):
        """Parse the given argument list and call the run method."""
        takes_arguments = list(self.arguments)
        takes_options = list(self.options)
        argdict = {}
        while len(args) > 0:
            arg = args.pop(0)
            # If it's an option.
            if len(arg) > 0 and arg[0] == '-':
                # Handle -h, --help specially, so that you can use -h after all
                # commands to get help.
                if arg in ['-h', '--help']:
                    from siptracklib.help import show_topic_help
                    show_topic_help(self.name)
                    return
                parse_option(arg, args, takes_options, argdict)
            # And if it's an argument.
            else:
                parse_argument(arg, args, takes_arguments, argdict)

        if len(takes_arguments) > 1:
            raise SiptrackCommandError('missing required arguments')
        if len(takes_arguments) == 1 and not takes_arguments[0].isOptional():
            raise SiptrackCommandError('missing required arguments')

        if self.connected:
            self.object_store = self.cm.connect()
            self.transport = self.object_store.transport
            self.view_tree = self.object_store.view_tree

        self.run(**argdict)

        self.cm.disconnect()

    def run(self):
        """Run the command itself, must be implemented in a subclass."""
        raise NotImplementedError()

    def getName(self):
        """Return the command name."""
        return self.name

    def help(self):
        """Return the commands help text (docstring of the subclass)."""
        if self.__doc__ is Command.__doc__:
            return "No help available."
        return getdoc(self)

def convert_arg_type(arg, type):
    """Validate an arguments type and return the converted arg.
    
    Type can be one of:
    * 'int'
    * 'float'
    * None - matches anything.

    Raises SiptrackCommandError if the type doesn't match.
    """
    conv = None
    if type == 'int':
        try:
            conv = int(arg)
        except ValueError:
            raise SiptrackError('must be an int')
    elif type == 'float':
        try:
            conv = float(arg)
        except ValueError:
            raise SiptrackError('must be a float')
    elif type is None:
        conv = arg
    else:
        raise SiptrackError('INTERNAL ERROR, unknown type')

    return conv

def parse_option(opt, optlist, valid_opts, optdict):
    """Parses a command option and places it in a dict.
    
    opt - The option string.
    optlist - Subsequent option list after 'opt'.
    valid_opts - List of Option objects.
    optdict - Where the parsed option is placed.

    '-' is converted to '_' in option names before being added to the optdict.
    """
    if len(opt) < 2:
        raise SiptrackCommandError('invalid option')
    if opt[1] == '-':
        option_type = 'long'
        option_name = opt[2:]
    else:
        option_type = 'short'
        option_name = opt[1:]

    option_arg = None
    if option_name.find('=') != -1:
        option_name, option_arg = option_name.split('=', 1)

    match = False
    for option in valid_opts:
        if option_type == 'long' and \
           option.getName() == option_name:
            match = True
            break
        if option_type == 'short' and \
           option.getShortName() == option_name:
            match = True
            break

    if not match:
        raise SiptrackCommandError('unknown option \'%s\'' % option_name)

    convname = option.getName().replace('-', '_')
    if not option.isMultishot() and optdict.has_key(convname):
        raise SiptrackCommandError('option \'%s\' given multiple times.' % (
            option.getName()))

    if not option.takesArgument():
        if optdict.has_key(convname):
            optdict[convname] += 1
        else:
            if option.isMultishot():
                optdict[convname] = 1
            else:
                optdict[convname] = True

    if option.takesArgument():
        if len(optlist) < 1 and not option_arg:
            raise SiptrackCommandError('option \'%s\' requires an argument' % (
                option.getName()))
        if not option_arg:
            option_arg = optlist.pop(0)
        type = option.getArgumentType()
        try:
            arg = convert_arg_type(option_arg, type)
        except SiptrackError, e:
            raise SiptrackCommandError('invalid type for option argument \'%s\': %s' % (
                option_arg, e.__str__()))
        convname = option.getName().replace('-', '_')
        if option.isMultishot():
            if optdict.has_key(convname):
                optdict[convname].append(arg)
            else:
                optdict[convname] = [arg]
        else:
            optdict[convname] = arg

def parse_argument(arg, arglist, valid_args, argdict):
    """Parses a command argument and places it in a dict.
    
    arg - The argument string.
    arglist - Subsequent argument list after 'arg'.
    valid_args - List of Argument objects.
    argdict - Where the parsed argument is placed.
    """
    if len(valid_args) == 0:
        raise SiptrackCommandError('to many arguments given')
    argument = valid_args.pop(0)
    try:
        argdict[argument.getName()] = convert_arg_type(arg, argument.getType())
    except SiptrackError, e:
        raise SiptrackCommandError('invalid type for argument \'%s\': %s' % (
            arg, e.__str__()))

def get_commands():
    """Returns all available commands.
    
    Returns a dict indexed by command name with all available command
    objects (not instances).
    '_' in class names are replaced with '-'.
    """
    import siptracklib.basecommands

    commands = {}
    basecommands = siptracklib.basecommands.__dict__
    for name in basecommands:
        if name.startswith('cmd_'):
            commands[name[4:].replace('_', '-')] = basecommands[name]

    return commands

def get_command(name):
    """Returns the object for the command 'name'."""
    commands = get_commands()
    for command in commands:
        if command == name:
            return commands[name]
        for alias in commands[command].aliases:
            if alias == name:
                return commands[command]
    return None
    
def run_command(cm, command_name, args):
    """See if a command is available and run it.

    hostname - xmlrpc server hostname.
    port - xmlrpc server port.
    command_name - the command to run (string).
    args - list of command arguments.
    """
    commands = get_commands()
    match = None
    for command in commands:
        if command == command_name:
            match = command
        if command_name in commands[command].aliases:
            match = command
        if match:
            break

    if not match:
        raise SiptrackCommandError('command not found')

    command_inst = commands[command](cm)
    return command_inst.parseArgsAndRun(args)

global_options = [
    Option('help', 'h', help = 'Print global help.'),
    Option('version', 'v', help = 'Print version information.'),
    Option('server', 'S', take_argument = True,
        help = 'Connection string [st|sts://][username@]server[:port]'),
    Option('username', 'u', take_argument = True,
        help = 'Username.'),
    Option('password-file', 'p', take_argument = True,
           help = 'File to read password from.'),
]

def run_siptrack(argv):
    """'Siptrack real main'.
    
    Parses global commandline options and runs a command if one was given.
    """
    cm = siptracklib.connection_manager

    optdict = {}

    argv = [arg.decode(siptracklib.user_encoding) for arg in argv]

    while len(argv) > 0:
        if argv[0][0] != '-':
            break
        opt = argv.pop(0)
        parse_option(opt, argv, global_options, optdict)

    if 'help' in optdict:
        from siptracklib.help import show_global_help
        show_global_help()
        return 1
    if 'version' in optdict:
        from siptracklib.basecommands import show_version
        show_version()
        return 1
    if 'server' in optdict:
        server_dict = utils.parse_connection_string(optdict['server'])
        del optdict['server']
        cm.config.update(server_dict)
    cm.config.update(optdict)

    if len(argv) == 0:
        from siptracklib.help import show_global_help
        show_global_help()
        return 1

    return run_command(cm, argv[0], argv[1:])

def main(argv):
    """Main siptracklib commandline client entry point.
    
    This is basically just an exception wrapper for run_siptrack.
    """
    try:
        return run_siptrack(argv[1:])
    except SiptrackCommandError, e:
        cprint('ERROR: %s' % (e))
        return 1
    except SiptrackError, e:
        cprint('ERROR: %s' % (e))
        return 1
    except KeyboardInterrupt:
        cprint('ERROR: command interrupted by user')
#    except Exception, e:
#        cprint('ERROR: %s' % (e))
#        return 1

    return 0
