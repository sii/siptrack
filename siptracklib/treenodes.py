import re
import time

from siptracklib import errors
from siptracklib.objectregistry import object_registry

class NodeFilter(object):
    """A filter for object tree node traversal.

    Can be used as a filter for traversal of nodes (node.traverse).
    include : a list of classes to be included, everything will be included
        if empty.
    exclude : a list of classes to exclude, has priority over the include
        list.
    no_match_break : will prevent further recursing down unmatches nodes.
    """
    result_match = 1
    result_no_match = 0
    result_break = -1

    def __init__(self, include = [], exclude = [], no_match_break = False):
        self.include_all = False
        self.include = include
        self.exclude = exclude
        if len(self.include) == 0:
            self.include_all = True
        self.ret_match = 1
        self.ret_no_match = 0
        if no_match_break:
            self.ret_no_match = -1
        self.result = 0

    def filter(self, node):
        """Filter a node through the filter rules.

        Returns -1 for no match + halt of further traversal down that
        branch. 0 for regular no match. 1 for match.
        """
        # Matched exclude, don't yield.
        if node.class_name in self.exclude:
            self.result = self.ret_no_match
        # Include list empty, include anything not excluded.
        elif self.include_all:
            self.result = self.ret_match
        # Matched include, yield.
        elif node.class_name in self.include:
            self.result = self.ret_match
        # We didn't match excludes, but not includes either, counts as no
        # match.
        else:
            self.result = self.ret_no_match
        return self.result

class FilterInclude(object):
    """A traversal filter that always returns 1 (matched)."""
    def __init__(self):
        self.result = 1

    def filter(self, node):
        return 1
filter_include = FilterInclude()

def traverse_tree_depth_first(root, include_root, max_depth, filter = None,
        include_depth = False, sorted = False):
    """Depth-first iteration through a tree starting at 'root'.

    If include_root is true also returns the root object given, otherwise
    only children will be returned.
    Only max_depth branches will be traversed, setting max_depth to -1 will
    skip depth checking.
    If include_depth is included the current depth is yielded along with
    the branch.

    Filters can be used to filter the results, if a filter is passed in
    it must have a filter method that accepts a node and returns one
    of the following:
    -1 : exclude branch and it's children.
     0 : exclude branch but not it's children.
     1 : include branch.
    Filters must also have a result attribute that contains the result
    of the last filter operation.
    """
    if filter == None:
        filter = filter_include
    depth = 0
    if include_root:
        if filter.filter(root) == -1:
            return
        if filter.result == 1:
            if include_depth:
                yield (depth, root)
            else:
                yield root
        depth += 1
    # We only yield the branch itself if max_depth = 0 and
    # include_self = True.
    if max_depth != -1 and depth > max_depth:
        return
    iterators = []
    if sorted:
        root.sortChildren()
    cur_iterator = iter(root.children)
    while cur_iterator != None:
        try:
            node = cur_iterator.next()
            if filter.filter(node) == 1:
                if include_depth:
                    yield (depth, node)
                else:
                    yield node
            if node.children and filter.result != -1 and \
                    (max_depth == -1 or depth < max_depth):
                depth += 1
                iterators.append(cur_iterator)
                if sorted:
                    node.sortChildren()
                cur_iterator = iter(node.children)
        except StopIteration:
            if len(iterators) > 0:
                cur_iterator = iterators.pop()
                depth -= 1
            else:
                cur_iterator = None

def traverse_tree_reverse(root, include_root):
    """Reverse depth-first iteration through a tree starting at 'root'.

    Iterate through a tree in reverse order, the outermost branches
    will be returned first.
    If include_root is true also returns (last) the root object given,
    otherwise only children will be returned.
    """
    iterators = []
    cur_iterator = iter(root.children)
    while cur_iterator != None:
        try:
            node = cur_iterator.next()
            if node.children:
                iterators.append((cur_iterator, node))
                cur_iterator = iter(node.children)
            else:
                yield node
        except StopIteration:
            if len(iterators) > 0:
                cur_iterator, node = iterators.pop()
                yield node
            else:
                cur_iterator = None
    if include_root:
        yield root

def traverse_list(entries, filter = None, sorted = False):
    """Walk a list using the given filter (if any)."""
    if sorted:
        entries = sorted(entries)
    if filter == None:
        filter = filter_include
    for ent in entries:
        if filter.filter(ent) == filter.result_match:
            yield ent

class BaseNode(object):
    """Base class for all objects in the tree.

    This class is inherited by all regular tree objects, views,
    containers etc.
    """
    sort_type = 'default'

    def __init__(self, parent):
        self.oid = None
        self.children = []
        self.parent = parent
        self.root = parent.root
        self.transport_root = parent.transport_root
        self.transport = self.transport_root.section(self.class_id)
        self.attributes = AttributeDict(self)
        self.fetched_children = False
        self.sorted_children = False
        self._associations = []
        self._references = []
        self.ctime = 0

    def describe(self):
        """Return a descriptive string for this node."""
        return '%s:%s:%s' % (self.class_name, self.oid,
                self.attributes.get('name'))

    def dictDescribe(self):
        """Return a dict representation of this node."""
        parent_oid = ''
        if self.parent and hasattr(self.parent, 'oid'):
            parent_oid = self.parent.oid
        data = {'oid': self.oid,
                'cls': self.class_name,
                'parent': parent_oid,
                'ctime': self.ctime,
                'associations': self._associations,
                'references': self._references,
               }
        return data

    def __lt__(self, other):
        if not isinstance(other, BaseNode):
            return False
        mine = self.attributes.get('name', None)
        theirs = other.attributes.get('name', None)
        if mine is not None and theirs is not None:
            if mine.lower() < theirs.lower():
                return True
            return False
        else:
            if self.class_name < other.class_name:
                return True
            return False
        return False

    def __eq__(self, other):
        if not isinstance(other, BaseNode):
            return False
        mine = self.attributes.get('name')
        theirs = other.attributes.get('name')
        if mine is not None and theirs is not None:
            if mine.lower() == theirs.lower():
                return True
            return False
        else:
            if self.class_name == other.class_name:
                return True
            return False
        return False

    def __gt__(self, other):
        return not self.__lt__(other)

    def createChildByID(self, class_id, *args, **kwargs):
        if not object_registry.isValidChild(self.class_id, class_id):
            raise errors.SiptrackError(
                    'trying to create child of invalid type \'%s\' for type \'%s\' (oid: %s)' % (class_id, self.class_id, self.oid))
        child = object_registry.createObject(class_id, self, *args, **kwargs)
        self.children.append(child)
        self._children_sorted = False
        return child

    def addChildByID(self, class_id, *args, **kwargs):
        child = self.createChildByID(class_id, *args, **kwargs)
        try:
            # Called only for newly created objects.
            child._created()
        except:
            child._delete()
            raise
        self.root.addedOID(child.oid, child)
        return child

    def addChildByName(self, class_name, *args, **kwargs):
        """Identical to addChildByID, but with class_name."""
        class_id = object_registry.getIDByName(class_name)
        if class_id is None:
            raise errors.SiptrackError('unknown class name for creating child')
        return self.addChildByID(class_id, *args, **kwargs)
    add = addChildByName
    addChild = addChildByName

    def loadChild(self, node_data):
        child = self.createChildByID(node_data['class_id'])
        self.root.addedOID(node_data['oid'], child)
        try:
            child._loaded(node_data)
        except:
            self.root.removedOID(node_data['oid'])
            child._delete()
            raise
        return child

    def _created(self):
        """Called when an object has been newly created.

        As opposed to when an already existing object is just being loaded.
        Should be overriden if work needs to be done here.
        """
        self.oid = self.transport.add(self.parent.oid)
        pass

    def _loaded(self, node_data):
        """Called when an existing object has just been loaded.

        As opposed to when an object has just been created for the first
        time (see: ._created()).
        Should be overriden if work needs to be done here.
        """
        if len(node_data['data']) != self.class_data_len:
            raise errors.InvalidServerData('%s: %s' % (node_data['class_id'], node_data['data']))
        self.oid = node_data['oid']
        self._associations = node_data['associations']
        self._references = node_data['references']
        self.ctime = node_data['ctime']

    def delete(self):
        self.transport.delete(self.oid)
        self._purge()

    def _purge(self):
        """Removes node and all children locally, not from the server."""
        for node in traverse_tree_reverse(self, include_root = True):
            node._delete()

    def _delete(self):
        if self.oid is not None:
            self.root.removedOID(self.oid)
        self.parent.children.remove(self)
        self.oid = None
        self.transport = None
        self.transport_root = None
        self.parent = None
        self.root = None

    def relocate(self, new_parent):
        """Sets a new parent for a node.

        Not all nodes are valid parents for certain node types. We ask the
        server to do the relocation first, if that doesn't fail, we also
        do it locally.
        """
        self.transport_root.cmd.moveOID(self.oid, new_parent.oid)
        self.parent.children.remove(self)
        new_parent.children.append(self)
        self.parent = new_parent

    def associate(self, other):
        self.transport_root.cmd.associate(self.oid, other.oid)
        self._associations.append(other.oid)
        other._references.append(self.oid)

    def disassociate(self, other):
        """Remove an association to another object."""
        self.transport_root.cmd.disassociate(self.oid, other.oid)
        self._associations.remove(other.oid)
        other._references.remove(self.oid)

    def unlink(self, other):
        if self.isAssociated(other):
            self.disassociate(other)
        elif other.isAssociated(self):
            other.disassociate(self)
        else:
            raise errors.SiptrackError('not linked: %s' % other)
        return True

    def isAssociated(self, other):
        return self.transport_root.cmd.isAssociated(self.oid, other.oid)

    def isLinked(self, other):
        ret = True
        if not self.transport_root.cmd.isAssociated(self.oid, other.oid):
            if not self.transport_root.cmd.isAssociated(other.oid, self.oid):
                ret = False
        return ret

    def _get_associations(self):
        for oid in self._associations:
            try:
                node = self.root.getOID(oid)
            except errors.NonExistent:
                continue
            if node:
                yield node

    def _set_associations(self, value):
        return
    associations = property(_get_associations, _set_associations)

    def _get_references(self):
        for oid in self._references:
            try:
                node = self.root.getOID(oid)
            except errors.NonExistent:
                continue
            if node:
                yield node

    def _set_references(self, value):
        return
    references = property(_get_references, _set_references)

    def listAssociations(self, include = [], exclude = [], sorted = True):
        node_filter = NodeFilter(include, exclude, no_match_break = False)
        return list(traverse_list(self.associations, node_filter, sorted))

    def listReferences(self, include = [], exclude = [], sorted = True):
        node_filter = NodeFilter(include, exclude, no_match_break = False)
        return list(traverse_list(self.references, node_filter, sorted))

    def _iterAssocRef(self):
        for link in self.references:
            yield link
        for link in self.associations:
            yield link

    def listLinks(self, include = [], exclude = [], sorted = True):
        node_filter = NodeFilter(include, exclude, no_match_break = False)
        return list(traverse_list(self._iterAssocRef(), node_filter, sorted))

    def fetch(self, max_depth, include_parents = True,
            include_associations = True,
            include_references = True,
            force = False):
        for data in self.transport_root.cmd.iterFetchIterator(self.oid, max_depth,
                                                       include_parents,
                                                       include_associations,
                                                       include_references):
            self.root.loadChildren(data, force)

    def traverse(self, include_self = True, max_depth = -1,
            include = [], exclude = [], no_match_break = False,
            include_depth = False, sorted = False):
        """Tree traversal.

        Just like branch.traverse but returns nodes, not branches.
        include/exclude are used to filter results with the NodeFilter
        class.
        """
        node_filter = NodeFilter(include, exclude, no_match_break)
        return traverse_tree_depth_first(self, include_self, max_depth,
                node_filter, include_depth, sorted)

    def listChildren(self, fetch = True, include = [], exclude = [],
            sorted = True):
        if not self.fetched_children and fetch:
            self.fetch(max_depth = 1)
            self.fetched_children = True
        return list(self.traverse(include_self = False, max_depth = 0,
                include = include, exclude = exclude, sorted = sorted))

    def search(self, re_pattern, attr_limit = [], include = [], exclude = [],
            no_match_break = False, sorted = True):
        oids = []
        for data, _oids in self.transport_root.cmd.iterSearchIterator(self.oid, re_pattern, attr_limit,
                include, exclude, no_match_break, False, False, False, False):
            oids.extend(_oids)
        nodes = list(self.root.getOIDs(oids))
        if sorted:
            nodes.sort()
        return nodes

    def localSearch(self, re_pattern, attr_limit = [], include = [],
            exclude = [], no_match_break = False):
        """Searches for nodes.

        Basically identical in funcationallity to a server side search,
        but only searches in the local tree, no server querying at all.

        Search the node tree for nodes attributes that match the regular
        expression re_pattern.

        re_pattern : a regular expression that is matched again attribute
            values
        attr_limit : limits the search to attributes with names in the given
            list
        include    : include only node types listed
        exclude    : exclude node types listed
        no_match_break : see argument with same name to traverse
        """
        re_compiled = re.compile(re_pattern, re.IGNORECASE)
        match_any_attrs = True
        if len(attr_limit) > 0:
            match_any_attrs = False
        local_include = ['attribute', 'ipv4 network', 'ipv6 network']
        prev_added = None
        node_filter = NodeFilter(include, exclude, no_match_break)
        for node in self.traverse(include = local_include, exclude = exclude,
                no_match_break = no_match_break):
            # Match attributes.
            if node.class_name == 'attribute':
                if (match_any_attrs or node.name in attr_limit) and \
                        node.atype == 'text' and \
                        re_compiled.search(node.value):
                    # Get the attributes nearest _non-attribute_ parent.
                    parent = node.getParentNode()
                    if parent is not prev_added and \
                            node_filter.filter(parent) == \
                            node_filter.result_match:
                        yield parent
                        prev_added = parent
            # Match networks.
            elif node.class_name in ['ipv4 network', 'ipv6 network']:
                if re_compiled.search(str(node.address)) and \
                        node is not prev_added and \
                        node_filter.filter(node) == \
                        node_filter.result_match:
                    yield node
                    prev_added = node

    def getChildByAttribute(self, attribute, value, include = [], exclude = []):
        for node in self.listChildren(include = include, exclude = exclude):
            for _attr in node.attributes._listAttributes():
                if attribute == _attr.name and value == _attr.value:
                    return node

    def getChildByName(self, name, include = [], exclude = []):
        for node in self.listChildren(include = include, exclude = exclude):
            if node.attributes.get('name') == name:
                return node
    getChild = getChildByName

    def getParent(self, class_name, include_self = False):
        """Return the nearest matching parent of type class_name."""
        # Can't go any further back.
        if self.class_name == 'view tree':
            return None
        if include_self:
            match = self
        else:
            match = self.parent
        while match:
            if match.class_name == class_name:
                return match
            # Can't go any further back.
            if match.class_name == 'view tree':
                break
            match = match.parent
        return None

    def getObjectOID(self, obj):
        if obj is None:
            return ''
        return obj.oid

    def sortChildren(self):
        """Sort the children stored for this node.

        To get as proper sorting as possible, sort groups
        of nodes that are 'sorting compatible'.
        """
        if self.sorted_children is False:
            self.sorted_children = True
            stypes = {}
            for child in self.children:
                if child.sort_type not in stypes:
                    stypes[child.sort_type] = []
                stypes[child.sort_type].append(child)
            self.children = []
            for children in stypes.itervalues():
                children.sort()
                self.children += children

    def prettyCtime(self):
        return time.ctime(self.ctime)

    def _isSafeCopyTarget(self, target):
        while target:
            if target == self:
                return False
            target = target.parent
        return True

    def copy(self, target, include_nodes = [], exclude_nodes = [], include_links = [], exclude_links = [], skip_safety_check = False):
        if not hasattr(self, '_copySelf'):
            return
        if not self._isSafeCopyTarget(target):
            raise errors.SiptrackError('unsafe copy target: %s' % (target))
        copy = self._copySelf(target)
        for node in self.listChildren(include = include_nodes, exclude = exclude_nodes):
            node.copy(copy, include_nodes, exclude_nodes, include_links, exclude_links, skip_safety_check = True)
        for node in self.listLinks(include = include_links, exclude = exclude_links):
            copy.associate(node)
        return copy

class AttributeDict(object):
    def __init__(self, real):
        self.real = real

    def __len__(self):
        return len(list(self._listAttributes()))

    def __iter__(self):
        for attr in self._listAttributes():
            yield attr

    def _listAttributes(self):
        # DO NOT SET SORTED = True.
        # Since sorting lists the compared objects attributes this will
        # result in a whole lot of sorting..
        local_types = [
            'attribute',
            'versioned attribute',
            'encrypted attribute'
        ]
        return self.real.listChildren(
            fetch = False,
            include = local_types,
            sorted = False
        )

    def __getitem__(self, item):
        for attr in self._listAttributes():
            if attr.name == item:
                return attr.value
        # If nothing is found, try case-insensitive match.
        item = item.lower()
        for attr in self._listAttributes():
            if attr.name.lower() == item:
                return attr.value
        raise TypeError('attribute not found in AttributeDict')

    def __contains__(self, item):
        for attr in self._listAttributes():
            if attr.name == item:
                return True
        # If nothing is found, try case-insensitive match.
        item = item.lower()
        for attr in self._listAttributes():
            if attr.name.lower() == item:
                return True
        return False

    def __setitem__(self, item, value):
        atype = 'text'
        if type(value) in [list, tuple]:
            if len(value) != 2:
                raise errors.SiptrackError('invalid attribute dict access')
            atype, value = value
        elif isinstance(value, bool):
            atype = 'bool'
        elif isinstance(value, int):
            atype = 'int'
        attr_exists = False
        for attr in self._listAttributes():
            if attr.name == item:
                attr.value = value
                attr_exists = True
        if not attr_exists:
            attribute = self.real.add('attribute', item, atype, value)

    def get(self, item, default = None):
        if item in self:
            return self[item]
        return default

    def getObject(self, item, default = None):
        for attr in self._listAttributes():
            if attr.name == item:
                return attr
        # If nothing is found, try case-insensitive match.
        item = item.lower()
        for attr in self._listAttributes():
            if attr.name.lower() == item:
                return attr
        return default

class NodeList(object):
    def __init__(self, parent, nodes = None):
        self.parent = parent
        self.nodes = []
        self.oids = []
        self.resolved = False
        if nodes != None and len(nodes) > 0:
            self.nodes = nodes
            self.oids = [node.oid for node in nodes]
            self.resolved = True

    def __iter__(self):
        self.resolve()
        for node in self.nodes:
            yield node

    def get(self):
        self.resolve()
        return self.nodes

    def resolve(self):
        if self.resolved:
            return
        self.nodes = list(self.parent.root.getOIDs(self.oids))

    def setOids(self, oids):
        self.oids = oids
        self.nodes = []
        self.resolved = False
    set = setOids

    def setNodes(self, nodes):
        self.nodes = list(nodes)
        self.oids = [node.oid for node in nodes]
        self.resolved = True

