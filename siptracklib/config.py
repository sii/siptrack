import ConfigParser
import os
import sys

import siptracklib
from siptracklib import utils
from siptracklib import win32utils

default_options = {
        'retain-session': True,
        'session-filename': utils.get_default_session_filename(),
        'transport': 'default',
        'use-ssl': True,
        'verbose': False
        }

class SiptrackConfig(object):
    def __init__(self, config_reader = None, sections = None,
            options = {}):
        if config_reader:
            self.config_reader = config_reader
        else:
            self.config_reader = ConfigReader(utils.get_default_config_files())
        if sections:
            self.sections = sections
        else:
            self.sections = ['DEFAULT']
        self.options = options

    def get(self, option, default = None, sections = None):
        if sections is None:
            sections = self.sections
        value = self.options.get(option,
                self._getOptionFromConfig(option, sections,
                    default_options.get(option, default)))
        return value

    def getInt(self, option, default = None, sections = None):
        value = self.get(option, default, sections)
        try:
            value = int(value)
        except:
            value = None
        return value

    def getBool(self, option, default = None, sections = None):
        value = self.get(option, default, sections)
        if isinstance(value, bool):
            pass
        elif type(value) in [str, unicode]:
            if value.lower() in ['true', '1']:
                value = True
            elif value.lower() in ['false', '0']:
                value = False
        return value

    def set(self, option, value):
        self.options[option] = value

    def update(self, options):
        self.options.update(options)

    def setConfigFiles(self, config_files):
        self.config_reader = ConfigReader(config_files)

    def _getOptionFromConfig(self, option, sections, default = None):
        value = None
        for section in sections:
            value = self.config_reader.get(section, option)
            if value:
                break
        if value is None:
            value = default
        return value

class ConfigReader(object):
    """Configuration objects base class.
    
    Parses a configuration file and has basic retrieval methods.
    """
    def __init__(self, config_files):
        self.conf = ConfigParser.SafeConfigParser()
        self.config_files = config_files
        self.conf.read(config_files)

    def get(self, section, option):
        """See if an option exists in the given section.
        
        The option value will be returned if it exists otherwise None.
        """
        if self.conf.has_option(section, option):
            return self.conf.get(section, option)
        return None

    def has_option(self, section, option):
        return self.conf.has_option(section, option)

    def section(self, section):
        return ConfigSection(self, section)

    def default_section(self):
        return ConfigSection(self, 'DEFAULT')

class ConfigSection(object):
    def __init__(self, config, section):
        self.config = config
        self.section = section

    def get(self, option):
        return self.config.get(self.section, option)

    def has_option(self, option):
        return self.config.has_option(self.section, option)

