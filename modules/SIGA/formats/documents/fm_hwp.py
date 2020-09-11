# -*- coding: utf-8 -*-

class fm_Tag_Record_Item:

    def __init__(self):
        super(fm_Tag_Record_Item, self).__init__()
        self.header_size = 0
        self.length = 0
        self.level = 0
        self.offset = 0
        self.tag_id = 0
        self.name = ''
        self.desc = ''


class fm_Tag_Suminfo_Item:

    def __init__(self):
        super(fm_Tag_Suminfo_Item, self).__init__()
        self.type = ''
        self.offset = 0
        self.length = 0
        self.desc = ''