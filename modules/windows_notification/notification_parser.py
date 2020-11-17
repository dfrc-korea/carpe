from datetime import timezone, datetime
import yarp
import sqlite3

import modules.windows_notification.old_notification_parser as old_notification_parser


def get_win_version(_file_object_dict):
    primary = _file_object_dict["primary"]
    log1 = _file_object_dict["log1"]
    log2 = _file_object_dict["log2"]

    hive = yarp.Registry.RegistryHive(primary)
    # if not log1 is None and not log2 is None:
    #     hive.recover_new(log1, log2)

    current_version_key = hive.find_key('Microsoft\Windows NT\CurrentVersion')

    major_version, build_number = "", ""
    try:
        major_version = current_version_key.value('CurrentMajorVersionNumber').data()
        build_number = int(current_version_key.value('CurrentBuildNumber').data().rstrip('\x00'))
    except AttributeError or FileNotFoundError:
        print("Key not found")

    return major_version, build_number


def old_noti_parser(path):
    noti_list = []
    chunks = []
    old_notification_parser.process_db(path, chunks)

    for chunk in chunks:
        if len(chunk.Badge.URI):
            badge_uri_info = ('BADGE_URI', 0, chunk.Badge.TimeStamp1, chunk.Badge.TimeStamp2,
                              chunk.Badge.URI, "")
            noti_list.append(badge_uri_info)

        if chunk.Badge.NotificationId != 0 and len(chunk.Badge.Xml) > 0:
            temp = old_notification_parser.get_xml_content(chunk.Badge.Xml)  # .decode()
            xml_content = _remove_tab_new_line(temp)
            badge_other_info = ('BADGE_OTHER', chunk.Badge.NotificationId, chunk.Badge.TimeStamp3, "",
                                xml_content, _remove_tab_new_line(chunk.Badge.Xml))
            noti_list.append(badge_other_info)

        for toast in chunk.Toasts:
            xml_content = ""
            if len(toast.Xml) > 0:
                temp = old_notification_parser.get_xml_content(toast.Xml)
                xml_content = _remove_tab_new_line(temp)
            toast_info = ('TOAST', toast.NotificationId, toast.TimeStamp1, toast.TimeStamp2,
                          xml_content, _remove_tab_new_line(toast.Xml))
            noti_list.append(toast_info)

        for tile in chunk.Tiles:
            xml_content = ""
            if len(tile.Xml) > 0:
                temp = old_notification_parser.get_xml_content(tile.Xml)
                xml_content = _remove_tab_new_line(temp)
            tile_info = ('TILE', tile.NotificationId, tile.TimeStamp1, tile.TimeStamp2,
                         xml_content, _remove_tab_new_line(tile.Xml))
            noti_list.append(tile_info)

    return noti_list


def new_noti_parser(path):
    # key: RecordId / value: [PrimaryId, HandlerType, CreatedTime, ModifiedTime]
    noti_handler_dict = {}

    # key: Order
    # value: [Id, HandlerId(=RecordId), Type, Payload, ExpiryTime,
    # ArrivalTime, BootId, PrimaryId, HandlerType, CreatedTime, ModifiedTime]
    noti_dict = {}

    con = sqlite3.connect(path)
    cur = con.cursor()

    cur.execute('select * from NotificationHandler')
    for row in cur:
        # 0: RecordId / 1: PrimaryId, 3: HandlerType, 6: CreatedTime, 7: ModifiedTime
         noti_handler_dict[row[0]] = [row[1], row[3], _str_to_timestamp(row[6]), _str_to_timestamp(row[7])]

    cur.execute('select * from Notification')
    for row in cur:
        # 0: Order /  1: Id, 2: HandlerId(=RecordId), 4: Type, 5: Payload, 8: ExpiryTime, 9: ArrivalTime, 12: BootId
        noti_dict[row[0]] = [row[1], row[2], row[4], row[5],
                             _convert_timestamp(row[8]), _convert_timestamp(row[9]), _convert_timestamp(row[12])]
        noti_dict[row[0]].extend(noti_handler_dict[row[2]])

    cur.close()
    con.close()

    # convert list_dict to list
    noti_list = [[key] + val for dic in [noti_dict] for key, val in dic.items()]

    return noti_list


def _convert_timestamp(from_ts):
    try:
        to_ts = datetime.fromtimestamp((from_ts - 116444736000000000) // 10000000, tz=timezone.utc).isoformat()
    except OSError:
        to_ts = 0
    return to_ts


def _str_to_timestamp(from_ts):
    to_ts = datetime.strptime(from_ts, '%Y-%m-%d %H:%M:%S').isoformat()
    return str(to_ts)


def _remove_tab_new_line(_str):
    return _str.replace("\t", " ").replace("\r", "").replace("\n", " ")
