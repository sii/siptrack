from siptracklib.objectregistry import object_registry
from siptracklib import treenodes
from siptracklib import errors
from siptracklib import attribute
from siptracklib import permission

class ContainerTree(treenodes.BaseNode):
    """Container tree, a tree for containers.

    This object type is pretty much obsolete.
    """
    class_id = 'CT'
    class_name = 'container tree'
    class_data_len = 0

    def __init__(self, parent):
        super(ContainerTree, self).__init__(parent)

class Container(treenodes.BaseNode):
    """Container for attributes.

    This object type is pretty much obsolete.
    """
    class_id = 'C'
    class_name = 'container'
    class_data_len = 0

    def __init__(self, parent):
        super(Container, self).__init__(parent)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(ContainerTree)
o.registerChild(Container)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(Container)
o.registerChild(Container)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

