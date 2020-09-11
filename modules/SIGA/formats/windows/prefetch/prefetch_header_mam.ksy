meta:
  id: prefetch_header_mam
  title: Microsoft Windows Prefetch (PF) File Format - Compressed PF File's Header
  endian: le
  # 'https://github.com/libyal/libscca/blob/master/documentation/'
  
  
seq:
  - id: signature
    contents: [0x4d, 0x41, 0x4d, 0x04]
    doc: Magic bytes "MAM\x04" that confirm that this is a MAM (PF) file
  - id: size_uncompressed_data
    type: u4
    doc: Total uncompressed data size
  - id: data_compressed
    size-eos: true
    doc: LZXPRESS Huffman compressed data
  
  