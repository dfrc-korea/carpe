# -*- coding: utf-8 -*-

class BasePlugin(object):
    NAME = 'base_plugin'

    DESCRIPTION = ''

    @property
    def plugin_name(self):
        """Return the name of the plugin."""
        return self.NAME

    def Process(self, **kwargs):
        """Evaluates if this is the correct plugin and processes data accordingly.
        """
