# -*- coding:utf-8 -*-
import sqlite3
import datetime
import os
import pandas as pd
import olefile
import re

"""
testcase
1.[win7]_가상환경_StickyNotes.snt
"""

class Sticky_Note_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    note_id = ''
    type = ''
    content = ''
    activated = ''
    createdtime = ''
    modifiedtime = ''

created_at_list = ["CreatedAt"]
updated_at_list = ["UpdatedAt"]

media_file_path_list = ["LocalFileRelativePath"]
media_mime_type_list = ["MimeType"]
media_id_list = ["Id"]
media_parent_id_list = ["ParentId"]

note_text_list = ["Text"]
note_is_open_list = ["IsOpen"]
note_id_list = ["Id"]

media_column_name_list = ["LocalFileRelativePath", "MimeType", "Id", "ParentId", "CreatedAt", "UpdatedAt"]
note_column_name_list = ["Text", "IsOpen", "Id", "CreatedAt", "UpdatedAt"]

our_db_column_name = ["Note_Id", "Type", "Content", "Activated", "CreatedTime", "ModifiedTime"]


def Parse2Type(data):
    return data


def Parse2FilePath(data):
    removable_text = "ms-appdata:///local/media/"
    if removable_text in data:
        result = data.replace(removable_text, "")

    return result


def Parse2TimeStamp(data):
    if data == 0:
        return 0
    return datetime.datetime.fromtimestamp(data / 10000000 - 62135596800).strftime('%Y-%m-%dT%H:%M:%S.%f')+'Z'


def Parse2Active(data):
    if data == 1:
        return "Open"
    else:
        return "Close"


def Parse2Id(data):
    return data


def Parse2Text(data):
    # id의 정규표현식 : \id=[a-zA-Z0-9_]{8}-[a-zA-Z0-9_]{4}-[a-zA-Z0-9_]{4}-[a-zA-Z0-9_]{4}-[a-zA-Z0-9_]{12}
    p = re.compile("\\\\id=[a-zA-Z0-9_]{8}-[a-zA-Z0-9_]{4}-[a-zA-Z0-9_]{4}-[a-zA-Z0-9_]{4}-[a-zA-Z0-9_]{12}")
    data = re.sub(p, "", data)

    return data


def saveDataInDict(our_db, output_column_name, data):
    our_db[output_column_name] = data


def ParseColumn(temp_result_dictionary, data, column_name, sep):
    if sep == "Media":
        saveDataInDict(temp_result_dictionary, "Activated", "NULL")
        if column_name in media_file_path_list:
            saveDataInDict(temp_result_dictionary, "Content", Parse2FilePath(data))
        elif column_name in media_mime_type_list:
            saveDataInDict(temp_result_dictionary, "Type", Parse2Type(data))
        # elif column_name in media_id_list:
        #     temp_result_dictionary["Media_Id"] = Parse2Id(data)
        elif column_name in media_parent_id_list:
            # 결과 값에서 Text와 image를 엮기 위해서 ParentId를 Id로 바꿔줌
            saveDataInDict(temp_result_dictionary, "Note_Id", Parse2Id(data))
        elif column_name in created_at_list:
            saveDataInDict(temp_result_dictionary, "CreatedTime", Parse2TimeStamp(data))
        elif column_name in updated_at_list:
            saveDataInDict(temp_result_dictionary, "ModifiedTime", Parse2TimeStamp(data))

    elif sep == "Note":
        saveDataInDict(temp_result_dictionary, "Type", "Text")
        if column_name in note_text_list:
            saveDataInDict(temp_result_dictionary, "Content", Parse2Text(data))
        elif column_name in note_is_open_list:
            saveDataInDict(temp_result_dictionary, "Activated", Parse2Active(data))

        elif column_name in note_id_list:
            saveDataInDict(temp_result_dictionary, "Note_Id", Parse2Id(data))

        elif column_name in created_at_list:
            saveDataInDict(temp_result_dictionary, "CreatedTime", Parse2TimeStamp(data))

        elif column_name in updated_at_list:
            saveDataInDict(temp_result_dictionary, "ModifiedTime", Parse2TimeStamp(data))


def convertSntResult(id, dictionary):
    our_db = dict()
    saveDataInDict(our_db, "Type", "text")
    saveDataInDict(our_db, "Activated", "NULL")
    saveDataInDict(our_db, "Note_Id", id)
    saveDataInDict(our_db, "CreatedTime", dictionary["created_time"])
    saveDataInDict(our_db, "ModifiedTime", dictionary["modified_time"])
    saveDataInDict(our_db, "Content", dictionary["content"])

    result = convertDictionaryToList(our_db)

    return result


def convertDictionaryToList(dict):
    result = list()
    for output_column_name in our_db_column_name:
        result.append(dict[output_column_name])
    return result


def divide2column(row, column_name_list, sep):
    result_sql = dict()
    for i in range(0, len(column_name_list)):
        ParseColumn(result_sql, row[i], column_name_list[i], sep)
    result = convertDictionaryToList(result_sql)
    return result


def ParseSnt(file):
    ole = olefile.OleFileIO(file)
    result = dict()
    for stream in ole.listdir():
        if stream[0].count("-") == 3 and stream[1] == "3":
            created_time = ole.getctime(stream[0])
            modified_time = ole.getmtime(stream[0])
            content = ole.openstream((stream)).read().decode("utf-16").rstrip("\u0000")
            result[stream[0]] = dict()
            result_stream = result[stream[0]]

            result_stream["created_time"] = str(created_time)
            result_stream["modified_time"] = str(modified_time)
            result_stream["content"] = content

    return result


def SaveDataInDict(our_db, output_colume_name, data):
    our_db[output_colume_name] = data


def STICKYNOTE(filename):

    result = []
    note_count = 0
    '''
    basepath = os.getcwd()
    #filename = "[win10]_1809_가상환경_plum.sqlite"
    target_file = basepath + "//" + filename
    '''
    target_file = filename

    # olefile signature = 0x D0 CF 11 E0 A1 B1 1A E1
    # sqlite signature = 0x 53 51 4C 69 74 65 20 66 6F 72 6D 61 74 20 33 00

    if not olefile.isOleFile(target_file):
        conn = sqlite3.connect(target_file)
        cur = conn.cursor()

        sql_command = "SELECT "
        for column_name in note_column_name_list:
            sql_command += column_name
            if column_name is not note_column_name_list[-1]:
                sql_command += ', '
        sql_command += " FROM Note"

        note_data = cur.execute(sql_command)

        for row in note_data:
            note_data_row = divide2column(row, note_column_name_list, "Note")
            sticky_note_information = Sticky_Note_Information()
            result.append(sticky_note_information)
            result[note_count].note_id = note_data_row[0]
            result[note_count].type = note_data_row[1]
            result[note_count].content = note_data_row[2]
            result[note_count].activated = note_data_row[3]
            result[note_count].createdtime = note_data_row[4]
            result[note_count].modifiedtime = note_data_row[5]
            note_count = note_count + 1

        sql_command = "SELECT "
        for column_name in media_column_name_list:
            sql_command += column_name
            if column_name is not media_column_name_list[-1]:
                sql_command += ', '
        sql_command += " FROM Media"
        media_data = cur.execute(sql_command)

        for row in media_data:
            media_data_row = divide2column(row, media_column_name_list, "Media")
            sticky_note_information = Sticky_Note_Information()
            result.append(sticky_note_information)
            result[note_count].note_id = media_data_row[0]
            result[note_count].type = media_data_row[1]
            result[note_count].content = ''.join(media_data_row[2].split())
            result[note_count].activated = media_data_row[3]
            result[note_count].createdtime = media_data_row[4]
            result[note_count].modifiedtime = media_data_row[5]
            note_count = note_count + 1

    elif olefile.isOleFile(target_file):
        result_snt = ParseSnt(target_file)
        for key, value in result_snt.items():
            rs = convertSntResult(key, value)
            result.append(rs)

    return result





