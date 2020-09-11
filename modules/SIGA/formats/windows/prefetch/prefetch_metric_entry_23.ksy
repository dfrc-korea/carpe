meta:
  id: prefetch_metric_entry_23
  title: Microsoft Windows Prefetch (PF) File Format - Metric Array Structure (v23, v26 and v30)
  endian: le
  # 'https://github.com/libyal/libscca/blob/master/documentation/'
  
seq:
  - id: unknown1
    size: 4
  - id: unknown2
    size: 4
  - id: unknown3
    size: 4
  - id: offset_filename
    type: u4
    doc: The offset is relative to the start of the file
  - id: size_filename
    type: u4
    doc: Does not include the end-of-string character
  - id: unknown4
    size: 4
  - id: file_reference
    type: file_ref
    doc: Contains an NTFS file reference of the file corresponding to the filename string or 0 if not set

types:
  file_ref:
    seq:
      - id: value
        type: u8    
    instances:
      mft_entry_number:
        value: 'value & 0x0000FFFFFFFFFFFF'
      sequence_number:
        value: '(value & 0xFFFF000000000000) >> 48'
