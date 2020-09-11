meta:
  id: egg_header
  title: EST soft EGG File Format - EGG's Header
  endian: le
  # https://web.archive.org/web/20130402232948/http://sdn.altools.co.kr/etc/EGG_Specification.zip
  
seq:
  - id: signature
    type: u4
  - id: version
    type: u2
  - id: header_id
    type: u4
    doc: Random number of the program (Cannot be 0)
  - id: reserved
    type: u4
  - id: end_of_egg_header
    type: u4
    
