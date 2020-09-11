meta:
  id: egg_windows_file_information
  title: EST soft EGG File Format - EGG's Windows File Information
  endian: le
  # https://web.archive.org/web/20130402232948/http://sdn.altools.co.kr/etc/EGG_Specification.zip
  
seq:
  - id: signature
    type: u4
  - id: bit_flags
    type: u1
  - id: size
    type: u2
  - id: last_modified_datatime
    type: u8
    doc: 100-nanosecond Time since the Epoch (00:00:00 UTC, January 1, 1601)
  - id: attribute
    type: u1
    