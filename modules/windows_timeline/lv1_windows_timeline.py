# -*- coding:utf-8 -*-
import sqlite3
import json
import datetime


class Windows_Timeline_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    program_name = ''
    display_name = ''
    content = ''
    activity_type = ''
    focus_seconds = ''
    start_time = ''
    end_time = ''
    activity_id = ''
    platform = ''
    created_time = ''
    created_in_cloud_time = ''
    last_modified_time = ''
    last_modified_one_client_time = ''
    original_last_modified_on_client_time = ''
    local_only_flag = ''
    group = ''
    clipboardpayload = ''
    timezone = ''


"""
TEST Enviroment
Windows 10 1909 (OS Build 18363.720)

program_name : AppId -> application
display_name : Payload -> display Text, app display
content : AppActivityId
activity_type : ActivityType
focus_seconds : if EndTime-StartTime > 0 -> EndTime-StartTime
start_time : StartTime
end_time : EndTime
activity_id : Id(Mixed GUID)
platform : AppId -> platform
created_time : ?? 추가분석 필요 일단 NULL
created_in_cloud_time : CreatedInCloud
last_modified_time : LastModifiedTime
last_modified_on_client_time : LastModifiedOnClient
original_last_modified_on_client_time : OriginalLastModifiedOnClient
local_only_flag : IsLocalOnly
"""
# db에 들어갈 column_name
our_db_column_name = ['program_name', 'display_name', 'content', 'activity_type', 'focus_seconds', 'start_time', \
                      'end_time', 'activity_id', 'platform','created_in_cloud_time', 'last_modified_time', \
                      'last_modified_time', 'last_modified_on_client_time', 'original_last_modified_on_client_time', 'local_only_flag', 'group', 'clipboardpayload(base64)', 'timezone']
known_path_dict = dict()
known_path_column = ["6D809377-6AF0-444B-8957-A3773F02200E", "7C5A40EF-A0FB-4BFC-874A-C0F2E0B9FA8E",
                     "1AC14E77-02E7-4E5D-B744-2EB1AE5198B7", "F38BF404-1D43-42F2-9305-67DE0B28FC23",
                     "D65231B0-B2F1-4857-A4CE-A8E7C6EA7D27"]

known_path_data = ["%ProgramFiles% (%SystemDrive%\\Program Files)", "%SystemDrive%\Program Files (x86)", "%SystemRoot%\\System", "%SystemRoot%",
                   "%SystemRoot%\\system32"]

for i in range(0, len(known_path_column)):
    known_path_dict[known_path_column[i]] = known_path_data[i]

parsing_column_name_list = ['AppId', 'Payload', 'AppActivityId', 'ActivityType', 'StartTime', 'EndTime', 'Id',
                            'CreatedInCloud', 'LastModifiedTime', 'LastModifiedOnClient', 'OriginalLastModifiedOnClient', 'IsLocalOnly', 'Group', 'ClipboardPayload']

# 버전에 따라서 DB column명이 달라질 때를 대비해서 만들어놓음.
app_id_list = ["AppId"]
payload_list = ["Payload"]
app_activity_id_list = ["AppActivityId"]
activity_type_list = ["ActivityType"]
start_time_list = ["StartTime"]
end_time_list = ["EndTime"]
id_list = ["Id"]
created_in_cloud_list = ["CreatedInCloud"]
last_modified_time_list = ["LastModifiedTime"]
last_modified_on_client_list = ["LastModifiedOnClient"]
original_last_modified_on_client_list = ["OriginalLastModifiedOnClient"]
is_local_list = ["IsLocalOnly"]
clipboardpayload_list = ["ClipboardPayload"]
group_list = ["Group"]


def convertTime(unixtime):
    if unixtime is not None:
        temp_time = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=unixtime)
        date = temp_time.isoformat()
        date += 'Z'
        return date
    else:
        pass

def convertbe(bytes):
    result = bytes
    return result

def convertle(bytes):
    result = bytes[::-1]
    return result

def parseAppActivityId(data):
    known_string = 'ECB32AF3-1440-4086-94E3-5311F97F89C4'

    if data.find(known_string) >= 0 :
        data = data.strip(known_string)
        return data
    elif data.find(known_string) < 0:
        return data

def parseType(data):
    #참고 : https://github.com/kacos2000/WindowsTimeline/blob/master/WindowsTimeline.sql
    type = ""
    if data == 2:
        type = "Notification"
    elif data == 3:
        type = "Mobile Backup"
    elif data == 5:
        type = "Open App/File/Page"
    elif data == 6:
        type = "App In Use/Focus"
    elif data == 10:
        type = "Clipboard"
    elif data == 16:
        type = "Copy/Paste"
    elif data == 11 or 12 or 15:
        type = "System"

    return type

def parseLocal(data):
    local_only_flag = "False"
    if data == 1:
        local_only_flag = "True"

    return local_only_flag

def parseId(data):
    #mixed endian 변환
    le1 = data[0:4]
    le2 = data[4:6]
    le3 = data[6:8]
    be1 = data[8:10]
    be2 = data[10:]

    activity_id = convertle(le1).hex() + "-" + convertle(le2).hex() + "-" + convertle(le3).hex() + "-" + convertbe(be1).hex() + "-" + convertbe(be2).hex()
    return activity_id

def parseAppId (data) :
    #AppId parsing
    #Appid structure : {'application': '....', 'platform' : '...'}, ...

    result = list()
    _json_data = json.loads(data)
    json_data = _json_data[0]
    if json_data['platform'] == 'afs_crossplatform':
        json_data = _json_data[1]
        platform = json_data['platform']
        application = json_data['application']
    else :
        platform = json_data['platform']
        application = json_data['application']


    for i in range (0, len(known_path_column)):
        if known_path_column[i] in application:
            replaced_path = "{" + known_path_column[i] + "}"
            application = application.replace(replaced_path, known_path_dict[known_path_column[i]])


    result.append(application)
    result.append(platform)

    return result

def parseClipBoard(data):
    #print(data)
    if data is not None:
        json_data = json.loads(data)
        keys = [key for key in json_data]
        if len(keys) == 0 :
            return None

        elif len(keys) !=0 and 'content' in keys[0] :
            encoded_text = keys[0]['content']
            return encoded_text
    else:
        return None

def parseGroup(data):
    return data

def parsePayload(data) :
    result = list()  # display Text, app display

    display_name = ""
    timezone = ""
    focus_seconds = 0
    try:
        json_data = json.loads(data)
        keys = [key for key in json_data]
        if "displayText" in keys:
            displayText = json_data['displayText']
            result.append(displayText)
        if "appDisplayName" in keys:
            displayname = json_data['appDisplayName']
            result.append(displayname)
        if "activeDurationSeconds" in keys :
            focus_seconds = json_data["activeDurationSeconds"]
        # if "clipboardDataId" in keys:
        #     clipboard_id = json_data["clipboardDataId"]
        if "userTimezone" in keys:
            timezone = json_data["userTimezone"]
        if len(result) >= 2 :
            display_name = result[0] + " (" + result[1] + ")"
        else :
            display_name = result[0]

    except:
        pass

    return display_name, focus_seconds, timezone

def saveDataInDict(our_db, output_column_name, data):
    our_db[output_column_name] = data

def parsecolumn(our_db, data, column_name):

    if column_name in parsing_column_name_list:
        saveDataInDict(our_db, 'created_time', '')
        if column_name in app_id_list:
            (program_name, platform) = parseAppId(data)
            saveDataInDict(our_db, 'program_name', program_name)
            saveDataInDict(our_db, 'platform', platform)
        elif column_name in payload_list:
            (display_name, focus_seconds, timezone) = parsePayload(data)
            saveDataInDict(our_db, 'display_name', display_name)
            saveDataInDict(our_db, 'focus_seconds', focus_seconds)
            saveDataInDict(our_db, 'timezone', timezone)
        elif column_name in  app_activity_id_list:
            saveDataInDict(our_db, 'content', parseAppActivityId(data))
        elif column_name in activity_type_list :
            saveDataInDict(our_db, 'activity_type', parseType(data))
        elif column_name in start_time_list:
            saveDataInDict(our_db, 'start_time', convertTime(data))
        elif column_name in end_time_list :
            saveDataInDict(our_db, 'end_time', convertTime(data))
        elif column_name in id_list :
            saveDataInDict(our_db, 'activity_id', parseId(data))
        elif column_name in created_in_cloud_list :
            saveDataInDict(our_db, 'created_in_cloud_time', convertTime(data))
        elif column_name in last_modified_time_list :
            saveDataInDict(our_db, 'last_modified_time', convertTime(data))
        elif column_name in last_modified_on_client_list:
            saveDataInDict(our_db, 'last_modified_on_client_time', convertTime(data))
        elif column_name in original_last_modified_on_client_list :
            saveDataInDict(our_db, 'original_last_modified_on_client_time', convertTime(data))
        elif column_name in is_local_list:
            saveDataInDict(our_db, 'local_only_flag', parseLocal(data))
        elif column_name in clipboardpayload_list :
            saveDataInDict(our_db, 'clipboardpayload(base64)', parseClipBoard(data))
        elif column_name in group_list:
            saveDataInDict(our_db, 'group', parseGroup(data))
    else :
        pass


def convertDictionaryToList(dict):
    result = list()
    for output_column_name in our_db_column_name:
        result.append(dict[output_column_name])
    return result

def divide2column(row, column_name_list) :
    our_db = dict()
    for i in range(0, len(column_name_list)):
        parsecolumn(our_db, row[i], column_name_list[i])
    result = convertDictionaryToList(our_db)
    return result

def WINDOWSTIMELINE(filename):

    result = []
    column_name_list = []
    timeline_count = 0
    targetDB = filename

    conn = sqlite3.connect(targetDB)
    cur = conn.cursor()

    # 윈도우 버전별로 칼럼이 달라져서 column_name_list를 새롭게 구해야함.
    sql_command = f"SELECT sql FROM sqlite_master WHERE tbl_name='Activity' AND name = 'Activity'"

    cur.execute(sql_command)

    first_row = None
    for row in cur:
        first_row = str(row)
    if not first_row:
        # TODO: 이유 찾아야 함
        return False

    first_column = first_row.split('(')
    column_list = first_column[2]
    start = '['
    end = ']'
    index1 = -1
    index2 = -1
    while True:
        index1 = column_list.find(start, index1 + 1)
        index2 = column_list.find(end, index2+1)
        if index1 == -1 or index2 ==-1:
            break
        column_name_list.append(column_list[index1+1:index2])

    sql_command = "SELECT *"
    sql_command += " FROM Activity"
    cur.execute(sql_command)

    for row in cur:
        rs = divide2column(row,column_name_list)
        windows_timeline_information = Windows_Timeline_Information()
        result.append(windows_timeline_information)
        result[timeline_count].program_name = rs[0]
        result[timeline_count].display_name = rs[1]
        if len(rs[2]) == 0:
            result[timeline_count].content = rs[2]
        else:
            if rs[2][0] == '\\':
                result[timeline_count].content = rs[2][1:]
            else:
                result[timeline_count].content = rs[2]
        result[timeline_count].activity_type = rs[3]
        result[timeline_count].focus_seconds = rs[4]
        result[timeline_count].start_time = rs[5]
        result[timeline_count].end_time = rs[6]
        result[timeline_count].activity_id = rs[7]
        result[timeline_count].platform = rs[8]
        result[timeline_count].created_time = rs[9]
        result[timeline_count].created_in_cloud_time = rs[10]
        result[timeline_count].last_modified_time = rs[11]
        result[timeline_count].last_modified_on_client_time = rs[12]
        result[timeline_count].original_last_modified_on_client_time = rs[13]
        result[timeline_count].local_only_flag = rs[14]
        result[timeline_count].group = rs[15]
        result[timeline_count].clipboardpayload= rs[16]
        result[timeline_count].timezone = rs[17]
        timeline_count = timeline_count + 1

    return result