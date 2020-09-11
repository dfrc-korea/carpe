from modules.OverTheShellbag import data_type

# 지금은 모두 Win10 기준.
# TODO : Win XP, Vista, 8 포맷 추가

MRU_DATA_FORMAT = [
  {"name" : "shell_item_size", "offset" : 0x00, "size" : 0x02, "format" : "<H"},
  {"name" : "shell_item_type", "offset" : 0x02, "size" : 0x01, "format" : "<B"},
  {"name" : "shell_item_data", "offset" : 0x03, "size" : 0x00, "format" : "DATA"},
]

# Users Property View (UPV) --> Serialized Property Store (?)
USERS_SHELL_ITEM_FORMAT = [
  {"name" : "empty",         "offset" : 0x03, "size" : 0x01, "format" : "<B"},
  {"name" : "upv_size",      "offset" : 0x04, "size" : 0x02, "format" : "<H"},
  {"name" : "upv_sig",       "offset" : 0x06, "size" : 0x04, "format" : "SIGNATURE"},
  {"name" : "upv_data_size", "offset" : 0x0a, "size" : 0x02, "format" : "<H"},
  {"name" : "upv_id_size",   "offset" : 0x0c, "size" : 0x02, "format" : "<H"},
  {"name" : "upv_id_data",   "offset" : 0x0e, "size" : 0x00, "format" : "DATA"}
]

# Serialized Property Storage
SPS_FORMAT = [
  {"name" : "storage_size",    "offset" : 0x00, "size" : 0x04, "format" : "<I"},
  {"name" : "storage_version", "offset" : 0x04, "size" : 0x04, "format" : "<I"},
  {"name" : "storage_guid",    "offset" : 0x08, "size" : 0x10, "format" : "GUID"},
  {"name" : "value_list",      "offset" : 0x18, "size" : 0x00, "format" : "DATA"}
]

# Serialized Property Value (Property Value)
SPV_FORMAT = [
  {"name" : "value_size", "offset" : 0x00, "size" : 0x04, "format" : "<I"}, # or name_size (first property value)
  {"name" : "value_id",   "offset" : 0x04, "size" : 0x04, "format" : "<I"}, # or name
  {"name" : "reserved1",  "offset" : 0x08, "size" : 0x01, "format" : "<B"},
  {"name" : "value_type", "offset" : 0x09, "size" : 0x02, "format" : "<H"},
  {"name" : "reserved2",  "offset" : 0x0b, "size" : 0x02, "format" : "<H"},
  {"name" : "value_data", "offset" : 0x0d, "size" : 0x00, "format" : "DATA"}
]

# HTTP URI (HTU)
HTU_SHELL_ITEM_FORMAT = [
  {"name" : "htu_sig",      "offset" : 0x00, "size" : 0x04, "format" : "<I"},    # second, unknown
  {"name" : "htu_size",     "offset" : 0x04, "size" : 0x04, "format" : "<I"},    # second, unknown
  {"name" : "unknown1",     "offset" : 0x08, "size" : 0x04, "format" : "<I"},
  {"name" : "unknown2",     "offset" : 0x0c, "size" : 0x04, "format" : "<I"},
  {"name" : "htu_url_size", "offset" : 0x10, "size" : 0x04, "format" : "<I"},
  {"name" : "htu_url",      "offset" : 0x14, "size" : 0x00, "format" : "DATA"}
]

ROOT_SHELL_ITEM_0014_FORMAT = [
  {"name" : "sort_index",      "offset" : 0x03, "size" : 0x01, "format" : "<B"},
  {"name" : "guid",            "offset" : 0x04, "size" : 0x10, "format" : "GUID"},
  {"name" : "extension_block", "offset" : 0x14, "size" : 0x00, "format" : "DATA"}
]

ROOT_SHELL_ITEM_0055_FORMAT = [ # Contains UPV Format (looks like...).
  {"name" : "sort_index",    "offset" : 0x03, "size" : 0x01, "format" : "<B"},
  {"name" : "upv_size",      "offset" : 0x04, "size" : 0x02, "format" : "<H"},
  {"name" : "upv_sig",       "offset" : 0x06, "size" : 0x04, "format" : "SIGNATURE"},
  {"name" : "upv_data_size", "offset" : 0x0a, "size" : 0x02, "format" : "<H"},
  {"name" : "upv_data",      "offset" : 0x0c, "size" : 0x00, "format" : "DATA"}
  # 2 GUIDs
]

# TODO : Attribute flags list 추가
FILE_ENTRY_SHELL_ITEM_FORMAT = [
  {"name" : "empty",           "offset" : 0x03, "size" : 0x01, "format" : "<B"},
  {"name" : "file_size",       "offset" : 0x04, "size" : 0x04, "format" : "<I"},
  {"name" : "fat_mtime",       "offset" : 0x08, "size" : 0x04, "format" : "I"},
  {"name" : "attribute_flags", "offset" : 0x0C, "size" : 0x02, "format" : ""},
  {"name" : "short_name",      "offset" : 0x0E, "size" : 0x00, "format" : "DATA"}
  # extension_block
]

CONTROL_PANEL_SHELL_ITEM_FORMAT = [
  {"name" : "sort_index",      "offset" : 0x03, "size" : 0x01, "format" : "<B"},
  {"name" : "Unknown",         "offset" : 0x04, "size" : 0x0a, "format" : "structure"},
  {"name" : "guid",            "offset" : 0x0e, "size" : 0x10, "format" : "GUID"},
  {"name" : "extension_block", "offset" : 0x1e, "size" : 0x00, "format" : "DATA"}
]

CONTROL_PANEL_CATEGORY_SHELL_ITEM_FORMAT = [
  {"name" : "empty",           "offset" : 0x03, "size" : 0x01, "format" : "<B"},
  {"name" : "sig",             "offset" : 0x04, "size" : 0x04, "format" : "<I"},
  {"name" : "category_id",     "offset" : 0x08, "size" : 0x04, "format" : "<I"},
  {"name" : "extension_block", "offset" : 0x0c, "size" : 0x00, "format" : "DATA"}
]

EXTENSION_BLOCK_SIGNATURE_FORMAT = [
  {"name" : "extension_size",    "offset" : 0x00, "size" : 0x02, "format" : "<H"},
  {"name" : "extension_version", "offset" : 0x02, "size" : 0x02, "format" : "<H"},
  {"name" : "extension_sig",     "offset" : 0x04, "size" : 0x04, "format" : "SIGNATURE"},
  {"name" : "extension_data",    "offset" : 0x08, "size" : 0x00, "format" : "DATA"},
]

# FILE_EXTENSION_BLOCK signature is 0xbeef0004
FILE_EXTENSION_BLOCK_COMMON_FORMAT = [
  {"name" : "fat_ctime",         "offset" : 0x08, "size" : 0x04, "format" : ""},
  {"name" : "fat_atime",         "offset" : 0x0C, "size" : 0x04, "format" : ""},
  {"name" : "extension_id",      "offset" : 0x10, "size" : 0x02, "format" : "<H"},
  {"name" : "data",              "offset" : 0x12, "size" : 0x00, "format" : ""}
]

FILE_EXTENSION_BLOCK_WIN81_FORMAT = [
  # Including Win10
  {"name" : "empty1",             "offset" : 0x00, "size" : 0x02, "format" : "<H"},
  {"name" : "mft_reference",      "offset" : 0x02, "size" : 0x08, "format" : "<Q"},
  {"name" : "empty2",             "offset" : 0x0a, "size" : 0x08, "format" : "<Q"},
  {"name" : "name_size",          "offset" : 0x12, "size" : 0x02, "format" : "<H"},
  {"name" : "empty3",             "offset" : 0x14, "size" : 0x04, "format" : "<I"},
  {"name" : "unknown",            "offset" : 0x18, "size" : 0x04, "format" : "<I"},
  {"name" : "long_name",          "offset" : 0x1c, "size" : 0x00, "format" : ""}
  # localized name
  # first extension block offset
]

EXTENSION_BLOCK_0000_FORMAT = [
  # same 0019
  {"name" : "folder_type_id1", "offset" : 0x08, "size" : 0x10, "format" : "GUID"},
  {"name" : "folder_type_id2", "offset" : 0x18, "size" : 0x10, "format" : "GUID"}
]

EXTENSION_BLOCK_0003_FORMAT = [
  {"name" : "guid", "offset" : 0x08, "size" : 0x10, "format" : "GUID"}
]

EXTENSION_BLOCK_0026_FORMAT = [
  {"name": "unknown",     "offset": 0x08, "size": 0x04, "format": "<I"},
  {"name": "win64_ctime", "offset": 0x0c, "size": 0x08, "format": "<Q"},
  {"name": "win64_mtime", "offset": 0x14, "size": 0x08, "format": "<Q"},
  {"name": "win64_atime", "offset": 0x1c, "size": 0x08, "format": "<Q"}
]

EXTENSION_BLOCK_0027_FORMAT = [
  # Contain SPS FORMAT.
]

# VT_STREAM contains it.
LAST_IDK_BLOCK = [
  {"name" : "unknown1",      "offset" : 0x00, "size" : 0x24, "format" : "DATA"},
  {"name" : "item_field",    "offset" : 0x24, "size" : 0x30, "format" : "DATA"},
  {"name" : "guid",          "offset" : 0x54, "size" : 0x10, "format" : "GUID"},
  {"name" : "pad_ff",        "offset" : 0x64, "size" : 0x0c, "format" : "DATA"},
  {"name" : "unknown2",      "offset" : 0x70, "size" : 0x0a, "format" : "DATA"},
  {"name" : "search_result", "offset" : 0x7a, "size" : 0x00, "format" : "DATA"}
]

SHELL_ITEM_TYPES = data_type.TypeList.SHELL_ITEM_TYPES