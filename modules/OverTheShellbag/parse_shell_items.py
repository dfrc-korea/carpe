import urllib.parse

from modules.OverTheShellbag import data_id
from modules.OverTheShellbag import data_format

from modules.OverTheShellbag import parse_sps_block
from modules.OverTheShellbag import parse_extension_block

from modules.OverTheShellbag import converter as cv
from modules.OverTheShellbag import debug_func as df

from modules.OverTheShellbag.errors import *


def RootFolder(_regData, _shell_item_result, _info):
  _shell_item_result["shell_type"] = "Root folder"
  (shell_item_size, shell_item_type, shell_item_data, pos) = _info

  extension_blocks = ""
  if shell_item_size in [0x14, 0x3A]:
    _shell_item_result["shell_type"] += ": GUID"
    (ITEM_DATA, pos) = cv.FormatParser(shell_item_data, data_format.ROOT_SHELL_ITEM_0014_FORMAT, pos)

    if ITEM_DATA["sort_index"] == b"\x00":
      raise ShellItemFormatError("New sort index (Root folder: GUID)")

    (guid, name) = cv.GUID2Text(ITEM_DATA["guid"])
    _shell_item_result["mapped_guid"] = (guid, name)
    _shell_item_result["value"] = name

    extension_blocks = ITEM_DATA["extension_block"]

  elif shell_item_size == 0x55:
    (ITEM_DATA, pos) = cv.FormatParser(shell_item_data, data_format.ROOT_SHELL_ITEM_0055_FORMAT, pos)

    if ITEM_DATA["sort_index"] != b"\x00":
      raise ShellItemFormatError("New sort index (Root folder: Drive)")

    if ITEM_DATA["upv_sig"] != b"\x10\xB7\xA6\xF5":
      raise ShellItemFormatError("New UPV signature of Root folder: Drive --> %s" %repr(ITEM_DATA["upv_sig"]))

    _shell_item_result = UsersPropertyView(_regData, _shell_item_result, _info)
    _shell_item_result["shell_type"] = "Root folder: Drive"

  else:  # UPV format
    (ITEM_DATA, pos) = cv.FormatParser(shell_item_data, data_format.USERS_SHELL_ITEM_FORMAT, pos)

    if ITEM_DATA["upv_sig"] != b"\xD5\xDF\xA3\x23":
      raise ShellItemFormatError("New UPV signature of Root folder: Variable --> %s" %repr(ITEM_DATA["upv_sig"]))

    _shell_item_result = UsersPropertyView(_regData, _shell_item_result, _info)
    _shell_item_result["shell_type"] += ": Search Folder"

  extension_block_result = parse_extension_block.Parse(extension_blocks, _regData)
  _shell_item_result["extension_block_result"] = extension_block_result

  return _shell_item_result


def Volume(_regData, _shell_item_result, _info):
  (shell_item_size, shell_item_type, shell_item_data, pos) = _info
  volume_type_flag = cv.Bytes2Int(shell_item_type) & 0x0F

  if volume_type_flag == 0x0E:      # Root Shell item (doesn't have name flags.) -> Shell folder
    volume_item_data = shell_item_data[1:]
    (guid, name)     = cv.GUID2Text(volume_item_data[0x00:0x10])
    extension_blocks = volume_item_data[0x10:]

    _shell_item_result["shell_type"] = "Root folder: GUID"
    _shell_item_result["mapped_guid"] = (guid, name)
    _shell_item_result["value"] = name

  elif volume_type_flag == 0x0F:
    offset = cv.FindEndOfStream(shell_item_data, 2, b"\x00\x00") - 2
    volume_letter = shell_item_data[:offset].decode()

    _shell_item_result["shell_type"]  = "Drive"
    _shell_item_result["value"] = volume_letter
    extension_blocks = ""

  else:
    raise ShellItemFormatError("New volume type flag (Volume Shell Item)")

  extension_block_result = parse_extension_block.Parse(extension_blocks, _regData)
  _shell_item_result["extension_block_result"] = extension_block_result

  return _shell_item_result


def FileEntry(_regData, _shell_item_result, _info):
  (shell_item_size, shell_item_type, shell_item_data, pos) = _info

  (ITEM_DATA, pos) = cv.FormatParser(shell_item_data, data_format.FILE_ENTRY_SHELL_ITEM_FORMAT, pos)

  _shell_item_result["file_size"] = cv.Bytes2Int(ITEM_DATA["file_size"])
  _shell_item_result["fat_mtime"] = cv.TSFat(ITEM_DATA["fat_mtime"])

  offset = cv.FindEndOfStream(ITEM_DATA["short_name"], 2, b"\x04\x00\xef\xbe") - 4
  _shell_item_result["short_name"] = cv.EncodingWizard(ITEM_DATA["short_name"][:offset]).replace("\x00", "")

  extension_blocks = ITEM_DATA["short_name"][offset:]

  if _shell_item_result["file_size"] == 0:
    _shell_item_result["shell_type"] = "Directory"
  elif _shell_item_result["file_size"] > 0:
    _shell_item_result["shell_type"] = "File"
  else:
    raise ShellItemFormatError("New file size (File Shell Item)")

  extension_block_result = parse_extension_block.Parse(extension_blocks, _regData)
  _shell_item_result["extension_block_result"] = extension_block_result

  for extension_block_dict in extension_block_result:
    if extension_block_dict["extension_sig"] == "0xbeef0004":
      _shell_item_result["value"] = extension_block_dict["long_name"]

  return _shell_item_result


def ControlPanel(_regData, _shell_item_result, _info):
  (shell_item_size, shell_item_type, shell_item_data, pos) = _info

  (ITEM_DATA, pos) = cv.FormatParser(shell_item_data, data_format.CONTROL_PANEL_SHELL_ITEM_FORMAT, pos)
  (guid, name) = cv.GUID2Text(ITEM_DATA["guid"])

  _shell_item_result["mapped_guid"] = (guid, name)
  _shell_item_result["value"] = name

  extension_blocks = ITEM_DATA["extension_block"]
  extension_block_result = parse_extension_block.Parse(extension_blocks, _regData)
  _shell_item_result["extension_block_result"] = extension_block_result

  return _shell_item_result


def ControlPanelCategory(_regData, _shell_item_result, _info):
  (shell_item_size, shell_item_type, shell_item_data, pos) = _info

  (ITEM_DATA, pos) = cv.FormatParser(shell_item_data, data_format.CONTROL_PANEL_CATEGORY_SHELL_ITEM_FORMAT, pos)

  if ITEM_DATA["sig"] != b"\x84\x21\xDE\x39":
    raise ShellItemFormatError("New signature (Control Panel Category)")

  category_id = cv.Bytes2Int(ITEM_DATA["category_id"])
  if category_id in data_id.CONTROL_PANEL_CATEGORY_ID.keys():
    _shell_item_result["value"] = data_id.CONTROL_PANEL_CATEGORY_ID[category_id]

  else:
    raise ShellItemFormatError("New category id (Control Panel Category)")

  extension_blocks = ITEM_DATA["extension_block"]
  extension_block_result = parse_extension_block.Parse(extension_blocks, _regData)
  _shell_item_result["extension_block_result"] = extension_block_result

  return _shell_item_result


def UsersPropertyView(_regData, _shell_item_result, _info):
  (shell_item_size, shell_item_type, shell_item_data, pos) = _info

  (ITEM_DATA, pos) = cv.FormatParser(shell_item_data, data_format.USERS_SHELL_ITEM_FORMAT, pos)
  _shell_item_result["shell_type"] = "Users property view"

  sps_blocks = ""
  extension_blocks = ""
  upv_size      = cv.Bytes2Int(ITEM_DATA["upv_size"])
  upv_data_size = cv.Bytes2Int(ITEM_DATA["upv_data_size"])
  upv_id_size   = cv.Bytes2Int(ITEM_DATA["upv_id_size"])

  if ITEM_DATA["upv_sig"] in [b"\x81\x19\x14\x10", b"\x00\xEE\xEB\xBE"]:
    upv_id_data = ITEM_DATA["upv_id_data"][:upv_id_size]  # unknown 32 bytes
    sps_blocks  = ITEM_DATA["upv_id_data"][upv_id_size:]

  elif ITEM_DATA["upv_sig"] == b"\xEE\xBB\xFE\x23":
    upv_id_data  = ITEM_DATA["upv_id_data"][:upv_id_size]
    (guid, name) = cv.GUID2Text(upv_id_data)

    _shell_item_result["mapped_guid"] = (guid, name)
    _shell_item_result["value"] = name

    if upv_data_size == 0:
      extension_blocks = ITEM_DATA["upv_id_data"][upv_id_size + 2:]

    elif upv_id_size > 0:
      sps_blocks = ITEM_DATA["upv_id_data"][upv_id_size:]

    else:
      raise ShellItemFormatError("New upv_id_size (Users property view Shell Item --> \\xEE\\xBB\\xFE\\x23)")

  elif ITEM_DATA["upv_sig"] == b"\xBB\xAF\x93\x3B":
    raise ShellItemFormatError("New upv_sig (Users property view Shell Item --> \\xBB\\xAF\\x93\\x3B)")

  elif ITEM_DATA["upv_sig"] == b"\x10\xB7\xA6\xF5":
    volume_shell_item_data = shell_item_data[pos-2:upv_size]
    two_guids = shell_item_data[upv_size + 3:]

    offset = cv.FindEndOfStream(volume_shell_item_data, 2, b"\x00\x00")
    volume_letter = volume_shell_item_data[:offset].decode()

    guid1 = cv.GUID2Text(two_guids[:16])
    guid2 = cv.GUID2Text(two_guids[16:32])
    extension_blocks = two_guids[32:]

    _shell_item_result["value"] = volume_letter
    _shell_item_result["mapped_guid"] = [guid1, guid2]

  elif ITEM_DATA["upv_sig"] == b"\xD5\xDF\xA3\x23":
    # size(upv_size, upv_sig, upv_data_size, upv_id_size) == 10
    sps_blocks = ITEM_DATA["upv_id_data"][upv_id_size:upv_size-10]
    root_item  = ITEM_DATA["upv_id_data"][upv_size-8:]  # 8 == 10 - len(\x00\x00)

    guid1 = cv.GUID2Text(root_item[:16])
    guid2 = cv.GUID2Text(root_item[16:32])
    extension_blocks = root_item[32:]

    (guid, name) = guid2
    _shell_item_result["value"] = name
    _shell_item_result["mapped_guid"] = [guid1, guid2]

  else:
    htu_size = cv.Bytes2Int(shell_item_data[5:9])
    htu_data = shell_item_data[1:htu_size - 3]

    if shell_item_data[1:5] == b"\x00\xB0\x01\xC0":
      _shell_item_result = HttpURIParser(htu_data, _shell_item_result)

    else:
      raise ShellItemFormatError("New HTTP URI(UTU) sig (Users Property View Shell Item) --> %s" %repr(ITEM_DATA["upv_sig"]))

  sps_result = parse_sps_block.Parse(sps_blocks, _debug=_regData)
  _shell_item_result["sps_result"] = sps_result

  if sps_result:
    RefineSPSResult(sps_result)

  extension_block_result = parse_extension_block.Parse(extension_blocks, _regData)
  _shell_item_result["extension_block_result"] = extension_block_result

  return _shell_item_result


def HttpURIParser(_htu_data, _parsing_result):
  _parsing_result["shell_type"] = "HTTP URI"

  loop = 0
  while True:
    if len(_htu_data) < 20:
      return _parsing_result

    (HTU_DATA, pos) = cv.FormatParser(_htu_data, data_format.HTU_SHELL_ITEM_FORMAT, 0)
    htu_url_size = cv.Bytes2Int(HTU_DATA["htu_url_size"])

    if loop == 0:
      _parsing_result["value"] = urllib.parse.unquote(_htu_data[pos:pos + htu_url_size].decode("UTF-16LE"))

    elif loop == 1:
      _parsing_result["full_url"] = _htu_data[pos:pos + htu_url_size].decode("UTF-16LE")

    else:
      if htu_url_size == 8 and HTU_DATA["htu_url"][-1] == 1:
        unknown_win64_time = cv.TSWin64bit(HTU_DATA["htu_url"])
        _parsing_result["unknown_data"] = ("Unknown Time", unknown_win64_time)

      else:
        raise ShellItemFormatError("New HTTP URI(HTU) format (Users Property View Shell Item)")

    _htu_data = _htu_data[pos + htu_url_size:]
    loop += 1


def RefineSPSResult(_sps_result):
  for spv_list in _sps_result:
    for spv in spv_list:
      if spv["value_id"] == 17:
        value = spv["value"]
        (dummy_guid, *other) = value.split(".")
        guid = dummy_guid[1:-1]

        # search dir path in network drive (%SystemRoot%\system32\Windows.Storage.Search.dll)
        if guid == "1685D4AB-A51B-4AF1-A4E5-CEE87002431D":
          network_drive_ip = '.'.join((other[-4:]))
          return network_drive_ip

        # search dir path in local (Windows Search Data Source)
        elif guid == "9E175B8B-F52A-11D8-B9A5-505054503030":
          return "local"

        else:
          raise WindowsPropertyFormatError("New value_id (Users Property View Shell Item) --> Search Results")
  return None