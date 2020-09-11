meta:
  id: prefetch_volume_info_entry_30
  title: Microsoft Windows Prefetch (PF) File Format - Volume Information Structure (v30 for Win 10)
  endian: le
  # 'https://github.com/libyal/libscca/blob/master/documentation/'
  
seq:
  - id: offset_volume_device_path
    type: u4
    doc: The offset is relative from the start of the volume information
  - id: number_volume_device_path_characters
    type: u4
  - id: time_volume_creation
    type: u8
    doc: Windows FILETIME format (number of 100-nanosecond intervals since January 1, 1601, UTC)
  - id: volume_serial
    type: u4
  - id: offset_file_references
    type: u4
  - id: size_file_references
    type: u4
  - id: offset_directory_strings
    type: u4
  - id: number_directory_strings
    type: u4
  - id: unknows1
    size: 4
  - id: unknows2
    size: 24
  - id: unknows3
    size: 4
  - id: unknows4
    size: 24
  - id: unknows5
    size: 4
    