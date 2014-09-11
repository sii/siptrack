#!/usr/bin/env python

from distutils.core import setup
try:
    import py2exe
    has_py2exe = True
except ImportError:
    has_py2exe = False

setup_kwargs = {
        'name': 'siptrack',
        'version': '2.0.0',
        'description': 'Siptrack IP/Device Manager Client Library',
        'author': 'Simon Ekstrand',
        'author_email': 'simon@theoak.se',
        'url': 'http://siptrack.theoak.se/',
        'license': 'BSD',
        'packages': ['siptracklib', 'siptracklib.network', 'siptracklib.external',
            'siptracklib.transport', 'siptracklib.transport.xmlrpc'],
        'scripts': ['siptrack', 'tools/siptrack-generate-dns'],
        'data_files': [('share/siptrack/icons', ['icons/64x64.png'])],
        'options': {},
        }
if has_py2exe:
    setup_kwargs['console'] = ['siptrack',
            'tools/siptrack-generate-dns']
    setup_kwargs['windows'] = ['siptrack-no-console']
#    setup_kwargs['options']['py2exe'] = {
#            'includes': 'cairo, pango, pangocairo, atk, gobject'
#            }
#    setup_kwargs['data_files'] = [('icons', ['icons/64x64.png'])]
    setup_kwargs['options']['py2exe'] = {}

setup(**setup_kwargs)
