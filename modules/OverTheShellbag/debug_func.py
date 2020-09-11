import string
import pprint
import collections

def GetUniqueList(_list):
  return sorted(list(set(_list)))


def PrintFrequency(_list):
  counter_result = collections.Counter(_list)
  sorted_result  = GetUniqueList(_list)

  PrintBeauty(sorted_result)
  PrintBeauty(counter_result)


def PrintBeauty(_data, _opt=False, _sept_count=77):
  if _opt:

    key_list = []
    for key in _data.keys():
      key_list.append(len(key))

    max_size = max(key_list) + 1

    line = "{\n"
    for key in _data.keys():
      padding_size = max_size - len(key)
      line += "  '%s'%s: %s,\n" %(key, " "*padding_size, _data[key] )

    line = line.strip()[:-1]
    line += "\n}"

  else:
    pprint.pprint(_data, indent=2)
    print("=" * _sept_count)


def PrintHexString(_bytes, _out=True, _alignment=16):
  if _bytes == None:
    print("[!] PrintHexString : No data -> None")
    return None

  alignment = _alignment

  hex_list   = []
  ascii_list = []
  for idx, _byte in enumerate(_bytes):
    tmp_hex_str = hex(_byte)[2:]
    hex_str = "0" * (len(tmp_hex_str) % 2) + tmp_hex_str

    hex_list.append(hex_str)
    ascii_list.append(GetPrintableASCII(_byte))

  idx = 0
  result = ""
  while idx < len(hex_list):
    print_hex   = ' '.join(hex_list[idx:idx+alignment])
    print_ascii = ''.join(ascii_list[idx:idx+alignment])

    if (len(hex_list[idx:idx+alignment]) % alignment) != 0:
      padd_count = alignment - (len(hex_list[idx:idx+alignment]) % alignment)
      print_hex += "   " * padd_count
      print_ascii += " " * padd_count

    line = "|" + hex(idx)[2:].zfill(4).upper() + "| " + print_hex + " |" + print_ascii + "|" + "\n"
    result += line
    idx += alignment

  if _out:
    print(result)
    return None
  return result.strip()

def PrintTypesList(_type_data):
  for type_data in _type_data:
    name = type_data["type"]

    result = "["
    for sig in type_data["sig"]:
      hex_str = "0x" + sig.hex() + ", "
      result += hex_str
    result = result[:-2]
    result += "]"
    print("%-30s\t: %s" %(name, result))


def GetPrintableASCII(_byte):
  ascii = chr(_byte)

  if not ascii in string.printable[:-5]:
    return "."
  return ascii