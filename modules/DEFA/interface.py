# -*- coding: utf-8 -*-

from modules import plugins

class DEFAPlugin(plugins.BasePlugin):
    """DEFA plugin."""

    NAME = 'DEFA_DEFAULT'
    DESCRIPTION = "DEFA plugin"

    def __init__(self):
        super(DEFAPlugin, self).__init__()

    def Process(self, **kwargs):
        """Process
        """
