from __future__ import print_function

import siptracklib
import siptracklib.root
import siptracklib.config
from siptracklib import utils
from siptracklib import errors
from siptracklib import win32utils

import os
import sys

class ConnectionManager(object):
    def __init__(self, config = None, interactive = False):
        if config:
            self.config = config
        else:
            self.config = siptracklib.config.SiptrackConfig()
        self.interactive = interactive

    def connect(self):
        session_filename = self.config.get('session-filename')
        if session_filename.startswith('~'):
            session_filename = os.path.expanduser(session_filename)

        if not self.config.getInt('port'):
            if self.config.getBool('use-ssl', False):
                self.config.set('port', siptracklib.default_ssl_port)
            else:
                self.config.set('port', siptracklib.default_port)
        if not self.config.get('transport'):
            raise errors.SiptrackCommandError('transport')

        self.transport = siptracklib.transports[self.config.get('transport')](
                self._getServer(), self.config.getInt('port'),
                self.config.getBool('use-ssl'))

        connected = False
        if self.config.getBool('retain-session', False):
            prev_session_id = utils.read_session_id(
                    session_filename)
            if prev_session_id:
                try:
                    new_session_id = self.transport.connect(
                            session_id = prev_session_id,
                            verify_session_id = True)
                    connected = True
                except errors.InvalidLoginError:
                    pass
        if not connected:
            username = self._getUsername()
            password = self._getPassword()
            new_session_id = self.transport.connect(username, password)

        if self.config.getBool('retain-session', False) and \
                prev_session_id != new_session_id:

            session_filename = self.config.get('session-filename')
            if session_filename.startswith('~'):
                session_filename = os.path.expanduser(session_filename)

            utils.write_session_id(
                session_filename,
                new_session_id
            )

        object_store = siptracklib.root.ObjectStore(self.transport)
        return object_store

    def disconnect(self):
        if not self.config.getBool('retain-session', False):
            self.transport.disconnect()

    def _getServer(self):
        server = self.config.get('server')
        if not server:
            if self.interactive:
                prompt = 'Siptrack server'
                server = utils.read_response(prompt)
            else:
                raise errors.InvalidUsernameError('invalid or missing username')
        self.config.set('server', server)
        return server

    def _getUsername(self):
        username = self.config.get('username')
        if not username:
            if self.interactive:
                prompt = 'Username for %s' % (self.config.get('server'))
                username = utils.read_response(prompt)
            else:
                raise errors.InvalidUsernameError('invalid or missing username')
        self.config.set('username', username)
        return username

    def _getPassword(self):
        password = self.config.get('password')
        if not password:
            password_file = self.config.get('password-file')
            if password_file and os.path.isfile(password_file):
                password = open(password_file).read().rstrip()
        if not password and self.interactive:
            prompt = 'Password for %s@%s' % (self.config.get('username'),
                    self.config.get('server'))
            password = utils.read_password(prompt, verify = False)
        if not password:
            raise errors.InvalidPasswordError('invalid or missing password')
        return password

