#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author:    Seonho Lee
@contact:   horensic@gmail.com
"""

import os
from pdfminer.pdfdocument import *
from pdfminer.pdfpage import *
from pdfminer.pdfinterp import *
from pdfminer.pdftypes import *
from pdfminer.pdffont import PDFUnicodeNotDefined
from pdfminer.cmapdb import CMapParser, FileUnicodeMap
try:
    from pdfminer.psparser import STRICT
except ImportError:
    from pdfminer.settings import STRICT
from modules.DEFA.PDF.error import CMAPNotFoundError
from modules.DEFA.PDF import logger


restore_pdf_log = logger.CarpeLog("PDFRestore", level=logger.LOG_INFO)


class XRefFallback(PDFXRefFallback):

    def load(self, parser):
        parser.seek(0)

        while True:
            try:
                (pos, line) = parser.nextline()
            except PSEOF:
                break

            # line = line.decode('latin-1')  # default pdf encoding

            m = self.PDFOBJ_CUE.match(line)

            if not m:
                continue

            (objid, genno) = m.groups()
            objid = int(objid)
            genno = int(genno)

            self.offsets[objid] = (None, pos, genno)

            # expand ObjStm
            parser.seek(pos)
            try:
                (_, obj) = parser.nextobject()
            except PSEOF:
                break

            if isinstance(obj, PDFStream) and obj.get('Type') is LITERAL_OBJSTM:
                stream = stream_value(obj)
                try:
                    n = stream['N']
                except KeyError:
                    if STRICT:
                        raise PDFSyntaxError('N is not defined: %r' % stream)
                    n = 0
                parser1 = PDFStreamParser(stream.get_data())
                objs = []

                try:
                    while True:
                        (_, obj) = parser1.nextobject()
                        objs.append(obj)
                except PSEOF:
                    pass
                n = min(n, len(objs)//2)
                for index in range(n):
                    objid1 = objs[index*2]
                    self.offsets[objid1] = (objid, index, 0)

        return


class PDFRestore:

    PDFOBJ_CUE = re.compile(r'^(\d+)\s+(\d+)\s+obj\b')
    INHERITABLE_ATTRS = {'Resources', 'MediaBox', 'CropBox', 'Rotate'}

    def __init__(self, parser):
        self.parser = parser
        self.doc = parser.doc
        self.xref = None
        self.catalog = {}
        self.info = None

    def restore_xref(self):
        xref = XRefFallback()
        xref.load(self.parser)

        self.xref = xref
        self.doc.xrefs.append(xref)

    def find_catalog(self):
        restore_pdf_log.debug("Called find_catalog()")
        for objid, pos in self.xref.offsets.items():
            if not pos[0]:
                self.parser.seek(pos[1])
                self.parser.nextline()
                (pos, obj) = self.parser.nextobject()

                if isinstance(obj, dict) and obj.get('Type') is LITERAL_CATALOG:
                    self.catalog = dict_value(obj)
                    break
        else:
            # Not Found Catalog Object
            restore_pdf_log.debug("Not Found Catalog Object")
            return False
        restore_pdf_log.debug("Found Catalog Object")
        return True

    def find_pages(self):
        for objid, pos in self.xref.offsets.items():
            if not pos[0]:
                self.parser.seek(pos[1])
                self.parser.nextline()
                (pos, obj) = self.parser.nextobject()

                if isinstance(obj, dict) and obj.get('Type') is LITERAL_PAGES:
                    self.pages = dict_value(obj)
                    break
        else:
            # Not Found Pages Object
            return False
        return True

    def find_page(self):
        restore_pdf_log.debug("Called find_page()")

        def search(obj, parent):
            objid = obj.objid
            tree = dict_value(obj).copy()

            for (k, v) in parent.items():
                if k in self.INHERITABLE_ATTRS and k not in tree:
                    tree[k] = v

            tree_type = tree.get('Type')

            if tree_type is LITERAL_PAGES and 'Kids' in tree:
                for c in list_value(tree['Kids']):
                    for x in search(c, tree):
                        yield x
            elif tree_type is LITERAL_PAGE:
                yield (objid, tree)

        if self.catalog is not None and 'Pages' in self.catalog:
            pages = self.catalog['Pages']
            restore_pdf_log.trace("Pages Object: {0}".format(pages))

            for (objid, tree) in search(pages, self.catalog):
                yield (objid, tree)

        elif self.pages is not None and 'Kids' in self.pages:
            pass

        else:
            pass

    def find_metadata(self):
        restore_pdf_log.debug("Called find_metadata()")
        for objid, pos in self.xref.offsets.items():
            if not pos[0]:
                self.parser.seek(pos[1])
                self.parser.nextline()
                (pos, obj) = self.parser.nextobject()

                if isinstance(obj, dict) and obj.get('CreationDate'):
                    self.info = obj
                    break
        else:
            # Not Found Metadata Object
            return False
        return True

    def find_multimedia(self):
        restore_pdf_log.debug("Called find_multimedia()")
        for objid, pos in self.xref.offsets.items():
            if not pos[0]:
                self.parser.seek(pos[1])
                self.parser.nextline()
                try:
                    (pos, obj) = self.parser.nextobject()
                except PSEOF:
                    return ('', None)
                # Multimedia
                if isinstance(obj, PDFStream) and obj.get('Type'):
                    if obj.get('Type').name == 'XObject':
                        yield ('', obj)

                if isinstance(obj, dict) and obj.get('EF'):
                    for media_ref, media_obj in obj['EF'].items():
                        filename = obj[media_ref].decode('ascii')
                        media_stream = media_obj.resolve()
                        yield (filename, media_stream)


class PDFPageStream:

    def __init__(self, page, version):
        self.resources = page.resources
        self.stream = page.contents
        self.textstate = PDFTextState()
        self.rsrcmgr = PDFResourceManager()

        self.fontmap = {}
        self.bodytext = ''

        self.init_unicode_map()

        self.restore_unicode_map(version)

    def interpreter(self):
        stream = list_value(self.stream)
        args = []

        try:
            parser = PDFContentParser(stream)
        except PSEOF:
            # empty page
            return
        while True:
            try:
                (_, obj) = parser.nextobject()
            except PSEOF:
                break

            if isinstance(obj, PSKeyword) and (keyword_name(obj) == 'Tj') or (keyword_name(obj) == 'TJ'):
                for scrabble in args:
                    if isinstance(scrabble, bytes):
                        if scrabble == b' ':  # Space
                            self.bodytext += ' '
                        for cid in self.textstate.font.decode(scrabble):
                            try:
                                self.bodytext += self.textstate.font.to_unichr(cid)
                            except PDFUnicodeNotDefined:  # Font Object(ToUnicode Object) damaged
                                self.bodytext += self.korean_unicode_map.cid2unichr[cid]

            elif isinstance(obj, PSKeyword) and keyword_name(obj) == 'Tf':
                self.select_font(*args)

            elif isinstance(obj, PSKeyword):
                args = []

            else:
                if isinstance(obj, list):
                    args = obj
                else:
                    args.append(obj)

        return self.bodytext

    def identity_cmap(self, code):
        n = len(code) // 2
        if n:
            return struct.unpack('>%dH' % n, code)
        else:
            return ()

    def init_unicode_map(self):
        for (k, v) in dict_value(self.resources).items():
            if k == 'Font':
                for (fontid, spec) in dict_value(v).items():
                    objid = None
                    if isinstance(spec, PDFObjRef):
                        objid = spec.objid
                    spec = dict_value(spec)
                    self.fontmap[fontid] = self.rsrcmgr.get_font(objid, spec)
            # elif k == 'ColorSpace':
                # pass
            # elif k == 'ProcSet':
                # pass
            # elif k == 'XObject':
                # pass

    def select_font(self, fontid, fontsize):
        try:
            self.textstate.font = self.fontmap[literal_name(fontid)]
        except KeyError:
            self.textstate.font = self.rsrcmgr.get_font(None, {})
        self.textstate.fontsize = fontsize

    def restore_unicode_map(self, version):

        self.korean_unicode_map = FileUnicodeMap()

        if not os.path.isdir('../cmap/'):
            print("Check if cmap file & directory exists")
            raise CMAPNotFoundError

        if version == 7:  # version 1.7
            if not os.path.exists('../cmap/Adobe-Identity-UCS_1-7'):
                print("Check the following file exists: {0}".format("cmap/Adobe-Identity-UCS_1-7"))
                raise CMAPNotFoundError
            with open('../cmap/Adobe-Identity-UCS_1-7', 'rb') as strm:  # TODO:path setting
                CMapParser(self.korean_unicode_map, BytesIO(strm.read())).run()
        elif version == 6:  # version 1.6
            pass
        elif version == 5:  # version 1.5
            pass
        elif version == 4:  # version 1.4
            if not os.path.exists('../cmap/Adobe-Identity-UCS_1-4'):
                print("Check the following file exists: {0}".format("cmap/Adobe-Identity-UCS_1-4"))
                raise CMAPNotFoundError
            with open('../cmap/Adobe-Identity-UCS_1-4', 'rb') as strm:  # TODO:path setting
                CMapParser(self.korean_unicode_map, BytesIO(strm.read())).run()
        elif version == 3:  # version 1.3
            pass
        elif version == 2:  # version 1.2
            pass
