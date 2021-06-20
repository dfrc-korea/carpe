from datetime import datetime, timedelta
import binascii
import modules.Registry.guid as gu
import modules.Registry.convert_util as cu
import re
import os
from modules import logger

class MRU_Folder_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    program_name = ''
    accessed_folder = ''
    modified_time = ''
    registry_order = ''
    value = ''
    useraccount = ''
    backup_flag = ''
    source_location = []

class MRU_Parser:
    def __init__(self):
        self.drive_letter = None
        self.guid_folder = None
        self.file_path = None

    def Assemble(self):
        file_path = ''
        if self.drive_letter is not None:
            drive_letter = (self.drive_letter).decode('utf-8')
            file_path += drive_letter + ":"
            if len(self.extension_dict) !=0:
                for extension_dict_key in self.extension_dict:
                    number_of_extension_block = len(extension_dict_key)
                    file_name = self.extension_dict.get(extension_dict_key).get('name_encoded')
                    file_path += os.sep + file_name
            self.file_path = file_path
            return self.file_path

        elif self.drive_letter is None and self.guid_folder is not None:
            file_path += self.guid_folder
            if len(self.extension_dict) !=0:
                for extension_dict_key in self.extension_dict:
                    number_of_extension_block = len(extension_dict_key)
                    file_name = self.extension_dict.get(extension_dict_key).get('name_encoded')
                    file_path += os.sep + file_name
            self.file_path = file_path
            return self.file_path
        elif self.drive_letter is None and self.guid_folder is None:
            if len(self.extension_dict) !=0:
                for extension_dict_key in self.extension_dict:
                    number_of_extension_block = len(extension_dict_key)
                    file_name = self.extension_dict.get(extension_dict_key).get('name_encoded')
                    if len(self.extension_dict) ==1:
                        file_path += file_name
                    else:
                        file_path += os.sep + file_name
            self.file_path = file_path
            return self.file_path

    def ParseExtensionBlock(self, hex_data):
        p = re.compile('@shell32.dll,-\d\d\d\d\d')
        length = len(hex_data) - 46 - 4
        dictionary = dict()
        dictionary['size'] = hex_data[0:2]
        dictionary['version'] = hex_data[2:4]
        dictionary['signature'] = hex_data[4:8]
        dictionary['name_hex'] = hex_data[46:46 + length]
        temp_name = hex_data[46:46 + length].decode("utf-16")
        name_encoded = ''
        if str(temp_name).find('@shell32.dll') > 0:
            deleted_string = p.findall(temp_name)
            name_encoded = temp_name.replace(deleted_string[0], "")
            dictionary['name_encoded'] = name_encoded[:-1]
        else:
            dictionary['name_encoded'] = temp_name
        dictionary['name_length'] = length
        return dictionary

    def hasFileName(self, infile):
        # sign이 0이면 파일네임이 없는 것
        temp = infile
        number_of_sign = temp.count(b"\x04\x00\xef\xbe")
        return number_of_sign

    def hasUniqueFileFormat(self, infile):
        temp = infile
        number_of_unique_filename = temp.count(b'\xB0\x01\xC0')
        return number_of_unique_filename

    def extractFileName(self, infile):
        # ChecktheNumberofSignature
        index_list = list()
        current_index = 0
        temp = infile
        number_of_sign = temp.count(b"\x04\x00\xef\xbe")
        if number_of_sign is 0:
            pass
        else:
            # Find All index
            target = b"\x04\x00\xef\xbe"
            index = -1
            while True:
                index = temp.find(target, index + 1)
                if index == -1:
                    break
                index_list.append(index)  # index는 16진수값

        if len(index_list) != number_of_sign:
            exit()
        extension_dict = dict()
        for i in range(0, number_of_sign):
            start = (index_list[i]) - 4
            size = temp[start]
            data = temp[start:start + size]
            dictionary_key = "Extension_" + str(i + 1)
            extension_dict[dictionary_key] = (self.ParseExtensionBlock(data))

        self.extension_dict = extension_dict

    def FindDriveLetter(self, ch):
        # ord("A") = 65, ord("Z")=90
        if 65 <= ord(ch) and ord(ch) <= 90:
            self.drive_letter = ch
            return self.drive_letter

    def RunType1(self, infile):
        self.guid_folder = self.FindGUIDFolder(infile)
        self.extractFileName(infile)
        self.file_path = str(self.Assemble())

        return self.file_path

    def RunType2(self, infile, start_point):
        find_location = start_point + 3
        self.drive_letter = self.FindDriveLetter(infile[find_location:find_location + 1])
        try:
            self.extractFileName(infile)

        except:
            pass

        self.file_path = str(self.Assemble())

        return self.file_path

    def RunType3(self, infile):
        self.guid_folder = self.FindNetworkDrive(infile)
        self.extractFileName(infile)
        self.file_path = str(self.Assemble())
        return self.file_path

    def RunType4(self, infile):
        #TODO 수정해보기
        #self.guid_folder = 'Desktop'
        self.guid_folder = None
        self.extractFileName(infile)
        self.file_path = str(self.Assemble())
        return self.file_path

    def RunType5(self, infile):

        find_text = b'\xB0\x01\xC0'
        last_location = self.FindNewLocation(infile, find_text)

        result_dict = self.ParseStructure(infile[last_location:len(infile)])
        if 'name_full_path' in result_dict.keys():
            self.file_path = result_dict['name_full_path']
        else:
            pass

        return self.file_path

    def RunType6(self, infile):
        try :
            self.guid_folder = self.FindGUIDFolder(infile)
        except:
            try:
                self.unknown_guid
            except:
                self.guid_folder = "Unknown_GUID:" + self.unknown_guid
            pass
        self.file_path = self.guid_folder

    def RunType7(self, infile):
        try :
            self.guid_folder = self.FindGUIDFolder(infile)
        except:
            try:
                self.unknown_guid
            except:
                self.guid_folder = "Unknown_GUID:" + self.unknown_guid
            pass
        self.file_path = self.guid_folder

    def ParseStructure(self, infile):
        dictionary = dict()
        dictionary['sep'] = infile[0:4]
        dictionary['temp1'] = infile[4:15]
        length_first_folder = int.from_bytes(infile[15:15 + 4], byteorder='little')
        dictionary['length_first_folder'] = length_first_folder
        dictionary['name_first_folder'] = infile[19:19 + length_first_folder].decode('utf-16')[:-1]
        dictionary['temp2'] = infile[19 + length_first_folder:19 + length_first_folder + 15]
        start_full_path = 19 + length_first_folder + 16
        length_full_path = int.from_bytes(infile[start_full_path:start_full_path + 4], byteorder='little')
        dictionary['length_full_path'] = length_full_path
        dictionary['name_full_path'] = infile[start_full_path + 4:start_full_path + 4 + length_full_path].decode(
            'utf-16')[:-1]

        return dictionary

    def isGUIDFolder(self, infile):
        check_guid = infile[4:20]
        guid = cu.convert2mixedendian(check_guid)
        try:
            guid_folder = gu.GUID[guid]
            return True
        except:
            self.unknown_guid = guid
            return False

    def FindGUIDFolder(self, infile):
        guid_folder = ''
        guid_collection_list = gu.GUID.keys()
        check_first_guid = infile[4:20]
        first_guid = cu.convert2mixedendian(check_first_guid)
        check_second_guid = check_guid = infile[24:40]
        second_guid = cu.convert2mixedendian(check_second_guid)

        if first_guid in guid_collection_list and second_guid in guid_collection_list:
            guid_folder = gu.GUID[second_guid]

        elif first_guid in guid_collection_list and second_guid not in guid_collection_list:
            if gu.GUID[first_guid] == 'My Computer':
                guid_folder = 'Desktop'
            if gu.GUID[first_guid] == 'Shared Documents Folder (Users Files)':
                guid_folder = '%UserProfile%'
            if gu.GUID[first_guid] == 'OneDrive - 고려대학교':
                guid_folder = gu.GUID[first_guid]

        if first_guid not in guid_collection_list:
            #print("GUID Update 필요 " + first_guid)
            guid_folder = "unknown_guid : "+str(first_guid)

        return guid_folder

    def FindNetworkDrive(self, infile):
        # input : hex 파일
        # output : Network Driver Folder Name
        index_list = list()
        name = ''
        find_text = b'\xC3\x01\xC5'
        index = -1
        if find_text in infile:
            while True:
                index = infile.find(find_text, index + 1)
                if index == -1:
                    break
                index_list.append(index)

            start = (index_list[0]) - 2
            size = infile[start]
            data = infile[start:start + size]
            name = data[5:].decode("utf-8").split('\x00')[0]
            return name

    def FindNewLocation(self, infile, find_text):
        # input : hex 값
        # output : index 값
        index_list = list()
        index = -1
        while True:
            index = infile.find(find_text, index + 1)
            if index == -1:
                break
            index_list.append(index)
        return index_list[-1]

    def AssignToType(self, infile):
        saved_file = infile
        first_component = infile[0]
        len_of_file = len(infile)
        check_first_third_ch = infile[0:3]
        hasAutoPlay = infile.find(b'\x41\x00\x75\x00\x74\x00\x6F\x00\x4C\x00\x69\x00\x73\x00\x74\x00')
        hasDriveLetterSign = infile.find(b'\x19\x00\x2F')
        hasNetworkDrive = infile.find(b'\xC3\x01\xC5')
        hasFileName = infile.find(b"\x04\x00\xef\xbe")
        return (saved_file, first_component, len_of_file, check_first_third_ch, hasAutoPlay, hasDriveLetterSign,
                hasNetworkDrive, hasFileName)

def MRUFOLDER(reg_nt):
    mru_folder_list = []
    mru_folder_count = 0
    mru_folder_order = []
    check_first_third_ch_list = [b'\x19\x00\x1F', b'\x3A\x00\x1F',b'\x14\x00\\', b'\x55\x00\x1F']
    try:
        reg_key = reg_nt.find_key(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU")
    except Exception as exception:
        logger.error(exception)
    try:
        if reg_key != None:
            for reg_value in reg_key.values():
                if reg_value.name() == 'MRUListEx':
                    for i in range(0, len(list(reg_key.values()))-1):
                        mru_folder_order.append(int(binascii.b2a_hex(reg_value.data()[4*i:4*i+4][::-1]), 16))
            for order in mru_folder_order:
                for reg_value in reg_key.values():
                    if reg_value.name() == str(order):
                        mru_folder_information = MRU_Folder_Information()
                        mru_folder_list.append(mru_folder_information)
                        mru_folder_list[mru_folder_count].source_location = []
                        mru_folder_list[mru_folder_count].source_location.append('NTUSER-SOFTWARE/Microsoft/Windows/CurrentVersion/Explorer/ComDlg32/LastVisitedPidlMRU')
                        mru_folder_list[mru_folder_count].program_name = reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + 1].decode('utf-16')
                        start_data = reg_value.data().find(b'\x00\x00\x00') + 3
                        file = reg_value.data()
                        saved_file = file[start_data:len(file)]
                        (saved_file, first_component, len_of_file, check_first_third_ch, hasAutoPlay, hasDriveLetterSign, hasNetworkDrive, hasFileName) = MRU_Parser().AssignToType(saved_file)

                        if first_component == len_of_file - 2:
                            result = MRU_Parser().RunType4(saved_file)

                        if check_first_third_ch == b'\x19\x00\x1F':
                            start_point = hasDriveLetterSign
                            if start_point < 0:
                                pass
                            else:
                                result = MRU_Parser().RunType2(saved_file, start_point)
                        if check_first_third_ch == b'\x14\x00\x1F' or check_first_third_ch == b'\x14\x00\\':
                            if hasDriveLetterSign < 0 and hasNetworkDrive < 0:
                                result = MRU_Parser().RunType1(saved_file)
                            elif hasDriveLetterSign < 0 and hasNetworkDrive > 0:
                                result = MRU_Parser().RunType3(saved_file)
                            elif hasDriveLetterSign > 0 and hasNetworkDrive < 0:
                                start_point = hasDriveLetterSign
                                result = MRU_Parser().RunType2(saved_file, start_point)
                            else:
                                MRU_Parser().isGUIDFolder(saved_file)

                        if check_first_third_ch == b'\x3A\x00\x1F':
                            if MRU_Parser().isGUIDFolder(saved_file) is True:
                                result = MRU_Parser().RunType1(saved_file)
                            else:
                                try :
                                    result = MRU_Parser().RunType1(saved_file)
                                except:
                                    pass

                        if check_first_third_ch == b'\x55\x00\x1F':
                            start_point = hasDriveLetterSign
                            if start_point < 0:
                                pass
                            else:
                                result = MRU_Parser().RunType2(saved_file, start_point)

                        if MRU_Parser().hasUniqueFileFormat(saved_file) > 0 and hasFileName <0:
                            result = MRU_Parser().RunType5(saved_file)

                        mru_folder_list[mru_folder_count].accessed_folder = result
                        if mru_folder_count == 0:
                            mru_folder_list[mru_folder_count].modified_time = reg_key.last_written_timestamp().isoformat()+'Z'
                        mru_folder_list[mru_folder_count].registry_order = mru_folder_count+1
                        mru_folder_list[mru_folder_count].value = reg_value.name()
                        mru_folder_count = mru_folder_count + 1
                        break

    except Exception as exception:
        logger.error(exception)

    return mru_folder_list

