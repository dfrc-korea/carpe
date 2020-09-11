meta:
  id: prefetch_trace_chain_entry_30
  title: Microsoft Windows Prefetch (PF) File Format - Trace Chain Array Structure (v30 for Win 10)
  endian: le
  # 'https://github.com/libyal/libscca/blob/master/documentation/'
  
seq:
  - id: count_loaded_blocks
    type: u4
    doc: Total number of blocks loaded (or fetched)
  - id: unknows1
    size: 1
  - id: unknows2
    size: 1
  - id: unknows3
    size: 2
