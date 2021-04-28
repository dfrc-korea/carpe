import sqlite3
import datetime
import json


def _convert_unixtimestamp(timestamp):
    if timestamp is None:
        time = ''
        return time

    if len(str(timestamp)) == 0:
        time = ''
        return time

    if len(str(timestamp)) == 10:
        timestamp = int(str(timestamp)+'000')
        time = datetime.datetime.fromtimestamp(timestamp/1000.0).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return time

    if len(str(timestamp)) == 13:
        time = datetime.datetime.fromtimestamp(timestamp/1000.0).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return time

    if len(str(timestamp)) == 16:
        timestamp = int(str(timestamp)[:-3])
        time = datetime.datetime.fromtimestamp(timestamp/1000.0).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return time


def _visit_type(type):
    if type == 1:
        visit_type = "LINK"
        return visit_type
    if type == 2:
        visit_type = "TYPED"
        return visit_type
    if type == 3:
        visit_type = "BOOKMARK"
        return visit_type
    if type == 4:
        visit_type = "EMBED"
        return visit_type
    if type == 5:
        visit_type = "REDIRECT_PERMANENT"
        return visit_type
    if type == 6:
        visit_type = "REDIRECT_TEMPORARY"
        return visit_type
    if type == 7:
        visit_type = "DOWNLOAD"
        return visit_type
    if type == 8:
        visit_type = "FRAMED_LINK"
        return visit_type
    if type == 9:
        visit_type = "RELOAD"
        return visit_type
    else:
        visit_type = "type error"
        return visit_type


def _visit_type_description(type):
    if type == 1:
        description = "The user followed a link and got a new toplevel window."
        return description
    if type == 2:
        description = "The user typed the page''s URL in the URL bar or selected it from URL bar autocomplete results, clicked on it from a history query."
        return description
    if type == 3:
        description = "The user followed a bookmark to get to the page."
        return description
    if type == 4:
        description = "Set when some inner content is loaded. This is true of all images on a page, and the contents of the iframe. It is also true of any content in a frame, regardless of whether or not the user clicked something to get there."
        return description
    if type == 5:
        description = "The transition was a permanent redirect."
        return description
    if type == 6:
        description = "The transition was a temporary redirect."
        return description
    if type == 7:
        description = "The transition is a download."
        return description
    if type == 8:
        description = "The user followed a link and got a visit in a frame."
        return description
    if type == 9:
        description = "The page has been reloaded."
        return description
    else:
        description = "description error"
        return description


def _bookmark_dir_tree(row, bookmark_id_title, bookmark_id_parent):

    if row[1] == 1: # CASE : parent is root
        mod_path = bookmark_id_title[row[1]] + 'root/' + row[2]
        return mod_path

    else: # CASE : parent is not root
        mod_path = bookmark_id_title[row[1]] + '/' + row[2]
        new_row = (row[0], bookmark_id_parent[row[1]], mod_path)
        mod_path = _bookmark_dir_tree(new_row, bookmark_id_title, bookmark_id_parent)
        return mod_path


def firefox_visit_history(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('select id, url from moz_places')
        url_dict = cur.fetchall()
        url_dict = dict(url_dict)
    except:
        print("[Web/Firefox] Visit History " + "\033[31m" + "url dict query error" + "\033[0m")
        url_dict = {}

    try:
        cur.execute('select id, place_id from moz_historyvisits')
        from_url = cur.fetchall()
    except:
        print("[Web/Firefox] Visit History " + "\033[31m" + "from_url dict query error" + "\033[0m")
        from_url = []

    match_result = []
    for row in from_url:
        id = row[0]
        try:
            place_id = url_dict[row[1]]
        except KeyError:
            place_id = row[1]
        match_row = tuple([id, place_id])
        match_result.append(match_row)
    from_url_dict = dict(match_result)

    try:
        cur.execute(
            'select id, from_visit, place_id, visit_date, visit_type from moz_historyvisits order by visit_date asc')
        visit_history = cur.fetchall()
    except:
        # print("[Web/Firefox] Visit History " + "\033[31m" + "Main Query Error" + "\033[0m")
        visit_history = []

    result = []
    for row in visit_history:
        id = row[0]

        try:
            from_visit = from_url_dict[row[1]]
        except KeyError:
            from_visit = row[1]

        if type(from_visit) == str and ("\'" or "\"") in from_visit:
            from_visit = from_visit.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        try:
            place_id = url_dict[row[2]]
        except KeyError:
            place_id = row[2]

        if type(place_id) == str and ("\'" or "\"") in place_id:
            place_id = place_id.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        visit_date = _convert_unixtimestamp(row[3])
        visit_type = _visit_type(row[4])
        visit_type_desc = _visit_type_description(row[4])

        outputformat = [id, from_visit, place_id, visit_date, visit_type, visit_type_desc]
        result.append(outputformat)

    conn.close()

    return result


def firefox_visit_urls(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute(
            'select url, title, rev_host, visit_count, hidden, typed, frecency, last_visit_date, guid, foreign_count, '
            'description, preview_image_url from moz_places')
        visit_urls = cur.fetchall()
    except:
        # print("[Web/Firefox] Visit Urls " + "\033[31m" + "Main Query Error" + "\033[0m")
        visit_urls = []

    result = []

    for row in visit_urls:

        if type(row[0]) == str and ("\'" or "\"") in row[0]:
            url = row[0].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            url = row[0]

        if type(row[1]) == str and ("\'" or "\"") in row[1]:
            title = row[1].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            title = row[1]

        rev_host = row[2]
        visit_count = row[3]
        hidden = row[4]
        typed = row[5]
        frecency = row[6]
        last_visit_date = _convert_unixtimestamp(row[7])
        guid = row[8]
        foreign_count = row[9]

        if type(row[10]) == str and ("\'" or "\"") in row[10]:
            description = row[10].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            description = row[10]

        preview_image_url = row[11]

        outputformat = [url, title, rev_host, visit_count, hidden, typed, frecency, last_visit_date, guid,
                        foreign_count, description, preview_image_url]
        result.append(outputformat)

    conn.close()

    return result


def firefox_domain(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute(
            'select prefix, host, frecency from moz_origins')
        domains = cur.fetchall()
    except:
        # print("[Web/Firefox] Domain " + "\033[31m" + "Main Query Error" + "\033[0m")
        domains = []

    result = []

    for row in domains:

        prefix = row[0]
        host = row[1]
        frecency = row[2]

        outputformat = [prefix, host, frecency]
        result.append(outputformat)

    conn.close()

    return result


def firefox_downloads(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('select id, url from moz_places')
        url_dict = cur.fetchall()
        url_dict = dict(url_dict)
    except:
        print("[Web/Firefox] Downloads " + "\033[31m" + "url dict query error" + "\033[0m")
        url_dict = {}

    try:
        cur.execute('select place_id, anno_attribute_id, content, flags, expiration, type, dateAdded, '
                    'lastModified from moz_annos order by place_id asc')
        download_record = cur.fetchall()
    except:
        # print("[Web/Firefox] Downloads " + "\033[31m" + "Main Query Error" + "\033[0m")
        download_record = []

    file_path_record = []
    meta_record = []
    result = []

    for row in download_record:
        if row[2][0:4] == 'file':

            place_id = row[0]
            url = url_dict[row[0]]
            file_path = row[2]
            flags = row[3]
            expiration = row[4]
            record_type = row[5]
            time = row[6]

            record_format = (place_id, url, file_path, flags, expiration, record_type, time)
            file_path_record.append(record_format)

        elif row[2][2:7] == 'state':
            place_id = row[0]
            meta_json = json.loads(row[2])
            try:
                state = meta_json["state"]
            except:
                state = ''
            try:
                end_time = meta_json["endTime"]
            except:
                end_time = ''
            try:
                file_size = meta_json["fileSize"]
            except:
                file_size = ''
            time = row[6]

            record_format = (place_id, state, end_time, file_size, time)
            meta_record.append(record_format)

        else:
            pass

    if len(file_path_record) != len(meta_record):
        print("[Web/Firefox] Downloads " + "\033[31m" + "There is record mismatch" + "\033[0m" +
              ". Check \"place.sqlite\" file.")

        for file_path_row in file_path_record:
            for meta_row in meta_record:
                if file_path_row[0] == meta_row[0]:
                    url = file_path_row[1]
                    if type(url) == str and ("\'" or "\"") in url:
                        url = url.replace("\'", "\'\'").replace('\"', '\"\"')
                    else:
                        pass

                    download_path = file_path_row[2]
                    if type(download_path) == str and ("\'" or "\"") in download_path:
                        download_path = download_path.replace("\'", "\'\'").replace('\"', '\"\"')
                    else:
                        pass

                    download_file_size = meta_row[3]
                    state = meta_row[1]

                    if int(str(file_path_row[6])[:-3]) >= meta_row[2]:
                        start_time = _convert_unixtimestamp(meta_row[2])
                        end_time = _convert_unixtimestamp(file_path_row[6])
                    else:
                        start_time = _convert_unixtimestamp(file_path_row[6])
                        end_time = _convert_unixtimestamp(meta_row[2])

                    flags = file_path_row[3]
                    expiration = file_path_row[4]
                    download_type = file_path_row[5]

                    outputformat = (url, download_path, download_file_size, state, start_time, end_time,
                                    flags, expiration, download_type)
                    result.append(outputformat)

                else:
                    pass

    else:
        for file_path_row, meta_row in zip(file_path_record, meta_record):

            url = file_path_row[1]
            if type(url) == str and ("\'" or "\"") in url:
                url = url.replace("\'", "\'\'").replace('\"', '\"\"')
            else:
                pass

            download_path = file_path_row[2]
            if type(download_path) == str and ("\'" or "\"") in download_path:
                download_path = download_path.replace("\'", "\'\'").replace('\"', '\"\"')
            else:
                pass

            download_file_size = meta_row[3]
            state = meta_row[1]

            if int(str(file_path_row[6])[:-3]) >= meta_row[2]:
                start_time = _convert_unixtimestamp(meta_row[2])
                end_time = _convert_unixtimestamp(file_path_row[6])
            else:
                start_time = _convert_unixtimestamp(file_path_row[6])
                end_time = _convert_unixtimestamp(meta_row[2])

            flags = file_path_row[3]
            expiration = file_path_row[4]
            download_type = file_path_row[5]

            outputformat = [url, download_path, download_file_size, state, start_time, end_time, flags, expiration,
                            download_type]
            result.append(outputformat)

    conn.close()

    return result


def firefox_cookies(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('pragma table_info(\'moz_cookies\')')
        result = cur.fetchall()
    except:
        print("[Web/Firefox] Cookies " + "\033[31m" + "column check query error" + "\033[0m")
        result = []

    column_list = []
    for row in result:
        column_list.append(row[1])

    if 'schemeMap' in column_list:
        try:
            cur.execute(
                'select name, value, host, path, expiry, lastAccessed, creationTime, isSecure, isHttpOnly, '
                'inBrowserElement, sameSite, rawSameSite, schemeMap from moz_cookies order by id asc')
            cookies = cur.fetchall()
        except:
            # print("[Web/Firefox] Cookies " + "\033[31m" + "Main Query Error" + "\033[0m")
            cookies = []
    else:
        try:
            cur.execute(
                'select name, value, host, path, expiry, lastAccessed, creationTime, isSecure, isHttpOnly, '
                'inBrowserElement, sameSite, rawSameSite from moz_cookies order by id asc')
            cookies = cur.fetchall()
        except:
            # print("[Web/Firefox] Cookies " + "\033[31m" + "Main Query Error" + "\033[0m")
            cookies = []

    result = []
    for row in cookies:
        name = row[0]
        value = row[1]
        host = row[2]
        path = row[3]
        expire_time = _convert_unixtimestamp(row[4])
        last_accessed_time = _convert_unixtimestamp(row[5])
        created_time = _convert_unixtimestamp(row[6])
        is_secure = row[7]
        is_http_only = row[8]
        inbrowser_element = row[9]
        same_site = row[10]
        raw_same_site = row[11]

        try:
            scheme_map = row[12]
        except IndexError:
            scheme_map = ''

        outputformat = [name, value, host, path, expire_time, last_accessed_time, created_time, is_secure,
                        is_http_only, inbrowser_element, same_site, raw_same_site, scheme_map]
        result.append(outputformat)

    conn.close()

    return result


def firefox_perms(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()
    try:
        cur.execute('select origin, type, permission, expireType, expireTime, modificationTime from moz_perms '
                    'order by id asc')
        perms = cur.fetchall()
    except:
        # print("[Web/Firefox] Permissions " + "\033[31m" + "Main Query Error" + "\033[0m")
        perms = []

    result = []
    for row in perms:

        url = row[0]
        type = row[1]
        permissions = row[2]
        expire_type = row[3]
        expire_time = _convert_unixtimestamp(row[4])
        modified_time = _convert_unixtimestamp(row[5])

        outputformat = [url, type, permissions, expire_type, expire_time, modified_time]
        result.append(outputformat)

    conn.close()

    return result


def firefox_forms(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('select fieldname, value, timesUsed, firstUsed, lastUsed, guid from moz_formhistory '
                    'order by id asc')
        forms = cur.fetchall()
    except:
        # print("[Web/Firefox] Form History " + "\033[31m" + "Main Query Error" + "\033[0m")
        forms = []
    result = []

    for row in forms:

        fieldname = row[0]
        value = row[1]
        if type(value) == str and ("\'" or "\"") in value:
            value = value.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        times_used = row[2]
        first_used_time = _convert_unixtimestamp(row[3])
        last_used_time = _convert_unixtimestamp(row[4])
        guid = row[5]

        outputformat = [fieldname, value, times_used, first_used_time, last_used_time, guid]
        result.append(outputformat)

    conn.close()

    return result


def firefox_favicons(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('select id, page_url from moz_pages_w_icons order by id asc')
        page_dict = cur.fetchall()
        page_dict = dict(page_dict)
    except:
        print("[Web/Firefox] Favicons " + "\033[31m" + "page dict query error" + "\033[0m")
        page_dict = {}

    try:
        cur.execute('select page_id, icon_id from moz_icons_to_pages')
        icon_page_dict_match = cur.fetchall()
    except:
        print("[Web/Firefox] Favicons " + "\033[31m" + "icon page dict query error" + "\033[0m")
        icon_page_dict_match = []

    icon_page_dict = {}
    for row in icon_page_dict_match:
        try:
            check_icon_id = icon_page_dict[row[1]]

            if type(check_icon_id) == list:
                check_icon_id.append(page_dict[row[0]])
                icon_page_dict[row[1]] = check_icon_id

            else:
                icon_page_dict[row[1]] = [check_icon_id, page_dict[row[0]]]

        except KeyError:
            icon_page_dict[row[1]] = page_dict[row[0]]
    try:
        cur.execute('select id, icon_url, fixed_icon_url_hash, width, root, color, expire_ms, data from moz_icons order by id asc')
        favicons = cur.fetchall()
    except:
        # print("[Web/Firefox] Favicons " + "\033[31m" + "Main Query Error" + "\033[0m")
        favicons = []

    result = []
    for row in favicons:
        icon_id = row[0]
        icon_url = row[1]
        if type(icon_url) == str and ("\'" or "\"") in icon_url:
            icon_url = icon_url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        icon_url_hash = row[2]
        width = row[3]
        root = row[4]

        if row[5] == None:
            color = ''

        expired_time = _convert_unixtimestamp(row[6])
        data = row[7]

        try:
            if type(icon_page_dict[row[0]]) == list:

                for row in icon_page_dict[row[0]]:

                    page_url_list = row

                    outputformat = [icon_id, icon_url, icon_url_hash, width, root, color, expired_time, data,
                                    page_url_list]
                    result.append(outputformat)

            else:
                page_url_list = icon_page_dict[row[0]]

                outputformat = [icon_id, icon_url, icon_url_hash, width, root, color, expired_time, data, page_url_list]
                result.append(outputformat)

        except KeyError:
            page_url_list = ''

            outputformat = [icon_id, icon_url, icon_url_hash, width, root, color, expired_time, data, page_url_list]
            result.append(outputformat)

    conn.close()

    return result


def firefox_prefs(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('select id, name from settings order by id asc')
        setting_dict = cur.fetchall()
        setting_dict = dict(setting_dict)
    except:
        print("[Web/Firefox] Preference " + "\033[31m" + "setting dict query error" + "\033[0m")
        setting_dict = {}

    try:
        cur.execute('select id, name from groups order by id asc')
        groups_dict = cur.fetchall()
        groups_dict = dict(groups_dict)
    except:
        print("[Web/Firefox] Preference " + "\033[31m" + "group dict query error" + "\033[0m")
        groups_dict = {}

    try:
        cur.execute('select id, groupID, settingID, value, timestamp from prefs order by id asc')
        prefs = cur.fetchall()
    except:
        # print("[Web/Firefox] Preference " + "\033[31m" + "Main Query Error" + "\033[0m")
        prefs = []

    result = []
    for row in prefs:
        url = groups_dict[row[1]]
        setting = setting_dict[row[2]]
        value = row[3]
        time = _convert_unixtimestamp(int(row[4]*(10**3)))

        outputformat = [url, setting, value, time]
        result.append(outputformat)

    conn.close()

    return result


def firefox_bookmarks(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('select id, title from moz_bookmarks where fk is null')
        bookmark_id_title = cur.fetchall()
        bookmark_id_title = dict(bookmark_id_title)
    except:
        print("[Web/Firefox] Bookmarks " + "\033[31m" + "id title dict query error" + "\033[0m")
        bookmark_id_title = {}

    try:
        cur.execute('select id, parent from moz_bookmarks where fk is null')
        bookmark_id_parent = cur.fetchall()
        bookmark_id_parent = dict(bookmark_id_parent)
    except:
        print("[Web/Firefox] Bookmarks " + "\033[31m" + "id parent dict query error" + "\033[0m")
        bookmark_id_parent = {}

    try:
        cur.execute('select id, url from moz_places')
        id_url = cur.fetchall()
        id_url_dict = dict(id_url)
    except:
        print("[Web/Firefox] Bookmarks " + "\033[31m" + "id url dict query error" + "\033[0m")
        id_url_dict = {}

    try:
        cur.execute('select id, parent, title from moz_bookmarks where fk is null')
        bookmark_path = cur.fetchall()
    except:
        print("[Web/Firefox] Bookmarks " + "\033[31m" + "bookmark path query error" + "\033[0m")
        bookmark_path = []

    bookmark_dir_tree = []
    for row in bookmark_path:

        id = row[0]
        parent = row[1]

        if parent == 0:
            path = "root/"
        else:
            path = _bookmark_dir_tree(row, bookmark_id_title, bookmark_id_parent)

        outputformat = [id, path]

        bookmark_dir_tree.append(outputformat)

    id_path_dict = dict(bookmark_dir_tree)

    try:
        cur.execute('select id, type, fk, parent, title, dateAdded, lastModified, syncStatus, syncChangeCounter '
                    'from moz_bookmarks')
        bookmarks = cur.fetchall()
    except:
        # print("[Web/Firefox] Bookmarks " + "\033[31m" + "Main Query Error" + "\033[0m")
        bookmarks = []

    result = []
    for row in bookmarks:

        if row[1] == 1:
            type = 'record'
        else:
            type = 'directory'

        if row[2] == None:
            url = ''
        else:
            url = id_url_dict[row[2]]

        title = row[4]

        if row[3] == 0:
            bookmark_path = 'root/'
        else:
            bookmark_path = id_path_dict[row[3]]

        added_time = _convert_unixtimestamp(row[5])
        last_modified_time = _convert_unixtimestamp(row[6])
        sync_status = row[7]
        sync_change_count = row[8]

        if type(url) == str and ("\'" or "\"") in url:
            url = url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        if type(title) == str and ("\'" or "\"") in title:
            title = title.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        outputformat = [type, url, title, bookmark_path, added_time, last_modified_time, sync_status, sync_change_count]
        result.append(outputformat)

    conn.close()

    return result

