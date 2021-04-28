import sqlite3
import datetime
import json


def _convert_strdate_to_datetime(strdate):
    month_dic = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}

    day = strdate[5:7]
    month = month_dic[strdate[8:11]]
    year = strdate[12:16]
    timestamp = strdate[17:25]

    time = year + '-' + month + '-' + day + 'T' + timestamp + 'Z'
    return time


def _count_microseconds(microseconds):
    time = datetime.timedelta(microseconds=microseconds)
    return str(time)


def _list_dict_to_list(_dict):
    return [[key] + val for dic in [_dict] for key, val in dic.items()]


def _convert_timestamp(timestamp):

    if timestamp == 0:
        time = ''
        return time
    elif len(str(timestamp)) <= 17:
        time = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=timestamp)
        time = str(time).replace(' ', 'T') + 'Z'
        return time
    else:
        time = timestamp
        return time


def _convert_unixtimestamp(timestamp):
    time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%f')+'Z'
    return time


def _bookmark_dir_tree(row, path, bookmark_result):

    if row['type'] == 'folder':
        path = path + '/' + row['name']

        for row in row['children']:
            _bookmark_dir_tree(row, path, bookmark_result)

    elif row['type'] == 'url':
        try:
            date_added = ''
            guid = ''
            id = ''
            last_visited_desktop = ''
            name = ''
            type = ''
            url = ''

            bookmark_columns = list(row.keys())
            for column in bookmark_columns:

                if column == 'date_added':
                    date_added = _convert_timestamp(int(row['date_added']))

                if column == 'guid':
                    guid = row['guid']

                if column == 'id':
                    id = row['id']

                if column == 'meta_info':
                    last_visited_desktop = _convert_timestamp(int(row['meta_info']['last_visited_desktop']))

                if column == 'name':
                    name = row['name']

                if column == 'type':
                    type = row['type']

                if column == 'url':
                    url = row['url']

            bookmark = [date_added, guid, id, last_visited_desktop, name, type, url, path]
            bookmark_result.append(bookmark)

        except KeyError:
            print('KeyError')


def whale_bookmarks(file):

    with open(file, 'r', encoding='UTF-8') as f:
        json_data = json.load(f)

        bookmark_result = []
        bookmarks_dir_list = list(json_data["roots"].keys())

        for dir in bookmarks_dir_list:

            path = '/roots'

            for row in json_data["roots"][dir]['children']:

                path = '/roots' + '/' + dir

                _bookmark_dir_tree(row, path, bookmark_result)

    return bookmark_result

def whale_download(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute(
            'select target_path, start_time, received_bytes, total_bytes, state, interrupt_reason, end_time, opened, '
            'last_access_time, referrer, site_url, tab_url, tab_referrer_url, last_modified, mime_type, '
            'original_mime_type from downloads order by start_time asc')
        result = cur.fetchall()
    except:
        # print("[Web/Whale] Downloads " + "\033[31m" + "Main Query Error" + "\033[0m")
        result = []

    download_list = []
    for row in result:
        filename_index = row[0].rfind("\\")

        file_name = row[0][filename_index + 1:]
        download_path = row[0][:filename_index].replace('\\', '/')
        received_bytes = row[2]
        total_bytes = row[3]
        state = row[4]
        interrupt_reason = row[5]
        opened = row[7]
        start_time = _convert_timestamp(row[1])
        end_time = _convert_timestamp(row[6])
        file_last_access_time = _convert_timestamp(row[8])

        if row[13] != '':
            file_last_modified_time = _convert_strdate_to_datetime(row[13])
        else:
            file_last_modified_time = row[13]

        download_tab_url = row[11]
        if type(download_tab_url) == str and ("\'" or "\"") in download_tab_url:
            download_tab_url = download_tab_url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        download_tab_refer_url = row[12]
        if type(download_tab_refer_url) == str and ("\'" or "\"") in download_tab_refer_url:
            download_tab_refer_url = download_tab_refer_url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        site_url = row[10]
        if type(site_url) == str and ("\'" or "\"") in site_url:
            site_url = site_url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        refer_url = row[9]
        if type(refer_url) == str and ("\'" or "\"") in refer_url:
            refer_url = refer_url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        mime_type = row[14]
        original_mime_type = row[15]

        outputformat = [file_name, download_path, received_bytes, total_bytes, state, interrupt_reason, opened,
                        start_time, end_time, file_last_access_time, file_last_modified_time, download_tab_url,
                        download_tab_refer_url, site_url, refer_url, mime_type, original_mime_type]

        download_list.append(outputformat)

    conn.close()

    return download_list


def whale_visit_urls(file):

    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('select id, url, title, visit_count, typed_count, last_visit_time from urls')
        result = cur.fetchall()
    except:
        # print("[Web/Whale] Visit Urls " + "\033[31m" + "Main Query Error" + "\033[0m")
        result = []

    url_list = []

    for row in result:

        if type(row[1]) == str and ("\'" or "\"") in row[1]:
            url = row[1].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            url = row[1]

        if type(row[2]) == str and ("\'" or "\"") in row[2]:
            title = row[2].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            title = row[2]

        url_list.append([row[0], url, title, row[3], row[4], _convert_timestamp(row[5])])

    conn.close()

    return url_list


def whale_visit_history(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('select id, url from urls')
        id_url = cur.fetchall()
        id_url_dict = dict(id_url)
    except:
        print("[Web/Whale] Visit History " + "\033[31m" + "id-url dict query error" + "\033[0m")
        id_url_dict = {}

    try:
        cur.execute('select id, title from urls')
        id_title = cur.fetchall()
        id_title_dict = dict(id_title)
    except:
        print("[Web/Whale] Visit History " + "\033[31m" + "id-title dict query error" + "\033[0m")
        id_title_dict = {}

    try:
        cur.execute('select id, url from visits')
        id_url_visits = cur.fetchall()
    except:
        print("[Web/Whale] Visit History " + "\033[31m" + "id-url-from-visits query error" + "\033[0m")
        id_url_visits = []

    id_url_match = []
    for row in id_url_visits:
        visits_id = row[0]
        url = id_url_dict[row[1]]

        output = [visits_id, url]
        id_url_match.append(output)
    id_url_visits_dict = dict(id_url_match)

    try:
        cur.execute('select id, name from segments')
        id_name_seg = cur.fetchall()
        id_name_seg_dict = dict(id_name_seg)
    except:
        print("[Web/Whale] Visit History " + "\033[31m" + "id-name-seg query error" + "\033[0m")
        id_name_seg_dict = {}


    transition_mask = 255 #0xFF
    transition_dict = {'0':'LINK', '1':'TYPED', '2':'AUTO_BOOKMARK', '3':'AUTO_SUBFRAME', '4':'MANUAL_SUBFRAME',
                       '5':'GENERATED', '6':'START_PAGE', '7':'FORM_SUBMIT', '8':'RELOAD', '9':'KEYWORD',
                       '10':'KEYWORD_GENERATED'}

    qualifiers_mask = 4294967040 #0xFFFFFF00
    qualifiers_first_dict = {'1':'CHAIN_START', '2':'CHAIN_END', '4':'CLIENT_REDIRECT',
                             '8':'SERVER_REDIRECT', 'c':'IS_REDIRECT_MASK',
                             '6':'CHAIN_END, CLIENT_REDIRECT', 'a':'CHAIN_END, SERVER_REDIRECT',
                             '3':'CHAIN_START, CHAIN_END'}
    qualifiers_second_dict = {'1':'FORWARD_BACK', '2':'FROM_ADDRESS_BAR', '3':'FORWARD_BACK, FROM_ADDRESS_BAR',
                              '4':'HOME_PAGE'}

    try:
        cur.execute('select url, visit_time, from_visit, transition, segment_id, visit_duration '
                    'from visits order by id asc')
        result = cur.fetchall()
    except:
        # print("[Web/Whale] Visit History " + "\033[31m" + "Main Query Error" + "\033[0m")
        result = []

    visit_history = []
    for row in result:

        try:
            from_url = id_url_visits_dict[row[2]]
        except:
            from_url = ''

        if type(from_url) == str and ("\'" or "\"") in from_url:
            from_url = from_url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        try:
            url = id_url_dict[row[0]]
        except:
            url = ''

        if type(url) == str and ("\'" or "\"") in url:
            url = url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        try:
            segment_url = id_name_seg_dict[row[4]]
        except:
            segment_url = ''

        if type(segment_url) == str and ("\'" or "\"") in segment_url:
            segment_url = segment_url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        title = id_title_dict[row[0]]
        if type(title) == str and ("\'" or "\"") in title:
            title = title.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass
        visit_time = _convert_timestamp(row[1])
        visit_duration = _count_microseconds(row[5])

        try:
            transition_decimal = row[3]
            transition = "{0:x}".format(transition_decimal & transition_mask)
            transition = transition_dict[transition]
        except:
            transition_decimal = row[3]
            unknown_transition = "{0:x}".format(transition_decimal & transition_mask)
            transition = 'Unknown : %s' %unknown_transition

        try:
            transition_decimal = row[3]
            qualifiers = "{0:x}".format(transition_decimal & qualifiers_mask)
            qualifiers_first = qualifiers_first_dict[qualifiers[0]]

            if qualifiers[1] != '0':
                qualifiers_second = qualifiers_second_dict[qualifiers[1]]
                qualifiers = qualifiers_first + ', ' + qualifiers_second
            else:
                qualifiers = qualifiers_first

        except:
            transition_decimal = row[3]
            unknown_qualifiers = "{0:x}".format(transition_decimal & qualifiers_mask)
            qualifiers = 'Unknown : %s' % unknown_qualifiers

        outputformat = [from_url, url, segment_url, title, visit_time, visit_duration, transition, qualifiers]
        visit_history.append(outputformat)

    conn.close()

    return visit_history


def whale_search_terms(file):

    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    keyword_dict, url_dict = {}, {}

    try:
        cur.execute('select id, url, last_visit_time from urls')
        result = cur.fetchall()
    except:
        print("[Web/Whale] Search Terms " + "\033[31m" + "url_dict query error" + "\033[0m")
        result = []

    for row in result:
        if type(row[1]) == str and ("\'" or "\"") in row[1]:
            url = row[1].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            url = row[1]

        url_dict[row[0]] = [url, _convert_timestamp(row[2])]

    try:
        cur.execute('select url_id, term, normalized_term from keyword_search_terms')
        result = cur.fetchall()
    except:
        print("[Web/Whale] Search Terms " + "\033[31m" + "keyword_dict query error" + "\033[0m")
        result = []

    for row in result:
        if type(row[1]) == str and ("\'" or "\"") in row[1]:
            term = row[1].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            term = row[1]

        if type(row[2]) == str and ("\'" or "\"") in row[2]:
            norm_term = row[2].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            norm_term = row[2]

        keyword_dict[row[0]] = [term, norm_term]
        keyword_dict[row[0]].extend(url_dict[row[0]])

    search_terms = _list_dict_to_list(keyword_dict)

    conn.close()

    return search_terms

def whale_cookies(file):

    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('select host_key, name, path, value, encrypted_value, '
                'creation_utc, expires_utc, last_access_utc from cookies')
        result = cur.fetchall()
    except:
        # print("[Web/Whale] Cookies " + "\033[31m" + "Main Query Error" + "\033[0m")
        result = []

    cookies_list = []
    for row in result:
        cookies_list.append([row[0], row[1], row[2], row[3], row[4], _convert_timestamp(row[5]),
                                   _convert_timestamp(row[6]), _convert_timestamp(row[7])])
    conn.close()

    return cookies_list


def whale_top_sites(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    # url, url_rank, title
    try:
        cur.execute('select url, title, url_rank from top_sites')
        result = cur.fetchall()
    except:
        # print("[Web/Whale] Top Sites " + "\033[31m" + "Main Query Error" + "\033[0m")
        result = []

    top_site_list = []
    for row in result:

        if type(row[0]) == str and ("\'" or "\"") in row[0]:
            url = row[0].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            url = row[0]

        if type(row[1]) == str and ("\'" or "\"") in row[1]:
            title = row[1].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            title = row[1]

        url_rank = row[2]

        outputformat = [url, title, url_rank]
        top_site_list.append(outputformat)

    conn.close()

    return top_site_list


def whale_autofill (file):

    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    # value, date_crated, date_last_used, count
    auto_fill_list = []
    try:
        cur.execute('select value, date_created, date_last_used, count from autofill')
        result = cur.fetchall()
    except:
        # print("[Web/Whale] Autofill " + "\033[31m" + "Main Query Error" + "\033[0m")
        result = []

    for row in result:
        if type(row[0]) == str and ("\'" or "\"") in row[0]:
            value = row[0].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            value = row[0]

        auto_fill_list.append([value, _convert_unixtimestamp(row[1]), _convert_unixtimestamp(row[2]), row[3]])

    conn.close()

    return auto_fill_list

def whale_logindata(file):

    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('pragma table_info(\'logins\')')
        result = cur.fetchall()
    except:
        print("[Web/Whale] Login Data " + "\033[31m" + "column check query error" + "\033[0m")
        result = []

    column_list = []
    for row in result:
        column_list.append(row[1])

    if 'date_last_used' in column_list:
        try:
            cur.execute(
                'select origin_url, action_url, username_element, username_value, password_element, password_value, '
                'signon_realm, date_created, form_data, blacklisted_by_user, scheme, password_type, times_used, '
                'date_synced, display_name, icon_url, federation_url, skip_zero_click, generation_upload_status, '
                'possible_username_pairs, submit_element, preferred, date_last_used from logins')
            result = cur.fetchall()
        except:
            # print("[Web/Whale] Login Data " + "\033[31m" + "Main Query Error" + "\033[0m")
            result = []

    else:
        try:
            cur.execute(
                'select origin_url, action_url, username_element, username_value, password_element, password_value, '
                'signon_realm, date_created, form_data, blacklisted_by_user, scheme, password_type, times_used, '
                'date_synced, display_name, icon_url, federation_url, skip_zero_click, generation_upload_status, '
                'possible_username_pairs, submit_element, preferred from logins')
            result = cur.fetchall()
        except:
            # print("[Web/Whale] Login Data " + "\033[31m" + "Main Query Error" + "\033[0m")
            result = []

    logindatas = []

    for row in result:
        origin_url = row[0]
        if type(origin_url) == str and ("\'" or "\"") in origin_url:
            origin_url = origin_url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        action_url = row[1]
        if type(action_url) == str and ("\'" or "\"") in action_url:
            action_url = action_url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        username_element = row[2]
        username_value = row[3]
        password_element = row[4]
        password_value = row[5]
        signon_realm = row[6]
        date_created = _convert_timestamp(row[7])
        form_data = row[8]
        blacklisted_by_user = row[9]
        scheme = row[10]
        password_type = row[11]
        times_used = row[12]
        date_synced = _convert_timestamp(row[13])
        display_name = row[14]
        icon_url = row[15]
        if type(icon_url) == str and ("\'" or "\"") in icon_url:
            icon_url = icon_url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        federation_url = row[16]
        if type(federation_url) == str and ("\'" or "\"") in federation_url:
            federation_url = federation_url.replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            pass

        skip_zero_click = row[17]
        generation_upload_status = row[18]
        possible_username_pairs = row[19]
        submit_element = row[20]
        preferred = row[21]

        if len(row) == 23:
            date_last_used = _convert_timestamp(row[22])
        else:
            date_last_used = ''

        outputformat = [origin_url, action_url, username_element, username_value, password_element, password_value,
                        signon_realm, date_created, form_data, blacklisted_by_user, scheme, password_type, times_used,
                        date_synced, display_name, icon_url, federation_url, skip_zero_click, generation_upload_status,
                        possible_username_pairs, submit_element, preferred, date_last_used]
        logindatas.append(outputformat)

    conn.close()

    return logindatas


def whale_shortcuts(file):

    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('select text, fill_into_edit, url, contents, description, keyword, last_access_time, '
                    'number_of_hits from omni_box_shortcuts order by last_access_time asc ')
        result = cur.fetchall()
    except:
        # print("[Web/Whale] Shortcuts " + "\033[31m" + "Main Query Error" + "\033[0m")
        result = []

    shortcuts = []

    for row in result:

        text = row[0]
        fill_into_edit = row[1]

        if type(row[2]) == str and ("\'" or "\"") in row[2]:
            url = row[2].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            url = row[2]

        contents = row[3]

        if type(row[4]) == str and ("\'" or "\"") in row[4]:
            description = row[4].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            description = row[4]

        keyword = row[5]
        last_access_time = _convert_timestamp(row[6])
        number_of_hits = row[7]

        outputformat = [text, fill_into_edit, url, contents, description, keyword, last_access_time, number_of_hits]

        shortcuts.append(outputformat)

    conn.close()

    return shortcuts


def whale_favicons(file):

    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('select favicon_bitmaps.id, favicon_bitmaps.icon_id, favicons.url, favicon_bitmaps.last_updated, '
                    'favicon_bitmaps.last_requested, favicon_bitmaps.image_data, favicon_bitmaps.width, '
                    'favicon_bitmaps.height from favicons, favicon_bitmaps where favicons.id = favicon_bitmaps.icon_id '
                    'order by favicon_bitmaps.id asc')
        result = cur.fetchall()
    except:
        # print("[Web/Whale] Favicons " + "\033[31m" + "Main Query Error" + "\033[0m")
        result = []

    favicons = []
    for row in result:

        id = row[0]
        icon_id = row[1]

        if type(row[2]) == str and ("\'" or "\"") in row[2]:
            icon_url = row[2].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            icon_url = row[2]

        last_updated = _convert_timestamp(row[3])
        last_requested = _convert_timestamp(row[4])
        image_data = row[5]
        width = row[6]
        height = row[7]

        outputformat = [id, icon_id, icon_url, last_updated, last_requested, image_data, width, height]

        favicons.append(outputformat)

    conn.close()

    return favicons