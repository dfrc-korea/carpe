import sys
import datetime

from modules.OverTheShellbag import errors
from modules.OverTheShellbag import parser_module as pm
from modules.OverTheShellbag import debug_func as df

# TODO : Filesystem(NTFS, exFAT, FAT 구분)
# TODO : HTTP URI BOM 지우기
# TODO : Minor Shell item Parser 추가(Control Panel, UsersFiles etc)
# TODO : Full Path 그려주기
# TODO : Dictionary 리턴 값 가공


DETECTED_EXCEPTIONS = {
    # ERROR_TYPE_A : { key, value }
    # ERROR_TYPE_B : { key, value }
}


def TreatExceptions(_error, _error_data):
    if type(_error) is tuple:
        (error_type, error_message) = _error

    else:
        error_type = _error.error_type
        error_message = _error.error_message

    if not error_type in DETECTED_EXCEPTIONS.keys():
        DETECTED_EXCEPTIONS[error_type] = []

    error_info = {
        "error_message": error_message,
        "error_data": _error_data
    }
    DETECTED_EXCEPTIONS[error_type].append(error_info)


def SaveExceptions(_save_folder_path):
    import os, zlib, pickle, datetime

    if not os.path.exists(_save_folder_path):
        os.mkdir(_save_folder_path)

    (tmp_ymd, tmp_hms) = str(datetime.datetime.now()).split(" ")
    ymd = tmp_ymd.replace("-", "")
    hms = tmp_hms.split(".")[0].replace(":", "")

    data = pickle.dumps(DETECTED_EXCEPTIONS)
    comp = zlib.compress(data)
    crc32 = hex(zlib.crc32(comp) & 0xFFFFFFFF)[2:].zfill(8)

    full_path = _save_folder_path + "/" + ymd + hms + "_" + crc32 + ".pic"
    open(full_path, "wb").write(comp)


def RefineResultToList(_parsing_result, _Bagkey):
    shell_item_result_key = ["shell_type", "value", "fat_mtime", "file_size"]
    extension_block_result_key = ["extension_sig", "mtime", "atime", "ctime", "filesystem", "mft_entry_number",
                                  "mft_sequence_number"]

    refined_shell = []
    for key in shell_item_result_key:
        if not _parsing_result[key] is None:
            if type(_parsing_result[key]) is int:
                refined_shell.append((_parsing_result[key]))
            else:
                refined_shell.append(str(_parsing_result[key]))

        else:
            if key == "file_size":
                refined_shell.append(0)
            else:
                refined_shell.append("")

    refined_extension_block = []
    extension_block_result_list = _parsing_result["extension_block_result"]
    if extension_block_result_list:
        for extension_block_result in extension_block_result_list:
            if extension_block_result["extension_sig"] in ["0xbeef0026", "0xbeef0004"]:
                for key in extension_block_result_key:
                    dict_value = extension_block_result[key]
                    if dict_value:
                        refined_extension_block.append(extension_block_result[key])
                    else:
                        refined_extension_block.append("")
            else:
                refined_extension_block = [""] * len(extension_block_result_key)
    else:
        refined_extension_block = [""] * len(extension_block_result_key)

    (shell_type, value, fat_mtime, file_size) = refined_shell
    (extension_sig, mtime, atime, ctime, filesystem, mft_entry_number, mft_sequence_number) = refined_extension_block

    if mtime == "":
        mtime = fat_mtime
    bag_path = "BagMRU" + _Bagkey
    last_written_time = _parsing_result["last_written_time"]
    last_written_time = last_written_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    if mtime:
        mtime = str(mtime).replace(' ', 'T') + 'Z'
    if atime:
        atime = str(atime).replace(' ', 'T') + 'Z'
    if ctime:
        ctime = str(ctime).replace(' ', 'T') + 'Z'
    return [bag_path, shell_type, value, str(mtime), str(atime), str(ctime), str(
        last_written_time), file_size, mft_entry_number, mft_sequence_number, filesystem]


def GetLastTime(_target_key, _key_lwt_dic):
    for key_path in _key_lwt_dic.keys():
        if _target_key == key_path:
            return _key_lwt_dic[key_path]
    return None


def GetSubKeys(_reg_data, _value_data_result, _key_lwt_dic):
    key_path = _reg_data["key_path"]
    reg_values = _reg_data["reg_values"]
    sub_keys = _reg_data["sub_keys"]

    for reg_value in reg_values:
        value_name = reg_value["value_name"]

        if not value_name in ["MRUListEx", "NodeSlot", "NodeSlots"]:
            value_data = reg_value["value_data"]
            key_value_path = key_path + value_name

            _value_data_result[key_value_path] = value_data

    if sub_keys:
        for sub_key in sub_keys:
            GetSubKeys(sub_key, _value_data_result, _key_lwt_dic)

    return _value_data_result


def Main(file_objects):
    isHive = True  # True is Hive, False is Live
    key_lwt = {}
    if isHive:
        from modules.OverTheShellbag import get_offline

        """file_object_dict = {
      # Input Hive Path or file_object.
      "primary": None,
      "log1": None,
      "log2": None
    }"""

        # file_object_dict["primary"] = open("./bug_report/20200513_infinite_loop_case/admin_hjung18/UsrClass.dat", "rb")
        # file_object_dict["log1"] = open("./bug_report/20200513_infinite_loop_case/admin_hjung18/UsrClass.dat.LOG1", "rb")
        # file_object_dict["log2"] = open("./bug_report/20200513_infinite_loop_case/admin_hjung18/UsrClass.dat.LOG2", "rb")

        (reg_data, key_lwt) = get_offline.GetRegistryDataFileObject(file_objects)
        # (reg_data, key_lwt) = get_offline.GetRegistryDataFileObject(file_object_dict)

    else:
        pass
        # from modules.OverTheShellbag import get_live

        # (reg_data, key_lwt) = get_live.Get()
    shellbags = []
    VALUE_DATA = {}
    for SID in reg_data.keys():
        value_data_result = {"/": "Root (BagMRU)"}
        value_data_result = GetSubKeys(reg_data[SID], value_data_result, key_lwt[SID])

        for idx, key in enumerate(value_data_result.keys()):
            value_data = value_data_result[key]
            if value_data == "Root (BagMRU)":
                value_data = b""

            last_written_time = GetLastTime(key + "/", key_lwt[SID])

            result = None
            try:
                result = pm.MRUDataParser(value_data)

            except errors.ShellItemFormatError as e:
                TreatExceptions(e, value_data)

            except errors.ExtensionBlockFormatError as e:
                TreatExceptions(e, value_data)

            except errors.WindowsPropertyFormatError as e:
                TreatExceptions(e, value_data)

            except:
                TreatExceptions(("Fatal error (Unexpected)", sys.exc_info()[0]), value_data)

            if result:
                result["last_written_time"] = last_written_time
                result_list = RefineResultToList(result, key)

                shellbags.append(result_list)

    return shellbags
    # print(result_tuple)

# Print Exceptions (Report This Error to developer)
# df.PrintBeauty(DETECTED_EXCEPTIONS)
# save_folder_path = "./Exceptions"
# SaveExceptions(save_folder_path)
