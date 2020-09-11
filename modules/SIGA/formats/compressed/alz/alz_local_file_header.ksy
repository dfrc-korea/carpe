meta:
  id: alz_local_file_header
  title: ALZ archive file - alz_local_file_header
  endian: le
  # 'https://kippler.com/win/unalz/'
  
  
seq:
  - id: signature
    type: u4
  - id: file_name_length
    type: u2
  - id: file_attribute
    type: u1
  - id: file_time_date
    type: u4
  # <  파일 크기 필드의 크기 : 0x10, 0x20, 0x40, 0x80 각각 1byte, 2byte, 4byte, 8byte.
  # 0x01 & file_descriptor == 0x01이면 암호화
  - id: file_descriptor
    type: u1
  - id: unknown1
    type: u1
  # ///< 압축 방법 : 2 - deflate, 1 - 변형 bzip2, 0 - 압축 안함.
  - id: compresstion_method
    type: u1
  - id: unknown2
    type: u1
  - id: file_crc
    type: u4
  - id: compressed_size
    type: 
      switch-on: file_descriptor
      cases:
       0x10: u1
       0x11: u1
       0x20: u2
       0x21: u2
       0x40: u4
       0x41: u4
       0x80: u8
       0x81: u8
  - id: uncompressed_size
    type: 
      switch-on: file_descriptor
      cases:
       0x10: u1
       0x11: u1
       0x20: u2
       0x21: u2
       0x40: u4
       0x41: u4
       0x80: u8
       0x81: u8
  - id: file_name
    size: file_name_length
    type: str
    encoding: euc-kr
  - id: compressed_data
    size: compressed_size
    if: file_descriptor != 0