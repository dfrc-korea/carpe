meta:
  id: prefetch_scca
  title: Microsoft Windows Prefetch (PF) File Format
  endian: le
  # 'https://github.com/libyal/libscca/blob/master/documentation/'
  imports:
    - prefetch_header_scca
    - prefetch_file_info_23
    - prefetch_file_info_30
    - prefetch_metric_entry_23
    - prefetch_trace_chain_entry_17
    - prefetch_volume_info_entry_23
    - prefetch_file_references_23
    - prefetch_directory_string_entry
  
  
seq:
  - id: header
    type: prefetch_header_scca
    
  # - id: file_info
  #   type: 
  #     switch-on: header.version
  #     cases:
  #       'formats::WIN_VISTA' : prefetch_file_info_23
  #       'formats::WIN_10'    : prefetch_file_info_30
          
  - id: file_info_23
    type: prefetch_file_info_23
    if: header.version == formats::WIN_VISTA
    
  - id: file_info_30
    type: prefetch_file_info_30
    if: header.version == formats::WIN_10

  - id: array_metric_23
    type: prefetch_metric_entry_23
    repeat: expr
    repeat-expr: file_info_23.number_metric_entries
    if: header.version == formats::WIN_VISTA

  - id: array_trace_chain_17
    type: prefetch_trace_chain_entry_17
    repeat: expr
    repeat-expr: file_info_23.number_trace_chain_entries
    if: header.version.to_i < formats::WIN_10.to_i

  - id: array_filepath_string_23
    size: file_info_23.size_filepath_strings + 6
    if: header.version == formats::WIN_VISTA
        
  - id: array_volume_info_23
    type: prefetch_volume_info_entry_23
    repeat: expr
    repeat-expr: file_info_23.number_volume_info_entries
    if: header.version.to_i < formats::WIN_10.to_i        
        

instances:
  volume_device_path: 
    pos: file_info_23.offset_volume_info_array + array_volume_info_23[0].offset_volume_device_path
    size: array_volume_info_23[0].number_volume_device_path_characters * 2
    type: str
    encoding: UTF-16LE

  array_file_reference_23: 
    pos: file_info_23.offset_volume_info_array + array_volume_info_23[0].offset_file_references
    type: prefetch_file_references_23
    
  array_directory_string_23: 
    pos: file_info_23.offset_volume_info_array + array_volume_info_23[0].offset_directory_strings
    type: prefetch_directory_string_entry
    repeat: expr
    repeat-expr: array_volume_info_23[0].number_directory_strings 
    
    
#   file_info:     
#     if: header.version == formats::WIN_VISTA
#     value: file_info_23

  # difat_1st:
    # if: header.size_difat > 0
    # pos: (header.ofs_difat + 1) * sector_size
    # size: sector_size
    # type: cfbf_difat_sector


enums:
  formats:
    17: win_xp
    23: win_vista
    26: win_8
    30: win_10