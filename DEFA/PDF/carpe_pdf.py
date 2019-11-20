#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author:    Seonho Lee
@contact:   horensic@gmail.com
"""

import io
import os, sys
from datetime import datetime, timezone
try:
    from restore_pdf import *
except ModuleNotFoundError:
    sys.path.append(os.path.dirname(__file__))
    from restore_pdf import *
from extract_pdf import *
from error import *
import logger
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter


carpe_pdf_log = logger.CarpeLog("PDF", level=logger.LOG_INFO)


class WrapperPDFPage(PDFPage):

    @classmethod
    def get_pages(klass, fp, parser=None, doc=None,
                  pagenos=None, maxpages=0, password='',
                  caching=True, check_extractable=True):

        if not parser:
            parser = PDFParser(fp)
        else:
            parser = parser

        if not doc:
            doc = PDFDocument(parser, password=password, caching=caching)
        else:
            doc = doc

        if check_extractable and not doc.is_extractable:
            raise PDFTextExtractionNotAllowed('Text extraction is not allowed: %r' % fp)

        for (pageno, page) in enumerate(klass.create_pages(doc)):
            if pagenos and (pageno not in pagenos):
                continue
            yield page
            if maxpages and maxpages <= pageno+1:
                break
        return


class PDF:

    def __init__(self, path):
        self._damaged = False
        self._recovered = False

        self.path = path
        self.pdf = None
        self.document = None
        self.content = str()
        self.metadata = None

        self.is_damaged = False
        self.has_content = False
        self.has_metadata = False
        self.has_ole = False
        self.ole_path = []

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

        if self.document or self.parse():
            caching = True
            # normal pdf
            rsrcmgr = PDFResourceManager(caching=caching)
            retstr = io.StringIO()
            # codec = 'utf-8'
            laparams = LAParams()

            device = TextConverter(rsrcmgr, retstr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)

            for page in WrapperPDFPage.get_pages(self.pdf, parser=self.parser, doc=self.document, caching=caching):
                interpreter.process_page(page)

            self.content = retstr.getvalue()
            device.close()
            retstr.close()
        else:
            # damaged pdf
            self.restore_content()

    def parse_metadata(self):

        def timestamp(ts):
            """
            :description:
            :param ts: (bytes) document.info['CreationDate']
            :return: (str) timestamp // UTC+0
            """

            raw_ts = ts.decode('ascii')[2:]
            if "'" in raw_ts:
                raw_ts = raw_ts.replace("'", "")
            if "Z" in raw_ts:
                if raw_ts[raw_ts.find('Z')+1].isdigit():
                    raw_ts = raw_ts.replace("Z", "+")
                else:
                    raw_ts = raw_ts.replace("Z", "")
                    raw_ts += '+0000'
            dt = datetime.strptime(raw_ts, "%Y%m%d%H%M%S%z")
            utc_dt= dt.astimezone(timezone.utc)

            return utc_dt.__str__()[:-6]

        if self.document or self.parse():
            # normal pdf
            self.metadata = self.document.info
        else:
            # damaged pdf
            self.metadata = self.restore_metadata()

        if len(self.metadata) != 0:
            print(self.metadata[0])

            if 'CreationDate' in self.metadata[0]:
                self.metadata[0]['CreationDate'] = timestamp(self.metadata[0]['CreationDate']).encode('ascii')

            if 'ModDate' in self.metadata[0]:
                self.metadata[0]['ModDate'] = timestamp(self.metadata[0]['ModDate']).encode('ascii')

    def extract_multimedia(self):

        if self.document or self.parse():
            # normal pdf
            count = 0
            pdf_path, pdf_name = os.path.split(self.path)
            for name, stream in PDFMultimedia.get_multimedia(document=self.document):
                extract = os.path.join(pdf_path, f"{pdf_name}_extracted")
                if not os.path.exists(extract):
                    os.mkdir(extract)
                if name == '':
                    name = f"{pdf_name}_image({count}).jpg"
                    count += 1
                dst = os.path.join(extract, name)
                with open(dst, 'wb') as multimedia_file:
                    multimedia_file.write(stream.get_data())
                    self.has_ole = True
                    self.ole_path.append(dst)
        else:
            count = 0
            pdf_path, pdf_name = os.path.split(self.path)
            for name, stream in self.restore_multimedia():
                extract = os.path.join(pdf_path, f"{pdf_name}_extracted")
                if not os.path.exists(extract):
                    os.mkdir(extract)
                if name == '':
                    name = f"{pdf_name}_image({count}).jpg"
                    count += 1
                dst = os.path.join(extract, name)
                with open(dst, 'wb') as multimedia_file:
                    multimedia_file.write(stream.get_data())
                    self.has_ole = True
                    self.ole_path.append(dst)

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

    def restore_multimedia(self):
        carpe_pdf_log.debug("Called restore_multimedia()")
        self.is_damaged = True

        restored_xref = None
        if not self._recovered:
            self._recovered = True

            if self.parser.doc is not None:
                xrefs = self.parser.doc.xrefs  # this case don't need to restore Xref
                for xref in xrefs:
                    if isinstance(xref, PDFXRefFallback):
                        restored_xref = xref
                        break

        damaged_pdf = PDFRestore(self.parser)

        if restored_xref is not None:
            damaged_pdf.xref = restored_xref
        else:
            carpe_pdf_log.info("Restore Xref")
            damaged_pdf.restore_xref()
            carpe_pdf_log.info("Xref restoration complete")

        for name, stream in damaged_pdf.find_multimedia():
            if stream is not None:
                yield name, stream

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
