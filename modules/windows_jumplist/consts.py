RS_LinkFIleInfo = 'Link 파일 정보'
RS_Name = '이름'
RS_Path = '경로'
RS_CreateDT = '생성일'
RS_AccessDT = '사용일'
RS_ModifyDT = '수정일'
RS_LinkFileHeaderInfo = 'Link 파일 헤더 정보'
RS_HeaderSize = '헤더 크기'
RS_ExistsIDListInShellHeader = 'ShellLinkHeader에 ID List가 있습니다.'
RS_NoExistsIDListInShellHeader = 'ShellLinkHeader에 ID List가 존재하지 않습니다.'
RS_LinkInfoPresent = 'Link Info가 존재합니다.'
RS_NoLinkInfoAvailable = 'Link Info가 존재하지 않습니다.'
RS_ShellLinkNamePresent = 'Shell link 이름이 존재합니다.'
RS_RelativeShellLinkPathUsed = 'Shell link 경로가 사용됩니다.'
RS_ShellWorkingDirEntered = 'Shell Working Directory가 입력되었습니다.'
RS_CommandLineArgumentsEntered = 'Command line 인수가 입력되었습니다.'
RS_IconLocationEntered = 'Icon 위치가 입력되었습니다.'
RS_LinkContainsUnicode = 'Link에 유니코드가 포함되어 있습니다.'
RS_LinkInfoStructureIgnored = 'Link 정보 구조가 무시됩니다.'
RS_LinkSavedInEnvironmentVariableDataBlock = 'Link는 EnvironmentVariableDataBlock에 저장됩니다.'
RS_RunTargetInVirtualMachine = '가상 컴퓨터에서 대상 실행 (16 비트 응용 프로그램)'
RS_LinkHasDrawinSection = 'Link에 Darwin section이 있습니다.'
RS_LinkRunsAsDifferentUser = 'Link가 다른 사용자로 실행됩니다.'
RS_LinkSavedWithIconEnvironmentDataBlock = 'Link는 IconEnvironmentDataBlock과 함께 저장됩니다.'
RS_FileSystemLocationRepresentedInShellNamespace = '파일 시스템 위치가 shell namespace에 표시됩니다.'
RS_ShellLinkHasShimDataBlock = 'Shell link에 ShimDataBlock이 있습니다.'
RS_TrackerDataBlockIgnored = 'TrackerDataBlock이 무시됩니다.'
RS_ShellLinkCollectsTargetProperties = 'Shell link가 대상 속성을 수집합니다.'
RS_EnvironmentVariableDataBlockIgnored = 'EnvironmentVariableDataBlock이 무시됩니다.'
RS_SpecialFolderDataBlockNKnownFolderDataBlockIgnored = 'SpecialFolderDataBlock 및 KnownFolderDataBlock이 무시됩니다.'
RS_KnownFolderDataBlock4TranslatingTargetIDList = '대상 ID List 변환에 KnownFolderDataBlock를 사용합니다.'
RS_CreatingLinkReferncesAnotherLink = '다른 Link를 참조하는 Link를 만들 수 있습니다.'
RS_UseUnaliased = 'Link를 저장하기 위해 Alias화 되지 않은 형식의 알려진 폴더 또는 대상 ID List를 사용하십시오.'
RS_TargetIDListShouldNotStored = '대상 ID List를 저장해서는 안됩니다 (SHOULD NOT SHOULD NOT).'
RS_StorePropertyStoreDataBlockIfTargetUNCName = '대상이 UNC 이름 인 경우 PropertyStoreDataBlock을 저장하십시오.'
RS_TargetFileProp = '대상 파일 속성'
RS_TargetFileCreateDT = '대상 파일 생성일'
RS_TargetFileAccessDT = '대상 파일 사용일'
RS_TargetFileModifyDT = '대상 파일 수정일'
RS_TargetFileSize = '대상 파일 크기'
RS_IconIndex = '아이콘 인덱스'
RS_HotKey = '바로 가기 키'
RS_ReservedField1 = '예약 필드1'
RS_ReservedField2 = '예약 필드2'
RS_ReservedField3 = '예약 필드3'
RS_TargetFilePath = '대상 파일 위치'
RS_Network = '네트워크'
RS_Local = '로컬'
RS_TargetFilePathInfo = '대상 파일 경로 정보'
RS_VolumeName = '볼륨 이름'
RS_VolumeType = '볼륨 종류'

HasLinkTargetIDList         = 0x1     # The shell link is saved with an item ID list (IDList).
HasLinkInfo                 = 0x2     # The shell link is saved with link information or without information. The header is available.
HasName                     = 0x4     # The shell link is saved with a name string.
HasRelativePath             = 0x8     # The shell link is saved with a relative path string.
HasWorkingDir               = 0x10    # The shell link is saved with a working directory string.
HasArguments                = 0x20    # The shell link is saved with command line arguments.
HasIconLocation             = 0x40    # The shell link is saved with an icon location string.
IsUnicode                   = 0x80    # The shell link contains Unicode encoded strings. This bit SHOULD be set.

ForceNoLinkInfo             = 0x100   # The LinkInfo structure is ignored.
HasExpString                = 0x200   # The shell link is saved with an EnvironmentVariableDataBlock
RunInSeparateProcess        = 0x400   # The target is run in a separate virtual machine when launching a link target that is a 16-bit application.
Unused1                     = 0x800   # A bit that is undefined and MUST be ignored.
HasDarwinID                 = 0x1000  # The shell link is saved with a DarwinDataBlock
RunAsUser                   = 0x2000  # The application is run as a different user when the target of the shell link is activated.
HasExpIcon                  = 0x4000  # The shell link is saved with an IconEnvironmentDataBlock
NoPidlAlias                 = 0x8000  # The file system location is represented in the shell namespace when the path to an item is parsed into an IDList.

Unused2                     = 0x10000  # A bit that is undefined and MUST be ignored.
RunWithShimLayer            = 0x20000  # The shell link is saved with a ShimDataBlock
ForceNoLinkTrack            = 0x40000  # The TrackerDataBlock is ignored
EnableTargetMetadata        = 0x80000  # The shell link attempts to collect target properties and store them in
                                       #    the PropertyStoreDataBlock (section 2.5.7) when the link target is set.
DisableLinkPathTracking     = 0x100000   # The EnvironmentVariableDataBlock is ignored.
DisableKnownFolderTracking  = 0x200000   # The SpecialFolderDataBlock (section 2.5.9) and the KnownFolderDataBlock are ignored when loading the shell link.
DisableKnownFolderAlias     = 0x400000   # If the link has a KnownFolderDataBlock, the unaliased form of the known folder IDList SHOULD be used when
                                         #    translating the target IDList at the time that the link is loaded.
AllowLinkToLink             = 0x800000   # Creating a link that references another link is enabled. Otherwise, specifying a link as the target IDList SHOULD NOT be allowed

UnaliasOnSave               = 0x1000000  # When saving a link for which the target IDList is under a known folder, either the unaliased form of that known folder or the target IDList SHOULD be used.
PreferEnvironmentPath       = 0x2000000  # The target IDList SHOULD NOT be stored; instead, the path specified in the EnvironmentVariableDataBlock SHOULD be used to refer to the target.
KeepLocalIDListForUNCTarget = 0x4000000  # When the target is a UNC name that refers to a location on a local machine, the local path IDList in the PropertyStoreDataBlock
                                         #      SHOULD be stored, so it can be used when the link is loaded on the local machine.
Unused3                     = 0x8000000  # A bit that is undefined and MUST be ignored.
Unused4                     = 0x10000000 # A bit that is undefined and MUST be ignored.
Unused5                     = 0x20000000 # A bit that is undefined and MUST be ignored.
Unused6                     = 0x40000000 # A bit that is undefined and MUST be ignored.
Unused7                     = 0x80000000 # A bit that is undefined and MUST be ignored.

VolumeIDAndLocalBasePath = 0x1
CommonNetworkRelativeLinkAndPathSuffix = 0x2

ValidDevice = 0x1
ValidNetType = 0x2
