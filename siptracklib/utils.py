import codecs
import sys
import getpass
import os
import urllib

import siptracklib
from siptracklib import errors
from siptracklib import win32utils

def parse_connection_string(cs):
    ret = {}
    if cs.startswith('st://'):
        ret['scheme'] = 'st'
        ret['use-ssl'] = False
        ret['port'] = siptracklib.default_port
        rest = cs[5:]
    elif cs.startswith('sts://'):
        ret['scheme'] = 'sts'
        ret['use-ssl'] = True
        ret['port'] = siptracklib.default_ssl_port
        rest = cs[6:]
    else:
        rest = cs
    rest, port = urllib.splitnport(rest, None)
    if port:
        ret['port'] = port
    username, hostname = urllib.splituser(rest)
    if username:
        ret['username'] = username
    if hostname:
        ret['server'] = hostname
    return ret

def get_default_config_files():
    if sys.platform == 'win32':
        appdata_dir = win32utils.get_appdata_dir()
        config_file = os.path.join(appdata_dir, 'siptrack.conf')
        files = [config_file]
    else:
        files = ['/etc/siptrack.conf',
                os.path.expanduser('~/.siptrackrc')]
    return files

def get_user_config_file():
    if sys.platform == 'win32':
        appdata_dir = win32utils.get_appdata_dir()
        config_file = os.path.join(appdata_dir, 'siptrack.conf')
    else:
        config_file = os.path.expanduser('~/.siptrackrc')
    return config_file

def get_default_session_filename():
    session_filename = None
    if sys.platform == 'win32':
        appdata_dir = win32utils.get_appdata_dir()
        if appdata_dir:
            session_filename = os.path.join(appdata_dir, '.siptrack.session')
    else:
        session_filename = os.path.expanduser('~/.siptrack.session')
    return session_filename

def make_replace_printer():
    """Create a unicode-converting, error-replacing stdout wrapper."""
    stream_wr = codecs.getwriter(siptracklib.user_encoding)
    return stream_wr(sys.stdout, errors = 'replace')
global_u_writer_fd = make_replace_printer()

def cprint(output):
    """A unicode, converting, error/replacing stdout printer.

    This is a replacement for the python print function, but it deals slightly
    differently with unicode strings.
    """
    print >>global_u_writer_fd, output

def encode_noerr(string):
    """Encode a unicode string as the users prefered encoding.
    
    Unencodable characters are replaced rather then erroring out.
    """
    return string.encode(siptracklib.user_encoding, 'replace')

def read_password(msg = 'Enter password', verify = True,
                  use_stderr = True):
    """Get a password from the user.
    
    Also prompts verification, checks for empty passwords, does character
    encoding/decoding etc.
    """
    match = False
    msg = '%s: ' % (encode_noerr(msg))
    try:
        old_stdout = sys.stdout
        sys.stdout = sys.stderr
        while not match:
            password = getpass.getpass(msg)
            if verify:
                verify_password = getpass.getpass('Re-enter for verification: ')
                if password != verify_password:
                    cprint('Passwords don\'t match.')
                else:
                    match = True
            else:
                match = True
    finally:
        sys.stdout = old_stdout
    password = password.decode(siptracklib.user_encoding)

    return password

def read_response(msg, default = None):
    """Get a response from a user."""
    prompt = '%s: ' % (msg)
    if default:
        prompt = '%s [%s]: ' % (msg, default)
    resp = raw_input(prompt)
    if len(resp) == 0 and default:
        return default
    resp = resp.decode(siptracklib.user_encoding)
    return resp

def ask_yes_no(msg, default):
    """Ask the user a yes or no question."""
    if default == 'y':
        yn = '[y]/n'
    else:
        yn = 'y/[n]'
    while True:
        reply = read_response('%s (%s)' % (msg, yn))
        if len(reply) == 0:
            reply = default
        reply = reply.lower()
        if reply not in ['y', 'n', 'yes', 'no']:
            continue
        break

    if reply in ['y', 'yes']:
        reply = True
    if reply in ['n', 'no']:
        reply = False

    return reply

class PicklistOption(object):
    def __init__(self, option, value = None, default = False):
        self.option = option
        self.value = value
        self.default = default

def pick_from_list(options, msg = 'Option number'):
    default_num = None
    for pos, opt in enumerate(options):
        pos = pos + 1
        print('[%2d] %s' % (pos, opt.option))
        if opt.default:
            default_num = str(pos)
    print
    max_val = len(options)
    if default_num:
        msg = '%s [%s]' % (msg, default_num)

    while True:
        resp = read_response(msg)
        if len(resp) == 0 and default_num is not None:
            resp = default_num
        try:
            resp = int(resp)
        except ValueError:
            continue
        if resp < 1 or resp > max_val:
            continue
        break

    return options[resp - 1]

def object_by_attribute(object_list, attr_value, attr_name = 'name',
        return_multiple = False):
    multiple = []
    for obj in object_list:
        cur_value = obj.attributes.get(attr_name, None)
        if cur_value != attr_value:
            continue
        if not return_multiple:
            return obj
        multiple.append(obj)
    if return_multiple and len(multiple) > 0:
        return multiple
    return None

def fetch_device_path(device_tree, path_names, create = False):
    dc = device_tree
    for loc in path_names:
        next_dc = object_by_attribute(dc.listDeviceCategories(), loc)
        if next_dc is None:
            if not create:
                return None
            next_dc = dc.deviceCategory()
            next_dc.attributes['name'] = loc
        dc = next_dc
    return dc

def read_session_id(filename):
    session_id = None
    if os.path.isfile(filename):
        session_id = open(filename).read()
    return session_id

def write_session_id(filename, session_id):
    exists = os.path.exists(filename)
    open(filename, 'w').write(session_id)
    if not exists:
        os.chmod(filename, 0o600)

def get_siptrack_base_dir():
    dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    return dir

def get_icon_path(icon_name):
    paths = ['/usr/share/siptrack/icons',
            './icons',
            os.path.join(get_siptrack_base_dir(), 'icons')]
    for path in paths:
        if os.path.isdir(path):
            return os.path.join(path, icon_name)
    return ''

def daemonize():
    if os.fork():
        os._exit(0)
    os.setsid()
    if os.fork():
        os._exit(0)
    null = os.open('/dev/null', os.O_RDWR)
    for i in range(3):
        try:
            os.dup2(null, i)
        except OSError as e:
            if e.errno != errno.EBADF:
                raise
    os.close(null)

def search_device(st, searchstring, attr_limit = [], quick = True, max_results = 0):
    if quick:
        result = st.quicksearch(searchstring, attr_limit,
                                include = ['device', 'ipv4 network', 'ipv6 network'],
                                max_results = max_results)
    else:
        result = st.search(searchstring, attr_limit,
                include = ['device', 'ipv4 network', 'ipv6 network'])
    devices = set()
    for node in result:
        if node.class_name == 'device':
            devices.add(node)
        elif node.class_name in ['ipv4 network', 'ipv6 network']:
            ndevices = node.listAssociations(include = ['device']) + \
                    node.listReferences(include = ['device'])
            devices.update(ndevices)
    return list(devices)

def select_device_from_list(devices):
    if len(devices) == 0:
        raise errors.SiptrackError('no matching device found')
    elif len(devices) == 1:
        device = devices[0]
    else:
        options = [PicklistOption(device.attributes.get('name'), device)
                for device in devices]
        device = pick_from_list(options, 'Select matching device').value
    return device

def get_terminal_size(fd = None):
    import struct, fcntl, termios, pty
    if fd is None:
        fd = pty.STDOUT_FILENO
    columns = 0
    rows = 0
    x_pixels = 0
    y_pixels = 0
    try:
        s = struct.pack('HHHH', 0, 0, 0, 0)
        x = fcntl.ioctl(fd, termios.TIOCGWINSZ, s)
        rows, columns, x_pixels, y_pixels = struct.unpack('HHHH', x)
    except IOError:
        pass
    if columns <= 0 and 'COLUMNS' in os.environ:
        try:
            columns = int(os.environ['COLUMNS'])
        except ValueError:
            pass
    if rows <= 0 and 'ROWS' in os.environ:
        try:
            rows = int(os.environ['ROWS'])
        except ValueError:
            pass
    if columns <= 0:
        columns = 80
    if rows <= 0:
        rows = 80
    return rows, columns, x_pixels, y_pixels

def set_terminal_size(fd = None, size = None):
    import struct, fcntl, termios, pty
    if fd is None:
        fd = pty.STDOUT_FILENO
    if size is None:
        size = get_terminal_size()
    size_struct = struct.pack('HHHH', size[0], size[1], size[2],
            size[3])
    try:
        x = fcntl.ioctl(fd, termios.TIOCSWINSZ, size_struct)
    except IOError:
        pass

