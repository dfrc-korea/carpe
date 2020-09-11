meta:
  id: egg_file_header
  title: EST soft EGG File Format - EGG's File Header
  endian: le
  # https://web.archive.org/web/20130402232948/http://sdn.altools.co.kr/etc/EGG_Specification.zip
  
seq:
  - id: signature
    type: u4
  - id: file_id
    type: u4
    doc: Unique value for each header (Includes 0)
  - id: file_length
    type: u8
    doc: Total size of the file