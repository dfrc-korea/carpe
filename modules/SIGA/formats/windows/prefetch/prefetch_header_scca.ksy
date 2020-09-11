meta:
  id: prefetch_header_scca
  title: Microsoft Windows Prefetch (PF) File Format - Uncompressed PF File's Header
  endian: le
  # 'https://github.com/libyal/libscca/blob/master/documentation/'
  
seq:
  - id: version
    type: u4
    enum: formats
  - id: signature
    contents: [0x53,0x43,0x43,0x41]
    doc: Magic bytes "SCCA" that confirm that this is a SCCA (PF) file
  - id: unknown1
    size: 4
  - id: size_file
    type: u4
  - id: exe_name
    type: str
    size: 60
    encoding: UTF-16LE
  - id: hash
    size: 4
    doc: This value should correspond with the hash in the Prefetch filename
  - id: unknown2
    size: 4
    
enums:
  formats:
    17: win_xp
    23: win_vista
    26: win_8
    30: win_10

