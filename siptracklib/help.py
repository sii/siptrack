import textwrap

import siptracklib

global_help = \
"""Siptrack IP/Device Manager.
http://www.launchpad.net/siptrack/

Usage: siptrack [global options] command [command options] [command arguments]

Use 'siptrack help commands' for a list of available commands.
"""

def show_global_help():
    """Print global help information."""
    from siptracklib.commands import global_options
    print global_help

    print 'Global options:'
    show_options(global_options)

def show_topic_help(topic):
    """Display help for a given topic.

    'topic' may be a command name or certain other keywords handled
    specifically in this function.
    """
    from siptracklib.commands import get_command
    command = get_command(topic)
    if command is not None:
        show_command_help(topic, command)
        return 0

    if topic == 'commands':
        show_commands()
        return 0

    print 'Topic not found.'
    return 0

def show_commands():
    """Print a list of all available commands."""
    from siptracklib.commands import get_commands

    commands = get_commands()
    for command in commands:
        cmd_inst = commands[command]()
        if cmd_inst.hidden:
            continue

        usage = 'siptrack %s' % (cmd_inst.getName())

        for option in cmd_inst.options:
            usage = '%s --%s' % (usage, option.getName())
            if option.takesArgument():
                arg_type = option.getArgumentType()
                if arg_type is None:
                    usage = '%s=STRING' % (usage)
                else:
                    usage = '%s=%s' % (usage, arg_type.upper())

        for arg in cmd_inst.arguments:
            if arg.isOptional():
                usage = '%s [%s]' % (usage, arg.getName().upper())
            else:
                usage = '%s %s' % (usage, arg.getName().upper())

        print usage

        # Only the first line.
        help = cmd_inst.help().split('\n')[0]
        print '    %s' % (help)
        print

def show_options(options):
    """Print help for a list of Option objects."""
    for option in options:
        out = '  --%s' % (option.getName())
        if option.getShortName():
            out = '%s, -%s' % (out, option.getShortName())
        if option.isMultishot():
            out = '%s [multiple]' % (out)
        print out
        print '    %s' % (option.getHelp())

def show_arguments(args):
    """Print help for a list of Argument objects."""
    for arg in args:
        print '  %s' % (arg.getName()),
        if arg.isOptional():
            print '(optional)',
        print
        print '    %s' % (arg.getHelp())

def show_command_help(topic, command):
    """Print pretty help for a command."""
    cmd_inst = command()

    usage = 'Usage: siptrack %s' % (cmd_inst.getName())

    for option in command.options:
        usage = '%s --%s' % (usage, option.getName())
        if option.takesArgument():
            arg_type = option.getArgumentType()
            if arg_type is None:
                usage = '%s=STRING' % (usage)
            else:
                usage = '%s=%s' % (usage, arg_type.upper())

    for arg in command.arguments:
        if arg.isOptional():
            usage = '%s [%s]' % (usage, arg.getName().upper())
        else:
            usage = '%s %s' % (usage, arg.getName().upper())

    print usage

    if len(command.aliases) > 0:
        aliases = ''
        for alias in command.aliases:
            aliases = '%s, %s' % (aliases, alias)
        aliases = aliases[2:]
        print 'Aliases: %s' % aliases

    print 
    print cmd_inst.help()

    if len(command.arguments) > 0:
        print
        print 'Arguments:'
        show_arguments(command.arguments)

    if len(command.options) > 0:
        print
        print 'Options:'
        show_options(command.options)
