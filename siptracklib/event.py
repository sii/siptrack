from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import attribute
from siptracklib import permission

def get_queue(object_store, queue_name):
    ret = None
    for queue in object_store.view_tree.listChildren(include = ['command queue']):
        if queue.attributes.get('name') == queue_name:
            ret = queue
            break
    return ret

class CommandQueue(treenodes.BaseNode):
    class_id = 'CQ'
    class_name = 'command queue'
    class_data_len = 0

    def _commandSorter(self, x, y):
        return cmp(x.ctime, y.ctime)

    def listCommands(self):
        commands = list(self.listChildren(include = ['command']))
        commands.sort(cmp=self._commandSorter)
        return commands

    def processCommands(self, only_unique = False, dedup_sequential = False, remove = False):
        sent = {}
        prev_command = None
        for command in self.listCommands():
            skip = False
            if only_unique:
                if command.freetext in sent:
                    skip = True
                sent[command.freetext] = True
            if dedup_sequential:
                if prev_command == command.freetext:
                    skip = True
                prev_command = command.freetext
            if not skip:
                yield command
            if remove:
                command.remove()

class Command(treenodes.BaseNode):
    class_id = 'C'
    class_name = 'command'
    class_data_len = 1

    def __init__(self, parent, freetext = None):
        super(Command, self).__init__(parent)
        self._freetext = freetext

    def _created(self):
        self.oid = self.transport.add(self.parent.oid, self._freetext)

    def _loaded(self, node_data):
        super(Command, self)._loaded(node_data)
        self._freetext = node_data['data'][0]

    def _get_freetext(self):
        return self._freetext

    def _set_freetext(self, val):
        self._freetext = val
        self.transport.setFreetext(self.oid, val)
    freetext = property(_get_freetext, _set_freetext)

    def setStatus(self, status):
        self.attributes['status'] = status

class EventTrigger(treenodes.BaseNode):
    class_id = 'ET'
    class_name = 'event trigger'
    class_data_len = 0

class EventTriggerRulePython(treenodes.BaseNode):
    class_id = 'ETRP'
    class_name = 'event trigger rule python'
    class_data_len = 3

    def __init__(self, parent, code = None):
        super(EventTriggerRulePython, self).__init__(parent)
        self._code = code
        self._error = ''
        self._error_timestamp = 0

    def _created(self):
        self.oid = self.transport.add(self.parent.oid, self._code)

    def _loaded(self, node_data):
        super(EventTriggerRulePython, self)._loaded(node_data)
        self._code = node_data['data'][0]
        self._error = node_data['data'][1]
        self._error_timestamp = node_data['data'][2]

    def _get_code(self):
        return self._code
    def _set_code(self, val):
        self._code = val
        self.transport.setCode(self.oid, val)
    code = property(_get_code, _set_code)

    @property
    def error(self):
        return self._error

    @property
    def error_timestamp(self):
        return self._error_timestamp

# Add the objects in this module to the object registry.
o = object_registry.registerClass(Command)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(CommandQueue)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
o.registerChild(Command)

o = object_registry.registerClass(EventTriggerRulePython)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(EventTrigger)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
o.registerChild(EventTriggerRulePython)
