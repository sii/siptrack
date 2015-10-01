from siptracklib.transport.xmlrpc import baserpc

class DeviceConfigRPC(baserpc.BaseRPC):
    command_path = 'device.config'

    def add(self, parent_oid, name, max_versions):
        return self.send('add', parent_oid, name, max_versions)

    def setName(self, oid, name):
        return self.send('set_name', oid, name)

    def setMaxVersions(self, oid, max_versions):
        return self.send('set_max_versions', oid, max_versions)

    def addConfig(self, oid, data):
        return self.send('add_config', oid, self.transport._makeBinary(data))

    def getLatestConfig(self, oid):
        res = self.send('get_latest_config', oid)
        ret = None
        if res is not False:
            data, timestamp = res
            ret = [str(data), timestamp]
        return ret

    def getAllConfigs(self, oid):
        res = self.send('get_all_configs', oid)
        ret = []
        if res is not False:
            for data, timestamp in res:
                ret.append([str(data), timestamp])
        return ret
