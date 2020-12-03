import os.path
from modules.windows_jumplist.consts import *
from modules.windows_jumplist.lib.yjSysUtils import *
from modules.windows_jumplist.lib.yjDateTime import *


def get_files(path, w='*'):
    """ 지정 경로의 파일목록을 구한다. """
    if os.path.isdir(path):
        import glob
        try:
            path = IncludeTrailingBackslash(path)
            return [v for v in glob.glob(path + w) if os.path.isfile(v)]
        finally:
            del glob
    else:
        return []


def _cast(buf, fmt):
    if debug_mode: assert type(buf) is bytes
    return cast(c_char_p(buf), POINTER(fmt)).contents


class TGUID(LittleEndianStructure):
    _fields_ = [
        ('D1', c_uint32),
        ('D2', c_ushort),
        ('D3', c_ushort),
        ('D4', c_ubyte * 8)
    ]


def GUIDToString(v):
    r = '%.8X-%.4X-%.4X-%.2X%.2X-%.2X%.2X%.2X%.2X%.2X%.2X' % (
        v.D1, v.D2, v.D3, v.D4[0], v.D4[1], v.D4[2], v.D4[3], v.D4[4], v.D4[5], v.D4[6], v.D4[7])
    return r


class TLNKFileHeader(LittleEndianStructure):
    _fields_ = [
        ('HeaderSize', c_uint32),  # 헤더의 크기로 항상 0x0000004C(76) 값
        ('CLSID', TGUID),  # 클래스 식별자(class identifier;CLSID)로 항상 00021401-0000-0000-C000-000000000046 값
        ('LinkFlags', c_uint32),  # 링크 대상의 다양한 정보에 대한 플래그
        ('FileAttrFlags', c_uint32),  # 링크 대상의 파일 특성 정보
        ('FileCreationTime', FILETIME),  # 링크 대상의 생성 시간 (TFileTime)
        ('FileAccessTime', FILETIME),  # 링크 대상의 접근 시간
        ('FileModifiedTime', FILETIME),  # 링크 대상의 쓰기 시간
        ('FileSize', c_uint32),  # 링크 대상의 크기
        ('IconIndex', c_uint32),  # 아이콘 인덱스
        ('ShowCommand', c_uint32),  # 링크가 실행될 때 응용프로그램의 동작 모드
        ('HotKey', c_short),  # 핫키 정보
        ('_Patch', c_short),  # 예약된 필드 (항상 0), Has a 0x00 entry
        ('_Reserved1', c_uint32),  # 예약된 필드 (항상 0)
        ('_Reserved2', c_uint32),  # 예약된 필드 (항상 0)
    ]


class TLinkFileLocationInfo(LittleEndianStructure):
    _fields_ = [
        ('LinkInfoSize', c_uint32),
        ('LinkInfoHeaderSize', c_uint32),
        ('LinkInfoFlags', c_uint32),
        ('OffsetVolumeTable', c_uint32),
        ('OffsetBasePath', c_uint32),
        ('OffsetNetwork', c_uint32),
        ('OffsetFinalPath', c_uint32)
    ]


class TLinkFileLocalVolumeTable(LittleEndianStructure):
    _fields_ = [
        ('VolumeTableLength', c_uint32),
        ('VolumeType', c_uint32),
        ('VolumeSerialNbr', c_uint32),
        ('OffsetVolumeName', c_uint32)
    ]


class TLinkFileNetworkVolumeTable(LittleEndianStructure):
    _fields_ = [
        ('NetVolumeLength', c_uint32),
        ('NetFlags', c_uint32),
        ('NetNameOffset', c_uint32),
        ('DeviceNameOffset', c_uint32),
        ('NetProviderType', c_uint32)
    ]


class TLNKFileParser:
    def __init__(self, srcfile, src_id, fileName='', fileCTime='', fileMTime='', fileATime=''):
        self.src_id = src_id
        self.data = None
        if srcfile == None :
            return None
        elif type(srcfile) is str:
            with open(srcfile, 'rb') as f:
                self.data = TDataAccess(f.read())
            self.fileName = srcfile
            from datetime import datetime

            self.fileCTime = datetime.fromtimestamp(os.path.getctime(srcfile))
            self.fileMTime = datetime.fromtimestamp(os.path.getmtime(srcfile))
            self.fileATime = datetime.fromtimestamp(os.path.getatime(srcfile))
        else:
            if type(srcfile) is bytes:
                self.data = TDataAccess(srcfile)
                self.fileName = fileName
            else:
                self.data = TDataAccess(srcfile.read())
                if fileName == '':
                    self.fileName = srcfile.name
                else:
                    self.fileName = fileName
            self.fileCTime = fileCTime
            self.fileMTime = fileMTime
            self.fileATime = fileATime
        self.header = _cast(self.data.read(sizeof(TLNKFileHeader)), TLNKFileHeader)

    def getAnsiStrValue(self, pos):
        data = self.data
        data.position = pos
        p = data.data.find(b'\0', data.position)
        l = p - data.position + 1
        return data.read(l).decode('cp949').rstrip('\x00')

    def getUnicodeStrValue(self, pos):
        data = self.data
        data.position = pos
        l = data.read(2, 'H')
        try:
            return data.read(l * 2).decode('utf-16')
        except:
            return ''

    def parse_data(self):
        data = self.data
        _id = 0
        sid = self.src_id

        def addItem(item, itemInfo, n=0):
            nonlocal _id
            try:
                return [sid, n, item, itemInfo]
            finally:
                _id += 1

        result = {'LinkHeaderInfo': [['sid', 'ParentIdx', 'Item', 'ItemInfo']]}
        hinfo = result['LinkHeaderInfo']
        hinfo.append(addItem(RS_LinkFileHeaderInfo, ''))

        data.position = 0
        h = _cast(data.read(sizeof(TLNKFileHeader)), TLNKFileHeader)
        hinfo.append(addItem(RS_HeaderSize, '%d (%x)' % (h.HeaderSize, h.HeaderSize)))
        hinfo.append(addItem('CLSID', GUIDToString(h.CLSID)))
        hinfo.append(addItem('Link Flags', '0x%.4X' % h.LinkFlags))
        node = _id
        hinfo.append(addItem('HasLinkTargetIDList', RS_ExistsIDListInShellHeader if (h.LinkFlags & HasLinkTargetIDList) != 0 else RS_NoExistsIDListInShellHeader,
                             node))
        hinfo.append(
            addItem('HasLinkInfo', RS_LinkInfoPresent if (h.LinkFlags & HasLinkInfo) != 0 else RS_NoLinkInfoAvailable,
                    node)
        )
        if (h.LinkFlags & HasName) != 0:
            hinfo.append(addItem('HasName', RS_ShellLinkNamePresent, node))
        if (h.LinkFlags & HasRelativePath) != 0:
            hinfo.append(addItem('HasRelativePath', RS_RelativeShellLinkPathUsed, node))
        if (h.LinkFlags & HasWorkingDir) != 0:
            hinfo.append(addItem('HasWorkingDir', RS_ShellWorkingDirEntered, node))
        if (h.LinkFlags & HasArguments) != 0:
            hinfo.append(addItem('HasArguments', RS_CommandLineArgumentsEntered, node))
        if (h.LinkFlags & HasIconLocation) != 0:
            hinfo.append(addItem('HasIconLocation', RS_IconLocationEntered, node))
        if (h.LinkFlags & IsUnicode) != 0:
            hinfo.append(addItem('IsUnicode', RS_LinkContainsUnicode, node))
        if (h.LinkFlags & ForceNoLinkInfo) != 0:
            hinfo.append(addItem('ForceNoLinkInfo', RS_LinkInfoStructureIgnored, node))
        if (h.LinkFlags & HasExpString) != 0:
            hinfo.append(addItem('HasExpString', RS_LinkSavedInEnvironmentVariableDataBlock, node))
        if (h.LinkFlags & RunInSeparateProcess) != 0:
            hinfo.append(addItem('RunInSeparateProcess', RS_RunTargetInVirtualMachine, node))
        if (h.LinkFlags & Unused1) != 0:
            hinfo.append(addItem('Unused1', 'unused? Unknown! Bit 0x800', node))
        if (h.LinkFlags & HasDarwinID) != 0:
            hinfo.append(addItem('HasDarwinID', RS_LinkHasDrawinSection, node))
        if (h.LinkFlags & RunAsUser) != 0:
            hinfo.append(addItem('RunAsUser', RS_LinkRunsAsDifferentUser, node))
        if (h.LinkFlags & HasExpIcon) != 0:
            hinfo.append(addItem('HasExpIcon', RS_LinkSavedWithIconEnvironmentDataBlock, node))
        if (h.LinkFlags & NoPidlAlias) != 0:
            hinfo.append(addItem('NoPidlAlias', RS_FileSystemLocationRepresentedInShellNamespace, node))
        if (h.LinkFlags & Unused2) != 0:
            hinfo.append(addItem('Unused2', 'unused? Unknown! Bit 0x10000', node))
        if (h.LinkFlags & RunWithShimLayer) != 0:
            hinfo.append(addItem('RunWithShimLayer', RS_ShellLinkHasShimDataBlock, node))
        if (h.LinkFlags & ForceNoLinkTrack) != 0:
            hinfo.append(addItem('ForceNoLinkTrack', RS_TrackerDataBlockIgnored, node))
        if (h.LinkFlags & EnableTargetMetadata) != 0:
            hinfo.append(addItem('EnableTargetMetadata', RS_ShellLinkCollectsTargetProperties, node))
        if (h.LinkFlags & DisableLinkPathTracking) != 0:
            hinfo.append(addItem('DisableLinkPathTracking', RS_EnvironmentVariableDataBlockIgnored, node))
        if (h.LinkFlags & DisableKnownFolderTracking) != 0:
            hinfo.append(
                addItem('DisableKnownFolderTracking', RS_SpecialFolderDataBlockNKnownFolderDataBlockIgnored, node))
        if (h.LinkFlags & DisableKnownFolderAlias) != 0:
            hinfo.append(addItem('DisableKnownFolderAlias', RS_KnownFolderDataBlock4TranslatingTargetIDList, node))
        if (h.LinkFlags & AllowLinkToLink) != 0:
            hinfo.append(addItem('AllowLinkToLink', RS_CreatingLinkReferncesAnotherLink, node))
        if (h.LinkFlags & UnaliasOnSave) != 0:
            hinfo.append(addItem('UnaliasOnSave', RS_UseUnaliased, node))
        if (h.LinkFlags & PreferEnvironmentPath) != 0:
            hinfo.append(addItem('PreferEnvironmentPath', RS_TargetIDListShouldNotStored, node))
        if (h.LinkFlags & KeepLocalIDListForUNCTarget) != 0:
            hinfo.append(addItem('KeepLocalIDListForUNCTarget', RS_StorePropertyStoreDataBlockIfTargetUNCName, node))
        if (h.LinkFlags & Unused3) != 0:
            hinfo.append(addItem('Unused3', 'unused? Unknown! Bit 0x8000000', node))
        if (h.LinkFlags & Unused4) != 0:
            hinfo.append(addItem('Unused4', 'unused? Unknown! Bit 0x10000000', node))
        if (h.LinkFlags & Unused5) != 0:
            hinfo.append(addItem('Unused5', 'unused? Unknown! Bit 0x20000000', node))
        if (h.LinkFlags & Unused6) != 0:
            hinfo.append(addItem('Unused6', 'unused? Unknown! Bit 0x40000000', node))
        if (h.LinkFlags & Unused7) != 0:
            hinfo.append(addItem('Unused7', 'unused? Unknown! Bit 0x80000000', node))
        if h.FileAttrFlags != 0:
            hinfo.append(addItem(RS_TargetFileProp, str(h.FileAttrFlags)))
        if (h.FileCreationTime.LowDateTime + h.FileCreationTime.HighDateTime) != 0:
            t = filetime_to_datetime(FileTime(h.FileCreationTime), 0).isoformat()
            hinfo.append(addItem(RS_TargetFileCreateDT, t))
        if (h.FileAccessTime.LowDateTime + h.FileAccessTime.HighDateTime) != 0:
            t = filetime_to_datetime(FileTime(h.FileAccessTime), 0).isoformat()
            hinfo.append(addItem(RS_TargetFileAccessDT, t))
        if (h.FileModifiedTime.LowDateTime + h.FileModifiedTime.HighDateTime) != 0:
            t = filetime_to_datetime(FileTime(h.FileModifiedTime), 0).isoformat()
            hinfo.append(addItem(RS_TargetFileModifyDT, t))
        if h.FileSize != 0:
            hinfo.append(addItem(RS_TargetFileSize, str(h.FileSize)))
        hinfo.append(addItem(RS_IconIndex, str(h.IconIndex)))
        hinfo.append(addItem(RS_HotKey, str(h.HotKey)))
        hinfo.append(addItem(RS_ReservedField1, str(h._Patch)))
        hinfo.append(addItem(RS_ReservedField2, str(h._Reserved1)))
        hinfo.append(addItem(RS_ReservedField3, str(h._Reserved2)))
        if (h.LinkFlags & HasLinkTargetIDList) != 0:
            targetIDListSize = data.read(2, 'H')
            hinfo.append(addItem('Target ID List', 'Pos=0x%.4X, Size=%d' % (data.position - 2, targetIDListSize)))
            node = _id
            if targetIDListSize > 0:
                i = 1
                while data.position < data.size:
                    listLen = data.read(2, 'H')
                    if listLen <= 2:
                        hinfo.append(addItem('Terminator found', '', node))
                        break
                    hinfo.append(
                        addItem('ID List entry - %.2d' % i, 'Pos=0x%.4X, Size=%d' % (data.position - 2, listLen), node))
                    data.position = data.position + (listLen - 2)
                    i += 1

        if (h.LinkFlags & HasLinkInfo) != 0:
            hinfo.append(addItem('Link Info List', 'Pos=0x%.4X' % data.position))
            node = _id
            LFLInfo = _cast(data.read(sizeof(TLinkFileLocationInfo)), TLinkFileLocationInfo)
            hinfo.append(addItem('Table Length', '%d (%x)' % (LFLInfo.LinkInfoSize, LFLInfo.LinkInfoSize), node))
            hinfo.append(
                addItem('Header Length', '%d (%x)' % (LFLInfo.LinkInfoHeaderSize, LFLInfo.LinkInfoHeaderSize), node))
            if LFLInfo.LinkInfoFlags != 0:
                hinfo.append(addItem('Link Info Flags', 'Pos=0x%.4X' % data.position, node))
                subNode = _id
                if (LFLInfo.LinkInfoFlags & VolumeIDAndLocalBasePath) != 0:
                    pass
                if (LFLInfo.LinkInfoFlags & CommonNetworkRelativeLinkAndPathSuffix) != 0:
                    pass
                else:
                    hinfo.append(addItem(RS_TargetFilePath, RS_Local, subNode))
                if (LFLInfo.LinkInfoFlags & VolumeIDAndLocalBasePath) != 0:
                    hinfo.append(addItem(RS_TargetFilePathInfo, 'Pos=0x%.4X' % data.position, subNode))
                    subNode = _id
                    if LFLInfo.LinkInfoHeaderSize > 0x1c:
                        data.position += 4
                        data.position += 4

                    LFLVTable = _cast(data.read(sizeof(TLinkFileLocalVolumeTable)), TLinkFileLocalVolumeTable)
                    hinfo.append(addItem(RS_VolumeName, self.getAnsiStrValue(data.position), subNode))
                    volumeType = ('', 'No root directory', 'Removable (Floppy, Zip, etc..)', 'Fixed (Hard disk)',
                                  'Remote (Network drive)', 'CD-ROM', 'Ram drive')
                    hinfo.append(addItem(RS_VolumeType, volumeType[LFLVTable.VolumeType] if LFLVTable.VolumeType < len(
                        volumeType) else 'Unknown', subNode))
                    hinfo.append(addItem('Drive Serial Number', '%x' % LFLVTable.VolumeSerialNbr, subNode))

                if (LFLInfo.LinkInfoFlags & CommonNetworkRelativeLinkAndPathSuffix) != 0:
                    hinfo.append(addItem(RS_TargetFilePathInfo, 'Pos=0x%.4X' % data.position, subNode))
                    subNode = _id
                    LFNVTable = _cast(data.read(sizeof(TLinkFileNetworkVolumeTable)), TLinkFileNetworkVolumeTable)
                    if LFNVTable.NetNameOffset > 0x14:
                        data.position += 4
                        data.position += 4
                    if (LFNVTable.NetFlags & ValidNetType) != 0:
                        netProviderType = {
                            0x00020000: 'WNNC_NET_SMB',
                            0x00440000: 'WNNC_NET_NDFS',
                            0x001A0000: 'WNNC_NET_AVID',
                            0x001B0000: 'WNNC_NET_DOCUSPACE',
                            0x001C0000: 'WNNC_NET_MANGOSOFT',
                            0x001D0000: 'WNNC_NET_SERNET',
                            0x001E0000: 'WNNC_NET_RIVERFRONT1',
                            0x001F0000: 'WNNC_NET_RIVERFRONT2',
                            0x00200000: 'WNNC_NET_DECORB',
                            0x00210000: 'WNNC_NET_PROTSTOR',
                            0x00220000: 'WNNC_NET_FJ_REDIR',
                            0x00230000: 'WNNC_NET_DISTINCT',
                            0x00240000: 'WNNC_NET_TWINS',
                            0x00250000: 'WNNC_NET_RDR2SAMPLE',
                            0x00260000: 'WNNC_NET_CSC',
                            0x00270000: 'WNNC_NET_3IN1',
                            0x00290000: 'WNNC_NET_EXTENDNET',
                            0x002A0000: 'WNNC_NET_STAC',
                            0x002B0000: 'WNNC_NET_FOXBAT',
                            0x002C0000: 'WNNC_NET_YAHOO',
                            0x002D0000: 'WNNC_NET_EXIFS',
                            0x002E0000: 'WNNC_NET_DAV',
                            0x002F0000: 'WNNC_NET_KNOWARE',
                            0x00300000: 'WNNC_NET_OBJECT_DIRE',
                            0x00310000: 'WNNC_NET_MASFAX',
                            0x00320000: 'WNNC_NET_HOB_NFS',
                            0x00330000: 'WNNC_NET_SHIVA',
                            0x00340000: 'WNNC_NET_IBMAL',
                            0x00350000: 'WNNC_NET_LOCK',
                            0x00360000: 'WNNC_NET_TERMSRV',
                            0x00370000: 'WNNC_NET_SRT',
                            0x00380000: 'WNNC_NET_QUINCY',
                            0x00390000: 'WNNC_NET_OPENAFS',
                            0x003A0000: 'WNNC_NET_AVID1',
                            0x003B0000: 'WNNC_NET_DFS',
                            0x003C0000: 'WNNC_NET_KWNP',
                            0x003D0000: 'WNNC_NET_ZENWORKS',
                            0x003E0000: 'WNNC_NET_DRIVEONWEB',
                            0x003F0000: 'WNNC_NET_VMWARE',
                            0x00400000: 'WNNC_NET_RSFX',
                            0x00410000: 'WNNC_NET_MFILES',
                            0x00420000: 'WNNC_NET_MS_NFS',
                            0x00430000: 'WNNC_NET_GOOGLE'
                        }
                        v = netProviderType.get(LFNVTable.NetProviderType)
                        if v == None: v = 'Unknown - %.8X (%d)' % (LFNVTable.NetProviderType, LFNVTable.NetProviderType)
                        hinfo.append(addItem('Network Provider Type', v, subNode))
                    hinfo.append(addItem('Network Relative Link', self.getAnsiStrValue(data.position), subNode))
                    hinfo.append(addItem('Net Name', self.getAnsiStrValue(data.position), subNode))
                    return result
                hinfo.append(addItem('Base Path', self.getAnsiStrValue(data.position), subNode))
                v = self.getAnsiStrValue(data.position)
                if v != '':
                    hinfo.append(addItem('Common Base Path', self.getUnicodeStrValue(data.position), subNode))
                if (h.LinkFlags & HasName) != 0:
                    hinfo.append(addItem('Name', self.getUnicodeStrValue(data.position), subNode))
                if (h.LinkFlags & HasRelativePath) != 0:
                    hinfo.append(addItem('Relative Path', self.getUnicodeStrValue(data.position), subNode))
                if (h.LinkFlags & HasWorkingDir) != 0:
                    hinfo.append(addItem('Working Directory', self.getUnicodeStrValue(data.position), subNode))
                if (h.LinkFlags & HasArguments) != 0:
                    hinfo.append(addItem('Arguments', self.getUnicodeStrValue(data.position), subNode))
                if (h.LinkFlags & HasIconLocation) != 0:
                    hinfo.append(addItem('Icon Location', self.getUnicodeStrValue(data.position), subNode))
        stpos = data.position
        while stpos <= data.size - 10:
            size = data.read(4, '<I')
            if size == 0:
                return result
            blk_sig = data.read(4, '<I')
            if blk_sig == 0xa0000003:
                hinfo.append(addItem('Distributed Tracker', 'Pos=0x%.4X' % data.position))
                node = _id
                sp = stpos + 16  # machine_id
                ep = data.data[sp:].find(b'\x00')
                if ep != -1:
                    ep += sp
                    hinfo.append(addItem('Machine Id', data.data[sp:ep].decode('utf-8'), node))
                sp = stpos + 80 + 10  # mac_address
                id = data.data[sp:sp + 6]
                hinfo.append(
                    addItem('Mac Address', '%.2x:%.2x:%.2x:%.2x:%.2x:%.2x' % (id[0], id[1], id[2], id[3], id[4], id[5]),
                            node)
                )
                pass
            data.position = stpos + size
            stpos = data.position
        return result

    def parse(self):
        fn = self.fileName
        result = {'LinkFileInfo': [['sid', 'Name', 'Path', 'CreationTime', 'ModifiedTime', 'AccessTime']]}
        finfo = result['LinkFileInfo']
        finfo.append(
            [self.src_id, ExtractFileName(fn), ExtractFilePath(fn), self.fileCTime, self.fileMTime, self.fileATime])
        if debug_mode:
            assert len(finfo[0]) == len(finfo[1])
        result.update(self.parse_data())
        return result


def main(file, file_name):
    LNKFileParser = TLNKFileParser(file, 0, fileName=file_name)
    if LNKFileParser.data is None:
        return False
    if LNKFileParser.header.HeaderSize != 76:
        return False
    result = LNKFileParser.parse()

    return result
