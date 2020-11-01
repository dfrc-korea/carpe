#-*- coding: utf-8 -*-
# http://www.multiweb.cz/twoinches/MP3inside.htm
#!/usr/bin/python3

#!/Author : Gibartes

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface
from structureReader import structureReader as sr
from collections     import OrderedDict
import os,sys,platform

struct_tag_v1       = sr.cref(["signature","name","artist","album","year","comment","genre"],[3,30,30,30,4,30,1],name="struct_tag_v1")
struct_tag_v2       = sr.cref(["signature","major","minor","flags","tag_size"],[3,1,1,1,4],name="struct_tag_v2")
struct_frame_header = sr.cref(["frame"],[4],name="struct_frame_header")
struct_frame        = sr.cref(["id","size","flag"],[4,4,2],name="struct_frame")
struct_frame_vbr    = sr.cref(["signature","reserved","flags","frames","length","toc","scale"],[4,36,4,4,4,100,4],name="struct_frame_vbr")

class MP3Structure(object):
    FOOTER_BE   = 0x00FFFBE4
    FOOTER_LE   = 0xE4FBFF00
    FOOTER_BIN  = b'\xff\xfb\xe4'
    TAG1        = b'TAG'
    TAG2        = b'ID3'

    bitRateIndex = {
            0:0,
            1:32,
            2:40,
            3:48,
            4:56,
            5:64,
            6:80,
            7:96,
            8:112,
            9:128,
            10:160,
            11:192,
            12:224,
            13:256,
            14:320,
            15:0,
    }
    samplingRateIndex = {
            0:44100,
            1:48000,
            2:32000,
    }

    frameIdentifier   = [
        b'TRCK',b'TENC',b'WXXX',b'TCOP',b'TOPE',b'TCOM',
        b'TCON',b'COMM',b'TYER',b'TALB',b'TPE1',b'TIT2',
        b'TPOS',b'TXXX',b'TSSE',b'APIC',b'PRIV',b'USLT'
    ]

    def __init__(self):
        # TAG
        self.TagV1      = OrderedDict({
            "signature" : [ 0, 3,None],  # TAG
            "name"      : [ 3,30,None],  # Song Name
            "artist"    : [33,30,None],  # Artist
            "album"     : [63,30,None],  # Album
            "year"      : [93, 4,None],  # Year
            "comment"   : [97,30,None],  # Comment
            "genre"     : [127,1,None],  # Genre
        })
        self.TagV2      = OrderedDict({
            "signature" : [0, 3,None],  # ID3
            "major"     : [3, 1,None],  # ID3 Major
            "minor"     : [4, 1,None],  # ID3 Minor
            "flags"     : [5, 1,None],  # 7:Unsync,6:Extended,5:Experimental,4:Footer
            "tag_size"  : [6, 4,None],  # Header Size (Excl Footer Signature)
        })
        self.FrameHeader = OrderedDict({
            "frame"  : [0, 4,None],
            # AAAAAAAA AAABBCCD EEEEFFGH IIJJKLMM
            # A: Frame synchronizer
            # B: MPEG version ID
            # C: Layer
            # D: CRC Protection
            # E: Bitrate Index
            # F: Sampling rate frequency index
            # G: Padding
            # H: Private Bit
            # I: Channel
            # J: Mode extension
            # K: Copyright
            # L: Original
            # M: Emphasis
            # FrameLen = int(144*BitRate/SampleRate)+Padding
        })
        self.TagFrames   = OrderedDict({
            "id"        :[0,4,None],
            "size"      :[4,4,None],
            "flag"      :[8,2,None],
            # Frame identifier consist of four characters. 
        })
        self.VBRFrame    = OrderedDict({
            "signature":[  0,  4,None],
            "reserved" :[  4, 36,None],
            "flags"    :[ 40,  4,None],
            "frames"   :[ 44,  4,None],
            "length"   :[ 48,  4,None],
            "toc"      :[ 52,100,None],
            "scale"    :[152,  4,None],
        })

    @staticmethod
    def constant(_long):
        return (_long&0xFFFF0000)>>16
    @staticmethod
    def getFrameLen(bitrate,samplerate,padding):
        return int(int((144*bitrate*1000)/samplerate)+padding)
    @staticmethod
    def rate(_long):
        return ((_long&0xF000)>>12,(_long&0x0C00)>>10,(_long&0x0200)>>9)
    @staticmethod
    def frameLen(_long):
        b,s,p = MP3Structure.rate(_long)
        try:return MP3Structure.getFrameLen(MP3Structure.bitRateIndex.get(b,0),
                                        MP3Structure.samplingRateIndex.get(s,0),p)
        except:return 0
    @staticmethod
    def findMSB(n): 
        n|=n>>1
        n|=n>>2
        n|=n>>4
        n|=n>>8
        n|=n>>16
        n+=1
        return (n>>1)

class ModuleMP3(ModuleComponentInterface):

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.parser     = sr.StructureReader()
        self.structure  = MP3Structure()

        self.set_attrib(ModuleConstant.NAME,"mp3")
        self.set_attrib(ModuleConstant.VERSION,"0.1")
        self.set_attrib(ModuleConstant.AUTHOR,"HK")
    
        self.off_t           = Offset_Info()
        self.off_t.name      = "mp3"    # alias
        self.off_t.signature = "mp3"    # signature in C_defy.SIGNATURE

    def __reinit__(self):
        fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.off_t.clear()

    def __del__(self):
        self.parser.cleanup()

    """ Module Methods """

    def __evaluate(self):
        fn = self.attrib.get(ModuleConstant.FILE_ATTRIBUTE)
        if(fn==None):
            return ModuleConstant.Return.EINVAL_ATTRIBUTE
        try:
            fd = os.open(fn,os.O_RDONLY)
            os.close(fd)
        except:return ModuleConstant.Return.EINVAL_FILE
        return ModuleConstant.Return.SUCCESS

    def carve(self):
        self.__reinit__()
        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE),1
        )
        opflag  = False
        base    = self.get_attrib(ModuleConstant.IMAGE_BASE)
        last    = self.get_attrib(ModuleConstant.IMAGE_LAST)
        offset  = base
        if(last==0):
            last= self.parser.bgoto(0,os.SEEK_END)
        
        fileSize = 0
        
        self.parser.bgoto(offset,os.SEEK_SET)
        self.parser.bexecute(self.structure.TagV2,'byte',offset,os.SEEK_SET)

        if(self.parser.get_value("signature")==self.structure.TAG2):
            if(self.parser.byte2int(self.parser.get_value("major"))>3):
                tagLen = self.parser.byte2int(self.parser.get_value("tag_size"),order='big')
                s      = self.structure.findMSB(tagLen)
                tok    = False
                if(s<257):pass
                else:tagLen = tagLen-s+int(s/2)  # TagLen = TagLen-MSB+(MSB/2)

                _current = self.parser.btell()
                
                if(tagLen>last):
                    tok = True
                else:
                    self.parser.bgoto(tagLen)
                    checkTagLast = self.parser.bread_raw(0,1)
                    # Check audio frame header which has the first synchro Byte FF)
                    if(checkTagLast!=b'\xFF'):
                        tok = True
                    self.parser.bgoto(_current,os.SEEK_SET)

                if(tok):
                    while(_current<last):
                        self.parser.bexecute(self.structure.TagFrames,'byte',0,os.SEEK_CUR)
                        self.parser.print()
                        jmp = self.parser.byte2int(self.parser.get_value('size'),order='big')
                        if(jmp==0):
                            break
                        if(jmp>last-_current):
                            return False
                        self.parser.bgoto(jmp)
                        _current = self.parser.btell()
                    while(1):
                        buff = self.parser.bread_raw(1,os.SEEK_CUR)
                        if(buff==b'\xFF'):
                            self.parser.bgoto(-1)
                            break
                        if(self.parser.btell()>=last):
                            return False
                    opflag  = True

                else:
                    self.parser.bgoto(tagLen)
                    checkTagLast = self.parser.bread_raw(0,1)
                    # Check audio frame header which has the first synchro Byte FF)
                    if(checkTagLast==b'\xFF'):
                        self.parser.bgoto(-1)
                        opflag  = True
            else:
                while(1):
                    self.parser.bexecute(self.structure.TagFrames,'byte',0,os.SEEK_CUR)
                    if(self.parser.get_value('id') not in MP3Structure.frameIdentifier):
                        self.parser.bgoto(-self.parser.get_size())
                        break   
                    self.parser.bgoto(self.parser.byte2int(self.parser.get_value('size'),'big'))
                
                while(1):
                        buff = self.parser.bread_raw(1,os.SEEK_CUR)
                        if(buff==b'\xFF'):
                            self.parser.bgoto(-1)
                            break
                        if(self.parser.btell()>=last):
                            return False # TAG ONLY
                opflag  = True

        elif(self.parser.get_value("signature")==self.structure.TAG1):
            s^elf.parser.bexecute(self.structure.TagV1,'byte',offset,os.SEEK_SET)
            checkTagLast = self.parser.bread_raw(0,1)
            # Check audio frame header which has the first synchro Byte FF)
            if(checkTagLast==b'\xFF'):
                self.parser.bgoto(-1)
                opflag  = True

        if(opflag==False):
            self.parser.cleanup()
            return False

        fileSize += self.parser.btell()
        offset= self.parser.btell()
        const = self.parser.byte2int(self.parser.bread_raw(0,2),order='big')
        self.parser.bgoto(-2)
        while(offset<last):
            res   = self.parser.bread_raw(0,4)
            if(res==False):
                break
            res   = self.parser.byte2int(res,order='big')
            temp  = self.structure.constant(res)
            frame = self.structure.frameLen(res)
            if(frame==0):
                break
            if(temp!=const):
                break
            fileSize+=frame
            offset+=frame
            self.parser.bgoto(frame-4)
        
        self.parser.bgoto(-4)
        res   = self.parser.bread_raw(0,3)
        self.off_t.append(base,fileSize,Offset_Info.VALID|Offset_Info.UNIT)
        self.parser.cleanup()

    """ Interfaces """

    def module_open(self,id):               # Reserved method for multiprocessing
        super().module_open()

    def module_close(self):                 # Reserved method for multiprocessing
        pass

    def set_attrib(self,key,value):         # 모듈 호출자가 모듈 속성 변경/추가하는 method interface
        self.update_attrib(key,value)

    def get_attrib(self,key,value=None):    # 모듈 호출자가 모듈 속성 획득하는 method interface
        return self.attrib.get(key)

    def execute(self,cmd=None,option=None): # 모듈 호출자가 모듈을 실행하는 method
        ret = self.__evaluate()
        if(ret!=ModuleConstant.Return.SUCCESS):
            return None
        self.carve()
        return self.off_t                  # return <= 0 means error while collecting information


if __name__ == '__main__':

    mp3 = ModuleMP3()
    try:
        mp3.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert MFT File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    mp3.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    cret = mp3.execute()
    print(cret.contents)
    sys.exit(0)
