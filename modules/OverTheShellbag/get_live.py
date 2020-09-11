import os
import winreg

from modules.OverTheShellbag import converter as cv


def Get():
  regKey = winreg.OpenKeyEx(winreg.HKEY_USERS, r"")
  loop = 0

  VALUE_DATA = {}
  while True:
    try:
      key_name = winreg.EnumKey(regKey, loop)
      if key_name.find("_Classes") != -1:
        SID = key_name.split("_")[0]
        VALUE_DATA[SID] = {}

    except Exception as e:
      break
    loop += 1

  KEY_LWT = {}
  for SID in VALUE_DATA.keys():
    key_path = SID + r"_Classes" +  r"\Local Settings\Software\Microsoft\Windows\Shell\BagMRU"
    key_lwt = {}
    (reg_data, key_lwt) = GetRegDataRecursive(winreg.HKEY_USERS, key_path, "/", key_lwt)

    VALUE_DATA[SID] = reg_data
    KEY_LWT[SID] = key_lwt
  return VALUE_DATA, KEY_LWT


def GetRegDataRecursive(_hive_type, _hKey, _key_path, _key_lwt):
  regKey = winreg.OpenKeyEx(_hive_type, _hKey)
  key_name = os.path.basename(_hKey)
  last_written_time = GetLastWrittenTime(regKey)
  reg_values = GetRegValues(regKey)

  reg_key = {
    "key_name": key_name,
    "key_path": _key_path,
    "last_written_time": last_written_time,
    "reg_values": reg_values,
    "sub_keys": []
  }

  _key_lwt[_key_path] = last_written_time

  sub_keys = []
  loop = 0
  while True:
    try:
      next_key_name = winreg.EnumKey(regKey, loop)
      next_hKey = _hKey + "\\" + next_key_name

      (sub_key, x) = GetFullKeyPath(_hive_type, next_hKey, _key_path, next_key_name, _key_lwt)
      sub_keys.append(sub_key)

    except Exception as e:
      break
    loop += 1

  reg_key["sub_keys"] = sub_keys

  return reg_key, _key_lwt


def GetFullKeyPath(_hive_type, _hKey, _key_path, _next_key_name, _key_lwt):
  _key_path += _next_key_name + "/"
  return GetRegDataRecursive(_hive_type, _hKey, _key_path, _key_lwt)


def GetRegValues(_regKey):
  reg_value_list = []

  loop = 0
  while True:
    try:
      (regValue, regData, regType) = winreg.EnumValue(_regKey, loop)
      reg_value = {
        "value_name": regValue,
        "value_data": regData
      }
      reg_value_list.append(reg_value)

    except Exception as e:
      break
    loop += 1
  return reg_value_list


def GetLastWrittenTime(_regKey):
  q_result = winreg.QueryInfoKey(_regKey)

  return cv.TSWin64bit(q_result[2])