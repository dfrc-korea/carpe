from yarp import Registry


def GetRegistryDataPath(_path):
  # path = "./hive/UsrClass.dat"
  hive = Registry.RegistryHive(open(_path, "rb"))

  return start(hive)


def GetRegistryDataFileObject(_file_object_dict):
  primary = _file_object_dict["primary"]
  log1 = _file_object_dict["log1"]
  log2 = _file_object_dict["log2"]

  hive = Registry.RegistryHive(primary)
  if (not log1 is None and not log2 is None) == True:
    try:
      hive.recover_new(log1, log2)
    except:
      pass

  return start(hive)


def start(_hive,):
  result = {}
  KEY_LWT = {}

  SID = _hive.root_key().name().split("_")[0]

  bag_key = _hive.find_key("\Local Settings\Software\Microsoft\Windows\Shell\BagMRU")

  if bag_key is None:
    return result, KEY_LWT

  key_lwt = {}
  (result[SID], key_lwt) = GetRegDataRecursive(bag_key, "/", key_lwt)
  KEY_LWT[SID] = key_lwt

  return result, KEY_LWT


def GetRegDataRecursive(_key, _key_path, _key_lwt):
  reg_values = GetRegValues(_key)
  sub_keys   = []

  reg_key = {
    "key_name" : _key.name(),
    "key_path" : _key_path,
    "last_written_time" : _key.last_written_timestamp(),
    "reg_values" : reg_values,
    "sub_keys" : []
  }

  _key_lwt[_key_path] = _key.last_written_timestamp()

  for next_key in _key.subkeys():
    next_key_name = next_key.name()
    (sub_key, x) = GetFuellKeyPath(next_key, _key_path, next_key_name, _key_lwt)
    sub_keys.append(sub_key)
  reg_key["sub_keys"] = sub_keys

  return reg_key, _key_lwt


def GetFuellKeyPath(_key, _key_path, _next_key_name, _key_lwt):
  _key_path += _next_key_name + "/"

  return GetRegDataRecursive(_key, _key_path, _key_lwt)


def GetRegValues(_key):
  reg_value_list = []

  for reg_value in _key.values():
    # reg_value.type_str() # value data type
    reg_value_dic = {
      "value_name" : reg_value.name(),
      "value_data" : reg_value.data()
    }
    reg_value_list.append(reg_value_dic)
  return reg_value_list