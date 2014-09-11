from siptracklib.transport import xmlrpc

def register_transports(transports):
    if len(transports) != 0:
        return
    transports['default'] = xmlrpc.Transport
    transports['xmlrpc'] = xmlrpc.Transport
