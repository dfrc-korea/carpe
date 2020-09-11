meta:
  id: egg_file_name_header
  title: EST soft EGG File Format - EGG's File Name Header
  endian: le
  # https://web.archive.org/web/20130402232948/http://sdn.altools.co.kr/etc/EGG_Specification.zip
  
seq:
  - id: signature
    type: u4
  - id: bit_flag
    type: u1
    doc: bit3(Unset -> No encryption, Set -> Encrypt), bit4(Unset -> Use UTF-8, Set -> User area code), bit5(Unset -> Absolute Path, Set -> Relative Path)
  - id: size
    type: u2
  - id: locale
    size: 2
    if: bit_flag & 0x04 == 1
  - id: parent_path_id
    type: u4
    if: bit_flag & 0x08 == 1
  - id: name
    size: size