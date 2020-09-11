meta:
  id: prefetch_directory_string_entry
  title: Microsoft Windows Prefetch (PF) File Format - Directory String Entry Structure
  endian: le
  # 'https://github.com/libyal/libscca/blob/master/documentation/'
  
seq:
  - id: number_characters
    type: u2
  - id: directory_string
    size: (number_characters + 1) * 2
    type: str
    encoding: UTF-16LE
