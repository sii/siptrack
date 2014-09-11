from siptracklib.transport.xmlrpc import baserpc
import xmlrpclib
import zlib
try:
    import simplejson
    json_encode = simplejson.dumps
    json_decode = simplejson.loads
except:
    import json
    json_encode = json.dumps
    json_decode = json.loads

class RootRPC(baserpc.BaseRPC):
    command_path = ''

    def login(self, username, password):
        self.transport.session_id = self.sendNoSID('login', username, password)

    def logout(self):
        ret = self.send('logout')
        self.transport.session_id = None
        return ret

    def ping(self):
        return self.sendNoSID('ping')

    def version(self):
        return self.sendNoSID('version')

    def hello(self):
        return self.send('hello')

    def sessionUserOID(self):
        return self.send('session_user_oid')

    def oidExists(self, oid):
        return self.send('oid_exists', oid)

    def moveOID(self, oid, new_parent_oid):
        return self.send('move_oid', oid, new_parent_oid)

    def iterFetch(self, oids, max_depth, include_parents, include_associations,
            include_references):
        return self.send('iter_fetch', oids, max_depth, include_parents,
                include_associations, include_references)

    def iterFetchNext(self, next_id):
        return self.send('iter_fetch_next', next_id)

    def iterFetchIterator(self, *args, **kwargs):
        result = self.iterFetch(*args, **kwargs)
        if result['data']:
            yield self._decodeFetchData(result['data'])
        while result['next']:
            result = self.iterFetchNext(result['next'])
            if result['data']:
                yield self._decodeFetchData(result['data'])

    def _decodeFetchData(self, data):
        data = zlib.decompress(str(data))
        data = json_decode(data)
        new_data = []
        for ent in data:
            new_data.append(json_decode(ent))
        return new_data

    def iterSearch(self, oid, search_pattern, attr_limit, include, exclude,
            no_match_break, include_data, include_parents, include_associations,
            include_references):
        return self.send('iter_search', oid, search_pattern, attr_limit, include,
                exclude, no_match_break, include_data, include_parents,
                include_associations, include_references)

    def iterSearchNext(self, next_id):
        return self.send('iter_search_next', next_id)

    def iterSearchIterator(self, *args, **kwargs):
        return self._iterSearchIterator(self.iterSearch, self.iterSearchNext, *args, **kwargs)

    def iterQuicksearch(self, search_pattern, attr_limit, include, exclude,
            include_data, include_parents, include_associations,
            include_references, fuzzy, default_fields, max_results):
        return self.send('iter_quicksearch', search_pattern, attr_limit, include,
                exclude, include_data, include_parents,
                include_associations, include_references, fuzzy, default_fields,
                max_results)

    def iterQuicksearchNext(self, next_id):
        return self.send('iter_quicksearch_next', next_id)

    def iterQuicksearchIterator(self, *args, **kwargs):
        return self._iterSearchIterator(self.iterQuicksearch, self.iterQuicksearchNext, *args, **kwargs)

    def _iterSearchIterator(self, search_method, next_method, *args, **kwargs):
        result = search_method(*args, **kwargs)
        if result['data']:
            yield self._decodeSearchData(result['data'])
        while result['next']:
            result = next_method(result['next'])
            if result['data']:
                yield self._decodeSearchData(result['data'])

    def _decodeSearchData(self, data):
        data = zlib.decompress(str(data))
        data = json_decode(data)
        match_data, oids = data
        new_data = []
        for ent in match_data:
            new_data.append(json_decode(ent))
        return new_data, oids

    def associate(self, oid_1, oid_2):
        return self.send('associate', oid_1, oid_2)

    def disassociate(self, oid_1, oid_2):
        return self.send('disassociate', oid_1, oid_2)

    def isAssociated(self, oid_1, oid_2):
        return self.send('is_associated', oid_1, oid_2)

    def setSessionTimeout(self, timeout):
        return self.send('set_session_timeout', timeout)

    def listSessions(self):
        return self.send('list_sessions')

    def killSession(self, session_id):
        return self.send('kill_session', session_id)

    def flushGathererDataCache(self):
        return self.send('flush_gatherer_data_cache')

    def getOIDGathererDataCache(self, oid):
        return self.send('get_oid_gatherer_data_cache', oid)

