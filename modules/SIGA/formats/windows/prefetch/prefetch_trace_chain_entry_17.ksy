meta:
  id: prefetch_trace_chain_entry_17
  title: Microsoft Windows Prefetch (PF) File Format - Trace Chain Array Structure (v17)
  endian: le
  # 'https://github.com/libyal/libscca/blob/master/documentation/'
  
seq:
  - id: index_next_entry
    type: u4
    doc: Contains the next trace chain array entry index in the chain, where the first entry index starts with 0, or -1 (0xffffffff) for the end-of-chain.
  - id: count_loaded_blocks
    type: u4
    doc: Total number of blocks loaded (or fetched)
  - id: unknows1
    size: 1
  - id: unknows2
    size: 1
  - id: unknows3
    size: 2
