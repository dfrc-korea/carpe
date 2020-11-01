# -*- coding: utf-8 -*-
# http://www.multiweb.cz/twoinches/MP4inside.htm
# !/usr/bin/python3

# !/Author : Gibartes

from moduleInterface.defines import *
from moduleInterface.interface import ModuleComponentInterface
from structureReader import structureReader as sr
from collections import OrderedDict
import os, sys, platform


class MP4Structure(object):
    def __init__(self):
        # TAG
        self.Header = OrderedDict({
            "size": [0, 4, None],  # HeaderSize
            "type": [4, 4, None],  # Type
            "subtype": [8, 4, None],  # Subtype
        })
        self.Chunk = OrderedDict({
            "size": [0, 4, None],
            "flag": [8, 4, None],
            "type": [12, 4, None],
        })

        # self.Types = (
        #     "ftyp", "mdat", "moov", "pnot",
        #     "udta", "uuid", "moof", "free",
        #     "skip", "jP2 ", "wide", "load",
        #     "ctab", "imap", "matt", "kmat",
        #     "clip", "crgn", "sync", "chap",
        #     "tmcd", "scpt", "ssrc", "PICT",
        #     "mvhd"
        # )

        # 2020.07.30 updated
        self.Types = (
            "ftyp", "pdin", "moov", "mvhd", "meta", "trak", "tkhd", "tref", "trgr", "edts", "elst", "mdia",
            "mdhd", "hdlr", "elng", "minf", "vmhd", "smhd", "hmhd", "sthd", "nmhd", "dinf", "dref", "url ",
            "urn ", "stbl", "stsd", "stts", "ctts", "cslg", "stsc", "stsz", "stz2", "stco", "co64", "stss",
            "stsh", "padb", "stdp", "sdtp", "sbgp", "sgpd", "subs", "saiz", "saio", "udta", "mvex", "mehd",
            "trex", "leva", "moof", "mfhd", "traf", "tfhd", "trun", "tfdt", "mfra", "tfra", "mfro", "mdat",
            "free", "skip", "cprt", "tsel", "strk", "stri", "strd", "iloc", "ipro", "rinf", "sinf", "frma",
            "schm", "iinf", "xml ", "bxml", "pitm", "fiin", "paen", "fire", "fpar", "fecr", "segr", "gitn",
            "idat", "iref", "meco", "mere", "styp", "sidx", "ssix", "prft"
        )

        self.hxedTypes = self.__convert(self.Types)
        self.hxedTypes.append(0x605ffff)

    def __convert(self, list):
        temp = []
        for i in list:
            temp.append(MP4Structure.str2ascii(i))
        return temp

    @staticmethod
    def str2ascii(string):
        code = 0
        length = len(string) - 1
        for i, v in enumerate(string):
            code += ord(v)
            if (i < length): code <<= 8
        return code


class ModuleISOBMFF(ModuleComponentInterface):

    def __init__(self):
        super().__init__()  # Initialize Module Interface
        self.fileSize = 0
        self.offset   = list()
        self.flag     = None

        self.missing = 0
        self.parser = sr.StructureReader()
        self.structure = MP4Structure()

        self.set_attrib(ModuleConstant.NAME, "ISOBMFF")
        self.set_attrib(ModuleConstant.VERSION, "0.2")
        self.set_attrib(ModuleConstant.AUTHOR, "HK, KH")

        self.fp = None
        self.off_t           = Offset_Info()
        self.off_t.name      = "isobmff"    # alias
        self.off_t.signature = "isobmff"    # signature in C_defy.SIGNATURE

    def __reinit__(self):
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.off_t.clear() 

    def __del__(self):
        self.parser.cleanup()

    """ Module Methods """

    def __evaluate(self):
        fn = self.attrib.get(ModuleConstant.FILE_ATTRIBUTE)
        if (fn == None):
            return ModuleConstant.Return.EINVAL_ATTRIBUTE
        try:
            fd = os.open(fn, os.O_RDONLY)
            os.close(fd)
        except:
            return ModuleConstant.Return.EINVAL_FILE
        return ModuleConstant.Return.SUCCESS

    def chunk_chain(self):
        # 1) while - check header
        first_header = True # ftyp 해결 용도

        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE), 1
        )

        offset = self.get_attrib(ModuleConstant.IMAGE_BASE)
        last = self.get_attrib(ModuleConstant.IMAGE_LAST)
        current = offset    # 최근 오프셋 가져와야함

        if(last == 0):  #오프셋 잘못됬을경우 다시 백
            last = self.parser.bgoto(0, os.SEEK_END)

        self.parser.bgoto(offset, os.SEEK_SET)
        self.parser.bexecute(self.structure.Header, 'int', 0, os.SEEK_CUR)

        if (self.parser.get_value("size") == 0):
            self.parser.cleanup()
            return

        self.parser.bgoto(-self.parser.get_size() + self.parser.get_value("size"))

        while (current < last ):
            if first_header == True:
                self.off_t.name  = "mp4"
                first_header = False
                current = current + 20
            self.parser.bexecute(self.structure.Header, 'int', 0, os.SEEK_CUR)
            if (self.parser.get_value("size") == 0):
                break
            if (self.parser.get_value("type") not in self.structure.hxedTypes):
                break

            self.parser.bgoto(-self.parser.get_size() + self.parser.get_value("size"))
            current = self.parser.btell()

        self.off_t.append(self.get_attrib(ModuleConstant.IMAGE_BASE), current, Offset_Info.VALID|Offset_Info.UNIT)
        self.parser.cleanup()

    # 2) read size

    def carve(self):
        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE), 1
        )

        offset = self.get_attrib(ModuleConstant.IMAGE_BASE)
        last = self.get_attrib(ModuleConstant.IMAGE_LAST)
        current = offset

        if (last == 0):
            last = self.parser.bgoto(0, os.SEEK_END)

        self.parser.bgoto(offset, os.SEEK_SET)
        self.parser.bexecute(self.structure.Header, 'int', 0, os.SEEK_CUR)
        if (self.parser.get_value("size") == 0):
            self.parser.cleanup()
            return
        self.parser.bgoto(-self.parser.get_size() + self.parser.get_value("size"))

        while (current < last):
            self.parser.bexecute(self.structure.Chunk, 'int', 0, os.SEEK_CUR)
            if (self.parser.get_value("size") == 0):
                break

            if (self.parser.get_value("type") not in self.structure.hxedTypes):
                break

            self.parser.bgoto(-self.parser.get_size() + self.parser.get_value("size"))
            current = self.parser.btell()

        self.off_t.append(self.get_attrib(ModuleConstant.IMAGE_BASE), current, Offset_Info.VALID|Offset_Info.UNIT)
        self.parser.cleanup()

    """ Interfaces """

    def module_open(self, id):  # Reserved method for multiprocessing
        super().module_open()

    def module_close(self):  # Reserved method for multiprocessing
        pass

    def set_attrib(self, key, value):  # 모듈 호출자가 모듈 속성 변경/추가하는 method interface
        self.update_attrib(key, value)

    def get_attrib(self, key, value=None):  # 모듈 호출자가 모듈 속성 획득하는 method interface
        return self.attrib.get(key)

    def execute(self, cmd=None, option=None):  # 모듈 호출자가 모듈을 실행하는 method
        ret = self.__evaluate()
        if (ret != ModuleConstant.Return.SUCCESS):
            return None
        self.__reinit__()
        self.chunk_chain()
        return self.off_t  # return <= 0 means error while collecting information

if __name__ == '__main__':

    MP4 = ModuleISOBMFF()
    try:
        MP4.set_attrib(ModuleConstant.FILE_ATTRIBUTE, sys.argv[1])  # Insert MFT File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    MP4.set_attrib(ModuleConstant.IMAGE_BASE, 0)  # Set offset of the file base
    cret = MP4.execute()
    sys.exit(0)
