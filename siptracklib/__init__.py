__copyright__ = 'Copyright (C) 2008-2011 Simon Ekstrand.'
__version__ = '2.0.0'

import locale
user_encoding = locale.getpreferredencoding() or 'ascii'
del locale

default_port = '9242'
default_ssl_port = '9243'

import siptracklib.transport
transports = siptracklib.transport.transports

from siptracklib.utils import (object_by_attribute, fetch_device_path)

def connect(hostname, username = None, password = None, port = None,
        session_id = None, transport = 'default',
        verify_session_id = False, use_ssl = True):
    import siptracklib.root
    if port is None:
        if use_ssl:
            port = default_ssl_port
        else:
            port = default_port
    t = transports[transport](hostname, port, use_ssl)
    t.connect(username, password, session_id, verify_session_id)
    object_store = siptracklib.root.ObjectStore(t)
    return object_store

from siptracklib.connections import ConnectionManager
cm = ConnectionManager(interactive = True)
config = cm.config
connection_manager = cm
fconnect = cm.connect
