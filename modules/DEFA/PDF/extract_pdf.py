#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author:    Seonho Lee
@contact:   horensic@gmail.com
"""

import io
# from PIL import Image
from pdfminer.psparser import LIT
from pdfminer.pdftypes import resolve1
from pdfminer.pdftypes import list_value
from pdfminer.pdftypes import dict_value

LITERAL_PAGE = LIT('Page')
LITERAL_PAGES = LIT('Pages')


class PDFMultimedia:

    def __init__(self, doc, attrs):
        self.doc = doc
        # self.attrs = dict_value(attrs)
        # self.resources = resolve1(self.attrs.get('Resources', dict()))

    @classmethod
    def get_multimedia(klass, document):

        def search(obj, parent):
            if isinstance(obj, int):
                objid = obj
                tree = dict_value(document.getobj(objid)).copy()
            else:
                objid = obj.objid
                tree = dict_value(obj).copy()

            for (k, v) in parent.items():
                if k in 'Resources' and k not in tree:
                    tree[k] = v

            tree_type = tree.get('Type')
            if tree_type is LITERAL_PAGES and 'Kids' in tree:
                for c in list_value(tree['Kids']):
                    for x in search(c, tree):
                        yield x

            elif tree_type is LITERAL_PAGE:
                yield (objid, tree)

        if 'Pages' in document.catalog:
            for (objid, tree) in search(document.catalog['Pages'], document.catalog):
                pageid = objid
                attrs = dict_value(tree)
                resources = resolve1(attrs.get('Resources', dict()))

                if 'XObject' in resources:  # Image
                    for (im_ref, xobj) in resources['XObject'].items():
                        image_stream = xobj.resolve()
                        if 'Filter' in image_stream:
                            if isinstance(image_stream['Filter'], list):
                                for filter in image_stream['Filter']:
                                    if filter.name == 'DCTDecode':
                                        yield ('', image_stream)
                            else:
                                #print(type(image_stream['Filter']), image_stream)
                                if image_stream['Filter'].name == 'DCTDecode':
                                    yield ('', image_stream)

                if 'Annots' in attrs:   # Multimedia (Video, Audio, SWF)
                    annots = resolve1(attrs.get('Annots', dict()))
                    for annot_obj in annots:
                        annot = annot_obj.resolve()

                        if 'RichMediaContent' in annot:
                            rich_media_content = resolve1(annot.get('RichMediaContent', dict()))

                            if 'Assets' in rich_media_content:
                                assets = resolve1(rich_media_content.get('Assets', dict()))

                                for i in range(0, len(assets['Names']), 2):
                                    media_name = assets['Names'][i].decode('utf-16')
                                    media_data_obj = assets['Names'][i+1].resolve()

                                    if 'EF' in media_data_obj:
                                        for media_ref, media_obj in media_data_obj['EF'].items():
                                            # print(media_ref, media_obj)
                                            filename = media_data_obj[media_ref].decode('ascii')
                                            media_stream = media_obj.resolve()
                                            yield (filename, media_stream)
