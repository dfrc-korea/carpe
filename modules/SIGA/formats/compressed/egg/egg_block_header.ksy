meta:
  id: egg_block_header
  title: EST soft EGG File Format - EGG's Block Header
  endian: le
  # https://web.archive.org/web/20130402232948/http://sdn.altools.co.kr/etc/EGG_Specification.zip
  
seq:
  - id: signature
    type: u4
  - id: compress_method
    type: u2
    doc: 0 byte -> Algorithm Number(0-Store, 1-Deflate, 2-Bzip2, 3-AZO, 4-LZMA)
  - id: uncompress_size
    type: u4
  - id: compress_size
    type: u4
  - id: crc32
    type: u4
  - id: end_of_block_header
    type: u4
  - id: compressed_data
    size: compress_size