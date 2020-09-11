from modules.OverTheShellbag import converter as cv

class TypeList:
  # key "sig" will convert list type -> ConverTypeForPython()

  # List : ['00', '10', '1f', '20', '2e', '2f', '31', '32', '35', '71', '74', '78', 'b1']
  #         '31': 1801, '35': 420,  '1f': 39,  '00': 13,
  #         '2f': 8,    '2e': 7,    '74': 6,   '71': 4,
  #         'b1': 4,    '78': 3,    '10': 3,   '32': 2, '20': 1

  SHELL_ITEM_TYPES = [
    {"type" : "users_property_view_shell_item",    "sig" : b"\x00"},
    {"type" : "root_folder_shell_item",            "sig" : b"\x1F"},
    {"type" : "volume_shell_item",                 "sig" : (0x20, 0x2F)},
    {"type" : "file_entry_shell_item",             "sig" : [(0x30, 0x3F), b"\xB1"]},
    {"type" : "network_location_shell_item",       "sig" : (0x40, 0x4F)},
    {"type" : "control_panel_shell_item",          "sig" : b"\x71"},
    {"type" : "control_panel_category_shell_item", "sig" : b"\x01"},
  ]

  FILE_EXTENSION_BLOCK_TYPES = [
    {"type" : "WinXP",    "sig" : b"\x03"},
    {"type" : "WinVista", "sig" : b"\x07"},
    {"type" : "Win7",     "sig" : b"\x08"},
    {"type" : "Win81",    "sig" : b"\x09"}
  ]


def GetListOnly():
  class_resource = TypeList.__dict__
  type_list = []

  for key in class_resource:
    if key.find("TYPES") != -1:
      type_list.append(class_resource[key])

  return type_list

def TupleInterpreter(_type_data_sig_tuple):
  (start, end) = _type_data_sig_tuple

  sig_list = []
  for sig_data in range(start, end + 1):
    hexString_sig = cv.AddPaddingHex(hex(sig_data))
    bytes_sig = bytes.fromhex(hexString_sig)
    sig_list.append(bytes_sig)

  return sig_list

def ConvertTypeForPython():
  type_list = GetListOnly()

  for _type_data in type_list:
    for type_data in _type_data:
      if type(type_data["sig"]) is bytes:
        type_data["sig"] = [type_data["sig"]]

      elif type(type_data["sig"]) is list:
        type_data_sig_tuple = type_data["sig"][0]
        added_sig_list = type_data["sig"][1:]

        sig_list = TupleInterpreter(type_data_sig_tuple)
        for added_sig in added_sig_list:
          sig_list.append(added_sig)
        type_data["sig"] = sig_list

      else:
        type_data["sig"] = TupleInterpreter(type_data["sig"])
ConvertTypeForPython()