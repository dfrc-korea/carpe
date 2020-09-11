meta:
  id: prefetch_file_info_30
  title: Microsoft Windows Prefetch (PF) File Format - File Information Structure (v30)
  endian: le
  # 'https://github.com/libyal/libscca/blob/master/documentation/'
  
seq:
  - id: offset_metric_array
    type: u4
    doc: The offset is relative to the start of the file
  - id: number_metric_entries
    type: u4
  - id: offset_trace_chain_array
    type: u4
    doc: The offset is relative to the start of the file
  - id: number_trace_chain_entries
    type: u4
  - id: offset_filepath_strings
    type: u4
    doc: The offset is relative to the start of the file
  - id: size_filepath_strings
    type: u4
  - id: offset_volume_info_array
    type: u4
    doc: The offset is relative to the start of the file
  - id: number_volume_info_entries
    type: u4
  - id: size_volume_info
    type: u4
  - id: unknown1
    size: 8
  - id: time_last_run
    type: u8
    doc: Windows FILETIME format (number of 100-nanosecond intervals since January 1, 1601, UTC)
    repeat: expr
    repeat-expr: 8
  - id: unknown2
    size: 8
  - id: count_run
    type: u4
  - id: unknown3
    size: 4
  - id: unknown4
    size: 4
  - id: unknown5
    size: 88
