#!/usr/bin/env python
# -*- coding: utf-8 -*-

#           OH MY GIRL License
#   To create a program using this source code,
#   Follow the link below to listen to the OH MY GIRL's song at least once.
#   LINK (1): https://youtu.be/RrvdjyIL0fA
#   LINK (2): https://youtu.be/QIN5_tJRiyY

"""
@author:    Seonho Lee
@license:   OH_MY_GIRL License
@contact:   horensic@gmail.com
"""

import io
from restore_pdf import *
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from error import *
import logger


carpe_pdf_log = logger.CarpeLog("PDF", level=logger.LOG_INFO)


class PDF:

    def __init__(self, path):
        self._damaged = False
        self._recovered = False

        self.pdf = None
        self.document = None
        self.content = str()
        self.metadata = []

        self.is_damaged = False
        self.has_content = False
        self.has_metadata = False

        # Open PDF file
        try:
            self.pdf = open(path, 'rb')
            carpe_pdf_log.debug("Open PDF file handle")
        except:
            carpe_pdf_log.error("PDF file open failed!")
            raise PDFOpenError

    def __enter__(self):
        carpe_pdf_log.trace("Called __enter__")
        return self

    def __exit__(self, type, value, traceback):
        carpe_pdf_log.trace("Called __exit__")
        self._end()

    def __del__(self):
        carpe_pdf_log.trace("Called __del__")
        self._end()

    def __iter__(self):
        for key in dir(self):
            if not key.startswith('_'):
                yield key, getattr(self, key)

    def __repr__(self):
        return "CARPE PDF"

    def _end(self):
        if (self.pdf is not None) and (self.pdf.closed is False):
            carpe_pdf_log.debug("Close PDF file handle")
            self.pdf.close()

    def parse(self):
        carpe_pdf_log.debug("Called parse()")

        magic = self.pdf.read(8)
        self.version = int(chr(magic[7]))

        self.parser = PDFParser(self.pdf)
        try:
            document = PDFDocument(self.parser)
        except PDFSyntaxError:
            return False
        except PSEOF:
            return False
        else:
            if not document.is_extractable:
                # damaged pdf
                return False
            else:
                # normal pdf
                self.document = document
                # print(self.document.catalog)
                return True

    def check(self):
        carpe_pdf_log.debug("Called check()")
        parser = PDFParser(self.pdf)
        try:
            document = PDFDocument(parser)
        except PDFSyntaxError:
            return False
        else:
            if not document.is_extractable:
                return False
            else:
                return True

    def parse_content(self):

        if self.parse():
            # normal pdf
            rsrcmgr = PDFResourceManager()
            retstr = io.StringIO()
            codec = 'utf-8'
            laparams = LAParams()

            device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)

            for page in PDFPage.get_pages(self.pdf):
                interpreter.process_page(page)

            self.content = retstr.getvalue()
            device.close()
            retstr.close()
        else:
            # damaged pdf
            self.restore_content()

    def parse_metadata(self):
        if self.document or self.parse():
            # normal pdf
            self.metadata = self.document.info
        else:
            # damaged pdf
            self.restore_metadata()

    def restore_content(self):
        carpe_pdf_log.debug("Called restore_content()")
        self.is_damaged = True

        def scan_page(xref):  # private inner function
            damaged_pdf = PDFRestore(self.parser)

            if xref is not None:
                damaged_pdf.xref = xref
            else:  # restore xref
                carpe_pdf_log.info("Restore Xref")
                damaged_pdf.restore_xref()
                carpe_pdf_log.info("Xref restoration complete")

            if damaged_pdf.find_catalog() or damaged_pdf.find_pages():
                carpe_pdf_log.info("Find Page")
                for (pageno, page) in damaged_pdf.find_page():
                    yield (pageno, page)

        restored_xref = None
        if not self._recovered:
            self._recovered = True

            if self.parser.doc is not None:
                xrefs = self.parser.doc.xrefs  # this case don't need to restore Xref
                for xref in xrefs:
                    if isinstance(xref, PDFXRefFallback):
                        restored_xref = xref
                        break

        for (pageno, page) in scan_page(restored_xref):
            carpe_pdf_log.trace("Page No: {0}, Page: {1}".format(pageno, page))
            page_object = PDFPage(self.parser.doc, pageno, page)
            carpe_pdf_log.trace("Page Object: {0}".format(page_object))
            page_stream = PDFPageStream(page_object, self.version)
            self.content += page_stream.interpreter()

        if self.content:
            carpe_pdf_log.debug("Complete string extraction from damaged PDF file")
            self.has_content = True

    def restore_metadata(self):
        carpe_pdf_log.debug("Called restore_metadata()")
        self.is_damaged = True

        def scan_metadata(xref):
            damaged_pdf = PDFRestore(self.parser)

            if xref is not None:
                damaged_pdf.xref = xref
            else:
                carpe_pdf_log.info("Restore Xref")
                damaged_pdf.restore_xref()
                carpe_pdf_log.info("Xref restoration complete")

            if damaged_pdf.find_metadata():
                carpe_pdf_log.info("Find Metadata")
                return damaged_pdf.info

        restored_xref = None
        if not self._recovered:
            self._recovered = True

            if self.parser.doc is not None:
                xrefs = self.parser.doc.xrefs  # this case don't need to restore Xref
                for xref in xrefs:
                    if isinstance(xref, PDFXRefFallback):
                        restored_xref = xref
                        break

        self.metadata.append(dict_value(scan_metadata(restored_xref)))

    def print_content(self):
        if self.content:
            print(self.content)

    def print_metadata(self):
        if self.metadata:
            for k, v in self.metadata[0].items():
                if k == 'Creator' or k == 'Producer':  # HACK
                    print(k, v.decode('utf-16'))
                else:
                    print(k, v.decode('ascii'))
