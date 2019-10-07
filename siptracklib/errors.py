class SiptrackError(Exception):
    """Generic siptrack error."""
    pass

class SiptrackCommandError(SiptrackError):
    """Command error, invalid command line options etc."""
    pass

class AlreadyExists(SiptrackError):
    """Generic object already exists error."""
    def __str__(self):
        if len(self.args) == 1:
            ret = self.args[0]
        else:
            ret = 'object already exists'
        return ret

class NonExistent(SiptrackError):
    """Generic object doesn't exist error."""
    def __str__(self):
        if len(self.args) == 1:
            ret = self.args[0]
        else:
            ret = 'object doesn\'t exist'
        return ret

class InvalidAttributeType(SiptrackError):
    """Invalid container attribute type."""
    def __str__(self):
        if len(self.args) == 1:
            ret = self.args[0]
        else:
            ret = 'invalid container attribute type'
        return ret


class InvalidLocation(SiptrackError):
    """Invalid path supplied to server error."""
    def __str__(self):
        if len(self.args) == 1:
            ret = self.args[0]
        else:
            ret = 'invalid object path supplied to server'
        return ret

class InvalidServerData(SiptrackError):
    """Invalid data received from server."""
    def __str__(self):
        if len(self.args) == 1:
            ret = 'invalid data received from server: %s' % (self.args[0])
        else:
            ret = 'invalid data received from server'
        return ret

class UnregisteredChildType(SiptrackError):
    """Something tried to use an unknown child type with treebuilder."""
    def __str__(self):
        if len(self.args) == 1:
            ret = 'unregistered child type: %s' % (self.args[0])
        else:
            ret = 'unregistered child type'
        return ret

class InvalidLoginError(SiptrackError):
    """Invalid username/password."""
    def __str__(self):
        if len(self.args) == 1:
            ret = self.args[0]
        else:
            ret = 'invalid username/password'
        return ret

class InvalidUsernameError(SiptrackError):
    pass

class InvalidPasswordError(SiptrackError):
    pass

class PermissionDenied(SiptrackError):
    def __str__(self):
        if len(self.args) == 1:
            ret = self.args[0]
        else:
            ret = 'permission denied'
        return ret
