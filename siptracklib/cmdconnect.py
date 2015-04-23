#!/usr/bin/env python

import sys
import subprocess
import os
from optparse import OptionParser
import socket
import tempfile
import codecs
import time
import select

from siptracklib import errors
from siptracklib import utils
from siptracklib import win32utils

if sys.platform == 'win32':
    try:
        import win32crypt
        import win32clipboard
        import _winreg as wreg
        import binascii
    except ImportError:
        raise errors.SiptrackCommandError('connect requires win32crypt/_winreg')
    DEFAULT_PUTTY_BIN = os.path.join(
            win32utils.get_program_files_dir(), 'PuTTY', 'putty.exe')
    DEFAULT_PUTTY_PWOPT = '-pw'
else:
    import pty
    import tty
    import signal

def select_device_username(device, usernames):
    match = None
    passwords = device.listChildren(include = ['password'])
    device_usernames = [p.attributes.get('username') for p in passwords]
    for username in usernames:
        if username in device_usernames:
            match = username
            break
    if not match:
        if len(device_usernames) == 1:
            match = device_usernames[0]
        elif len(device_usernames) > 1:
            print 'No default usernames matched, select username to use.'
            options = []
            options.append(utils.PicklistOption('Abort.', None))
            for password in passwords:
                if len(password.attributes.get('description', '')) == 0:
                    optionstr = password.attributes.get('username', '')
                else:
                    optionstr = '%s - %s' % (
                            password.attributes.get('username', ''),
                            password.attributes.get('description', ''))
                option = utils.PicklistOption(optionstr,
                        password.attributes.get('username'))
                options.append(option)
            match = utils.pick_from_list(options, 'Username').value
            print match
    return match

class BaseConnect(object):
    rdp_console = False

    def _checkTCPPort(self, hostname, port, timeout = 2):
        sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sd.settimeout(timeout)
        try:
            sd.connect((hostname, port))
        except socket.error:
            return False
        sd.close()
        return True

    def _getDeviceInfo(self, device, username):
        hostname = device.attributes.get('name')
        host_os = device.attributes.get('os')
        password = None
        for child in device.listChildren(include = ['password']):
            if child.attributes.get('username') == username:
                password = child.password
        if password is None:
            raise errors.SiptrackError('no password for user %s found' % (username))
        password = password.rstrip('\n')
        return hostname, host_os, password

    def connect(self, device, username):
        hostname, host_os, password = self._getDeviceInfo(device, username)
        if host_os == 'linux':
            print 'trying ssh connection to %s@%s with password %s' % (username, hostname, password)
            self._connectSSH(hostname, username, password)
        elif host_os == 'windows':
            print 'trying rdp connection to %s@%s with password %s' % (username, hostname, password)
            self._connectRDP(hostname, username, password)
        else:
            if self._checkTCPPort(hostname, 3389):
                print 'trying rdp connection to %s@%s with password %s' % (username, hostname, password)
                self._connectRDP(hostname, username, password)
            elif self._checkTCPPort(hostname, 22):
                print 'trying ssh connection to %s@%s with password %s' % (username, hostname, password)
                self._connectSSH(hostname, username, password)
            else:
                raise errors.SiptrackError('sorry, I don\'t know how to connect to this device')

    def setPasswordClipboard(self, device, username):
        hostname, host_os, password = self._getDeviceInfo(device, username)
        self._addPasswordToClipboard(password)

class UnixConnect(BaseConnect):
    clipboard_progs = ['/usr/bin/xclip', '/usr/bin/pbcopy']
    clipboard_bin = None
    use_clipboard = True
    terminal_bin = '/usr/bin/x-terminal-emulator'
    ssh_bin = '/usr/bin/ssh'
    ssh_extraopt = None
    open_new_terminal = False
    rdp_extraopt = None

    def _sshWrite(self, fd, data):
        while data != '':
            n = os.write(fd, data)
            data = data[n:]

    def _matchSSHPassword(self, data, passwd, remote_fd):
        self._pass_data = '%s%s' % (self._pass_data, data)
        # Only look for data in the first 10Kb, if it hasn't come by then,
        # skip it.
        if len(self._pass_data) > 1024*10:
            return True
        if 'assword:' in self._pass_data:
            self._pass_data = None
            self._sshWrite(remote_fd, '%s\n' % (passwd))
            return True
        return False

    def _copySSHData(self, remote_fd, passwd):
        matched_password = False
        self._pass_data = ''
        while True:
            try:
                rfds, wfds, xfds = select.select(
                        [remote_fd, pty.STDIN_FILENO], [], [])
            except select.error, e:
                if e[0] == 4: # Interrupted system call
                    continue
                raise
            if remote_fd in rfds:
                try:
                    data = os.read(remote_fd, 1024)
                except OSError, e:
                    if e.errno != 4: # Interrupted system call
                        raise
                else:
                    if len(data) == 0:
                        return
                if not matched_password:
                    matched_password = self._matchSSHPassword(data, passwd,
                            remote_fd)
                try:
                    os.write(pty.STDOUT_FILENO, data)
                except OSError, e:
                    if e.errno != 4: # Interrupted system call
                        raise
            if pty.STDIN_FILENO in rfds:
                try:
                    data = os.read(pty.STDIN_FILENO, 1024)
                except OSError, e:
                    if e.errno != 4: # Interrupted system call
                        raise
                else:
                    if len(data) == 0:
                        return
                if len(data) > 0:
                    self._sshWrite(remote_fd, data)

    def _connectSSH(self, hostname, username, passwd):
        if self.open_new_terminal:
            self._connectSSHFork(hostname, username, passwd)
        else:
            self._connectSSHLocal(hostname, username, passwd)

    def _connectSSHFork(self, hostname, username, passwd):
        sshenv = os.environ
        sshenv['STCONNECT_FORK_PASS_%s' % (os.getpid())] = passwd
        siptrack_bin = sys.argv[0]
        sshcmd = [self.terminal_bin, '-e', siptrack_bin, 'connect-fork',
                username, hostname, str(os.getpid()), self.ssh_bin]
        self._addPasswordToClipboard(passwd)
        subprocess.call(sshcmd, env = sshenv)

    def _setRemoteTTYSize(self, tty):
        size = utils.get_terminal_size()
        utils.set_terminal_size(tty, size)

    def _winchHandler(self, signum, frame):
        self._setRemoteTTYSize(self.remote_fd)

    def _connectSSHLocal(self, hostname, username, passwd):
        sshcmd = [self.ssh_bin, '%s@%s' % (username, hostname)]
        if self.ssh_extraopt:
            sshcmd += self.ssh_extraopt.split()
        self._addPasswordToClipboard(passwd)
        pid, self.remote_fd = pty.fork()
        if pid == pty.CHILD:
            os.execlp(sshcmd[0], *sshcmd)
        try:
            mode = tty.tcgetattr(pty.STDIN_FILENO)
            tty.setraw(pty.STDIN_FILENO)
            restore = True
        except tty.error:
            restore = False
        signal.signal(signal.SIGWINCH, self._winchHandler)
        self._setRemoteTTYSize(self.remote_fd)
        self._setTerminalTitle('%s@%s' % (username, hostname))
        try:
            self._copySSHData(self.remote_fd, passwd)
        except (IOError, OSError):
            pass
        except:
            if restore:
                tty.tcsetattr(pty.STDIN_FILENO, tty.TCSAFLUSH, mode)
            raise
        if restore:
            tty.tcsetattr(pty.STDIN_FILENO, tty.TCSAFLUSH, mode)
        signal.signal(signal.SIGWINCH, signal.SIG_DFL)
        os.close(self.remote_fd)

    def _connectRDP(self, hostname, username, passwd):
        rdpcmd = ['rdesktop', '-u', username, '-p', passwd]
        if self.rdp_console:
            rdpcmd.append('-0')
        if self.rdp_extraopt:
            rdpcmd += self.rdp_extraopt.split()
        rdpcmd += [hostname]
        self._addPasswordToClipboard(passwd)
        subprocess.Popen(rdpcmd)

    def _selectClipboardProg(self):
        if self.clipboard_bin is not None:
            return
        for prog in self.clipboard_progs:
            if os.path.isfile(prog):
                self.clipboard_bin = prog
                return

    def _addPasswordToClipboard(self, passwd):
        if not self.use_clipboard:
            return
        self._selectClipboardProg()
        if self.clipboard_bin is None or not os.path.isfile(self.clipboard_bin):
            return
        cmd = [self.clipboard_bin]
        # This might fail if we have no xserver etc.
        try:
            pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE).stdin
            pipe.write(passwd)
            pipe.close()
        except Exception, e:
            pass

    def _setTerminalTitle(self, title):
        print '\033]0;%s\007' % (title)

class Win32Connect(BaseConnect):
    _registry_rdp_key = 'Software\\Microsoft\\Terminal Server Client\\LocalDevices'
    win32_ssh_bin = None
    win32_ssh_pwopt = None
    win32_ssh_extraopt = None
    win32_rdp_addreg = None
    win32_rdp_cfgtmpl = None
    use_clipboard = True

    def _connectSSH(self, hostname, username, password):
        if not self.win32_ssh_bin:
            if os.path.isfile(DEFAULT_PUTTY_BIN):
                self.win32_ssh_bin = DEFAULT_PUTTY_BIN
                self.win32_ssh_pwopt = DEFAULT_PUTTY_PWOPT
            else:
                raise errors.SiptrackError('set the "win32-ssh-bin" option in your config file')
        sshcmd = [self.win32_ssh_bin, '%s@%s' % (username, hostname)]
        if self.win32_ssh_pwopt:
            sshcmd.append(self.win32_ssh_pwopt)
            sshcmd.append(password)
        if self.win32_ssh_extraopt:
            sshcmd += self.win32_ssh_extraopt.split()
        self._addPasswordToClipboard(password)
        subprocess.Popen(sshcmd)

    def _connectRDP(self, hostname, username, password):
        config_file = self._createMstscConfig(hostname, username, password)
        rdpcmd = ['mstsc', config_file]
        if self.rdp_console:
            rdpcmd.append('/console')
        if self.win32_rdp_addreg:
            self._addDeviceToRegistry(hostname)
        self._addPasswordToClipboard(password)
        subprocess.Popen(rdpcmd)
        time.sleep(5)
        os.unlink(config_file)

    def _createMstscConfig(self, hostname, username, password):
        fd, filename = tempfile.mkstemp()
        password = self._encryptPassword(password)
        os.write(fd, 'full address:s:%s\r\n' % (hostname))
        os.write(fd, 'username:s:%s\r\n' % (username))
        os.write(fd, 'password 51:b:%s\r\n' % (password))
        os.write(fd, 'authentication level:i:0\r\n')
        if self.win32_rdp_cfgtmpl:
            if os.path.isfile(self.win32_rdp_cfgtmpl):
                rfd = open(self.win32_rdp_cfgtmpl, 'r')
                rfd = codecs.EncodedFile(rfd, 'utf-8', 'utf-16')
                for line in rfd:
                    line = line.strip()
                    if line.startswith('full address:') or \
                            line.startswith('username:') or \
                            line.startswith('password 51:') or \
                            line.startswith('authentication level:'):
                        continue
                    os.write(fd, '%s\r\n' % (line))
            else:
                print 'WARNING: file not found for win32-rdp-config-template'
        os.close(fd)
        return filename

    def _encryptPassword(self, password):
        hash = win32crypt.CryptProtectData(password.decode('utf-8'),
                u'psw', None, None, None, 0)
        password = binascii.hexlify(hash)
        password = password.upper()
        return password

    def _addDeviceToRegistry(self, hostname):
        try:
            key = wreg.OpenKey(wreg.HKEY_CURRENT_USER, self._registry_rdp_key,
                    0, wreg.KEY_WRITE)
            wreg.SetValueEx(key, hostname, None, wreg.REG_DWORD, 0x0c)
        except WindowsError, e:
            print 'WARNING: failed to add registry key: "%s"' % (str(e))
            return
        else:
            key.Close()

    def _addPasswordToClipboard(self, passwd):
        if not self.use_clipboard:
            return
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_TEXT, passwd)
        win32clipboard.CloseClipboard()

def get_connection_class(config):
    if sys.platform == 'win32':
        connection = Win32Connect()
        if config:
            connection.win32_ssh_bin = config.get('win32-ssh-bin')
            connection.win32_ssh_pwopt = config.get('win32-ssh-pwopt')
            connection.win32_ssh_extraopt = config.get('win32-ssh-extraopt')
            connection.win32_rdp_addreg = config.get('win32-rdp-addreg')
            connection.win32_rdp_cfgtmpl = config.get('win32-rdp-config-template')
            if config.getBool('use-clipboard', None) is not None:
                connection.use_clipboard = config.get('use-clipboard')
    else:
        connection = UnixConnect()
        if config:
            if config.getBool('open-new-terminal', False) is not None:
                connection.open_new_terminal = config.getBool('open-new-terminal', False)
            connection.rdp_extraopt = config.get('rdp-extraopt')
            if config.get('terminal-bin', False):
                connection.terminal_bin = config.get('terminal-bin')
            if config.get('ssh-bin', False):
                connection.ssh_bin = config.get('ssh-bin')
            if config.get('ssh-extraopt', False):
                connection.ssh_extraopt = config.get('ssh-extraopt')
            if config.get('clipboard-bin', False):
                connection.clipboard_bin = config.get('clipboard-bin')
            if config.getBool('use-clipboard', None) is not None:
                connection.use_clipboard = config.getBool('use-clipboard')
    return connection

def get_device_and_user(st, devicename, search_all, quick_search, config, config_sections):
    username = None
    username_in_cmdline = False
    if '@' in devicename:
        try:
            username, devicename = devicename.split('@')
            usernames = [username]
            username_in_cmdline = True
        except ValueError:
            raise errors.SiptrackError('invalid devicename')

    config.sections = config_sections
    if username is None:
        username = config.get('default-username')
        if username is None:
            raise errors.SiptrackError('no username supplied, set default-username in config or give username\non command-line')
        usernames = username.strip().split()
    attr_limit = []
    if not search_all:
        attr_limit = ['name']
    devices = utils.search_device(st, devicename, attr_limit, quick_search, max_results = 50)
    devices.sort()
    device = utils.select_device_from_list(devices)
    username = select_device_username(device, usernames)
    if not username:
        raise errors.SiptrackError('no matching username found for device')
    if username_in_cmdline and username != usernames[0]:
        raise errors.SiptrackError('no matching username found for device')
    return (device, username)

def cmd_connect(st, devicename, search_all, quick_search, console, config):
    device, username = get_device_and_user(st, devicename, search_all, quick_search,
                                           config, ['STCONNECT', 'DEFAULT'])
    connection = get_connection_class(config)
    connection.rdp_console = console
    connection.connect(device, username)

def cmd_copy_password_clipboard(st, devicename, search_all, quick_search, config):
    device, username = get_device_and_user(st, devicename, search_all, quick_search,
                                           config, ['STCONNECT', 'DEFAULT'])
    connection = get_connection_class(config)
    connection.setPasswordClipboard(device, username)

def cmd_connect_fork(username, hostname, caller_pid, ssh_bin):
    """Called when connect is starting a ssh connection in a new terminal.
    
    This is the command that connects to the server in the new terminal,
    it is started as a separate process.
    """
    env_name = 'STCONNECT_FORK_PASS_%s' % (caller_pid)
    if env_name not in os.environ:
        print 'Unable to find password'
        return
    passwd = os.environ[env_name]
    os.environ[env_name] = ''
    connection = UnixConnect()
    connection.ssh_bin = ssh_bin
    connection.open_new_terminal = False
    connection._connectSSH(hostname, username, passwd)

