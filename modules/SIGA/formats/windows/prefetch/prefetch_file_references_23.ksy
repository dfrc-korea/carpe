meta:
  id: prefetch_file_references_23
  title: Microsoft Windows Prefetch (PF) File Format - File References Structure (v23)
  endian: le
  # 'https://github.com/libyal/libscca/blob/master/documentation/'
  
seq:
  - id: unknown
    size: 4
  - id: number_file_references
    type: u4
  - id: array_file_references
    type: file_ref
    repeat: expr
    repeat-expr: number_file_references

types:
  file_ref:
    seq:
      - id: value
        type: u8
      # - id: mft_entry_number
      #   size: 6
      # - id: sequence_number
      #   type: u2
    
    instances:
      mft_entry_number:
        value: 'value & 0x0000FFFFFFFFFFFF'
      sequence_number:
        value: '(value & 0xFFFF000000000000) >> 48'
          
  

