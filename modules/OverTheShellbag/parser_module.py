import urllib.parse

from modules.OverTheShellbag import data_format
from modules.OverTheShellbag import parse_shell_items
from modules.OverTheShellbag import parse_sps_block
from modules.OverTheShellbag import parse_extension_block

from modules.OverTheShellbag import converter as cv
from modules.OverTheShellbag import debug_func as df

from modules.OverTheShellbag.errors import *


def MRUDataParser(_regData):
  shell_item_result = {
    "last_written_time" : None,
    "shell_type"  : None,
    "file_size"   : 0,
    "fat_mtime"   : None,
    "short_name"  : None,
    "full_url" : None,
    "value"    : None,
    "mapped_guid"  : None,
    "unknown_data" : None,
    "extension_block_result" : [],
    "sps_result" : [],          # sps_result can have shell_item_result. so, it can have extension_block_result also.
    # "registry_data"  : _regData
  }

  (MRU_DATA, shell_item_pos) = cv.FormatParser(_regData, data_format.MRU_DATA_FORMAT, 0)

  shell_item_size = cv.Bytes2Int(MRU_DATA["shell_item_size"])
  shell_item_type = cv.ReturnType(MRU_DATA["shell_item_type"], data_format.SHELL_ITEM_TYPES)
  shell_item_data = MRU_DATA["shell_item_data"]

  shell_item_info = (shell_item_size, MRU_DATA["shell_item_type"], shell_item_data, shell_item_pos)
  if shell_item_type == "root_folder_shell_item":         # Shell folder (GUID)
    shell_item_result = parse_shell_items.RootFolder(_regData, shell_item_result, shell_item_info)

  elif shell_item_type == "volume_shell_item":      # My Computer in Explorer
    shell_item_result = parse_shell_items.Volume(_regData, shell_item_result, shell_item_info)

  elif shell_item_type == "file_entry_shell_item":
    shell_item_result = parse_shell_items.FileEntry(_regData, shell_item_result, shell_item_info)

  # elif shell_item_type == "network_location_shell_item":
  #   # Never seen.

  elif shell_item_type == "control_panel_shell_item":
    shell_item_result = parse_shell_items.ControlPanel(_regData, shell_item_result, shell_item_info)

  elif shell_item_type == "control_panel_category_shell_item":
    shell_item_result = parse_shell_items.ControlPanelCategory(_regData, shell_item_result, shell_item_info)

  elif shell_item_type == "users_property_view_shell_item":
    shell_item_result = parse_shell_items.UsersPropertyView(_regData, shell_item_result, shell_item_info)

  else:
    # df.PrintHexString(MRU_DATA["shell_item_type"])
    return None
    pass

  if shell_item_result["value"] == None:
    shell_item_result["value"] == "Comming Soon"
    pass

  # df.PrintBeauty(shell_item_result, _sept_count=67)

  return shell_item_result


def MRUListExParser(_regData):
  loop = 0
  result = []

  while loop < len(_regData):
    mru_index_bytes = _regData[loop:loop+0x04]

    if mru_index_bytes == b"\xFF\xFF\xFF\xFF":
      break

    mru_index = cv.Bytes2Int(mru_index_bytes)
    result.append(mru_index)

    loop += 4
  return result
