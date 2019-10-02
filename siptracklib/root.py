from siptracklib import treenodes
from siptracklib import view
from siptracklib import password
from siptracklib import errors
from siptracklib.objectregistry import object_registry

class ObjectStore(object):
    def __init__(self, transport):
        self.oid_mapping = {}
        self.root = self
        self.parent = None
        self.transport = transport
        self.transport_root = transport
        self.object_registry = object_registry
        self.view_tree = object_registry.createObject(view.ViewTree.class_id,
                self)
        self.view_tree.oid = '0'
        self.addedOID(self.view_tree.oid, self.view_tree)

    def _getOID(self, oid):
        if oid in self.oid_mapping:
            return self.oid_mapping[oid]
        return None

    def getOID(self, oid):
        r = list(self.getOIDs(oid))
        return self._getOID(oid)

    def getOIDs(self, oids):
        if not isinstance(oids, list):
            oids = [oids]
        missing = [oid for oid in oids if not self._getOID(oid)]
        if len(missing) > 0:
            for data in self.transport.cmd.iterFetchIterator(missing, 0,
                                                      include_parents = True, include_associations = True,
                                                      include_references = True):
                self.loadChildren(data)
        for oid in oids:
            yield self._getOID(oid)

    def fetch(self, *args, **kwargs):
        """Convenience function."""
        return self.view_tree.fetch(*args, **kwargs)

    def getSessionUser(self):
        oid = self.transport.cmd.sessionUserOID()
        return self.getOID(oid)

    def traverse(self, *args, **kwargs):
        """Convenience function."""
        return self.view_tree.traverse(*args, **kwargs)

    def search(self, *args, **kwargs):
        """Convenience function."""
        return self.view_tree.search(*args, **kwargs)

    def quicksearch(self, search_pattern, attr_limit = [], include = [],
                    exclude = [], sorted = True, fuzzy = True, default_fields = ['name', 'description'],
                    max_results = 0):
        oids = []
        for data, _oids in self.transport_root.cmd.iterQuicksearchIterator(search_pattern,
                                                                           attr_limit, include, exclude, False, False, False, False, fuzzy, default_fields, max_results):
            oids.extend(_oids)
        nodes = list(self.getOIDs(oids))
        if sorted:
            nodes.sort()
        return nodes

    def localSearch(self, *args, **kwargs):
        """Convenience function."""
        return self.view_tree.localSearch(*args, **kwargs)

    def addedOID(self, oid, node):
        self.oid_mapping[oid] = node

    def removedOID(self, oid):
        if oid in self.oid_mapping:
            del self.oid_mapping[oid]

    def loadChildren(self, transport_data, force = False):
        for node_data in transport_data:
            if node_data['oid'] in self.oid_mapping:
                # If force, have the node reload it's data even if it
                # already exists.
                if force is True:
                    self.oid_mapping[node_data['oid']]._loaded(node_data)
#                print 'trying to add existing oid:', node_data['oid']
                continue
            parent = self._getOID(node_data['parent'])
            # If we don't have a node for the parent, use the view tree.
            # Ugly..
            if not parent:
                print 'adding to unknown parent:', node_data['parent'], node_data['oid']
                parent = self.view_tree
            if not object_registry.isValidChild(parent.class_id, node_data['class_id']):
                print 'skipping invalid node type:', node_data['class_id'], node_data['oid']
                continue
            parent.loadChild(node_data)

    def logout(self):
        self.transport.cmd.logout()

    def listServerSessions(self):
        return self.transport.cmd.listSessions()

    def killServerSession(self, session_id):
        return self.transport.cmd.killSession(session_id)

    def flushServerGathererDataCache(self):
        return self.transport.cmd.flushGathererDataCache()

    def getOIDServerGathererDataCache(self, oid):
        return self.transport.cmd.getOIDGathererDataCache(oid)

