from modules.OverTheShellbag import data_format
from modules.OverTheShellbag import converter as cv
from modules.OverTheShellbag import parse_sps_block

from modules.OverTheShellbag import debug_func as df

from modules.OverTheShellbag.errors import *


def Parse(_extension_blocks, _debug=None):
  global regData
  regData = _debug

  if len(_extension_blocks) == 0 or _extension_blocks == b"\x00\x00":
    extension_block_result = None
  else:
    extension_block_result = []
    extension_block_list = SplitExtensionBlocks(_extension_blocks)

    for extension_block in extension_block_list:
      parsed_extension_block = ExtensionBlockParser(extension_block)
      extension_block_result.append(parsed_extension_block)
  return extension_block_result


def SplitExtensionBlocks(_extension_blocks):
  extension_block_list = []
  extension_blocks = _extension_blocks

  while True:
    (EXTENSION_BLOCK_SIG, pos) = cv.FormatParser(extension_blocks, data_format.EXTENSION_BLOCK_SIGNATURE_FORMAT, 0)
    block_size       = cv.Bytes2Int(EXTENSION_BLOCK_SIG["extension_size"])
    extension_block  = extension_blocks[:block_size]
    extension_blocks = extension_blocks[block_size:]
    extension_block_list.append(extension_block)

    if extension_blocks[:2] == b"\x00\x00" or extension_blocks == b"":
      return extension_block_list


def ExtensionBlockParser(_extension_block):
  extension_block_result = {
    "extension_sig" : None,
    "mapped_guid"   : None,   # [(guid, name), (guid, name), ...]
    "filesystem"    : None,
    "mft_entry_number": None,
    "mft_sequence_number" : None,
    "ctime" : None,
    "mtime" : None,
    "atime" : None,
    "long_name" : None,
    "localized_name" : None,
    "comment" : None,
    "sps_result" : []
  }

  (EXTENSION_BLOCK_SIGNATURE, pos) = cv.FormatParser(_extension_block, data_format.EXTENSION_BLOCK_SIGNATURE_FORMAT, 0)
  extension_size    = cv.Bytes2Int(EXTENSION_BLOCK_SIGNATURE["extension_size"])
  extension_version = cv.Bytes2Int(EXTENSION_BLOCK_SIGNATURE["extension_version"])
  extension_sig     = EXTENSION_BLOCK_SIGNATURE["extension_sig"]
  extension_block_result["extension_sig"] = "0x" + hex(cv.Bytes2Int(extension_sig))[2:].zfill(8)

  if extension_sig in [b"\x00\x00\xef\xbe", b"\x19\x00\xef\xbe"]:
    (EXTENSION_BLOCK_0000, pos) = cv.FormatParser(_extension_block, data_format.EXTENSION_BLOCK_0000_FORMAT, 0)

    if extension_size == 14: # Unknown Data
      pass

    elif extension_size == 42:
      mapped_guid1 = cv.GUID2Text(EXTENSION_BLOCK_0000["folder_type_id1"])
      mapped_guid2 = cv.GUID2Text(EXTENSION_BLOCK_0000["folder_type_id2"])

      extension_block_result["mapped_guid"] = [mapped_guid1, mapped_guid2]

    else:
      raise ExtensionBlockFormatError("New BEEF0000, BEEF0019 block size.")

  elif extension_sig == b"\x03\x00\xef\xbe":
    (EXTENSION_BLOCK_0003, pos) = cv.FormatParser(_extension_block, data_format.EXTENSION_BLOCK_0003_FORMAT, 0)

    extension_block_result["mapped_guid"] = cv.GUID2Text(EXTENSION_BLOCK_0003["guid"])

  elif extension_sig == b"\x04\x00\xef\xbe":
    extension_block_result = FileExtensionBlockParser(_extension_block, extension_version, extension_block_result)

  elif extension_sig == b"\x13\x00\xef\xbe":
    extension_block_result["comment"] = "Unknown extension block."

  elif extension_sig == b"\x26\x00\xef\xbe":
    (EXTENSION_BLOCK_0026, pos) = cv.FormatParser(_extension_block, data_format.EXTENSION_BLOCK_0026_FORMAT, 0)

    extension_block_result["ctime"] = cv.TSWin64bit(EXTENSION_BLOCK_0026["win64_ctime"])
    extension_block_result["mtime"] = cv.TSWin64bit(EXTENSION_BLOCK_0026["win64_mtime"])
    extension_block_result["atime"] = cv.TSWin64bit(EXTENSION_BLOCK_0026["win64_atime"])

  elif extension_sig == b"\x27\x00\xef\xbe":
    (EXTENSION_BLOCK, pos) = cv.FormatParser(_extension_block, data_format.EXTENSION_BLOCK_SIGNATURE_FORMAT, 0)
    extension_data = EXTENSION_BLOCK["extension_data"]

    # TODO : SPS 파싱 끝나면, 여기에 반영하기.
    parse_sps_block.Parse(extension_data)

  else:
    sig = repr(extension_sig)[1:].replace("'", "")
    raise ExtensionBlockFormatError("New extension block (%s)" %sig)

  return extension_block_result


def FileExtensionBlockParser(_extension_block, _extension_version, _extension_block_result):
  # TODO : WinXP ~ Win 8 추가 필요.
  (FILE_EXTENSION_BLOCK_COMMON, pos) = cv.FormatParser(_extension_block,
                                                    data_format.FILE_EXTENSION_BLOCK_COMMON_FORMAT, 0)
  _extension_block_result["ctime"] = cv.TSFat(FILE_EXTENSION_BLOCK_COMMON["fat_ctime"])
  _extension_block_result["atime"] = cv.TSFat(FILE_EXTENSION_BLOCK_COMMON["fat_atime"])

  if _extension_version == 9:       # Win8.1 ~ Win10
    (FILE_EXTENSION_BLOCK_DATA, pos) = cv.FormatParser(FILE_EXTENSION_BLOCK_COMMON["data"],
                                                    data_format.FILE_EXTENSION_BLOCK_WIN81_FORMAT, 0)
    mft_reference   = FILE_EXTENSION_BLOCK_DATA["mft_reference"]
    name_size       = cv.Bytes2Int(FILE_EXTENSION_BLOCK_DATA["name_size"])
    dummy_name      = FILE_EXTENSION_BLOCK_DATA["long_name"]
    _extension_block_result["mft_entry_number"] = cv.Bytes2Int(mft_reference[0:4])
    _extension_block_result["mft_sequence_number"] = cv.Bytes2Int(mft_reference[4:6])

    if name_size == 0:
      long_name = dummy_name[:-4].decode("UTF-16LE")
      _extension_block_result["long_name"] = long_name

    elif name_size > 0:
      offset = cv.FindEndOfStream(dummy_name, 2, b"\x00\x00")
      long_name  = dummy_name[:offset].decode("UTF-16LE")
      local_name = dummy_name[offset+2:-4].decode("UTF-16LE")

      _extension_block_result["long_name"]      = long_name
      _extension_block_result["localized_name"] = local_name

    return _extension_block_result