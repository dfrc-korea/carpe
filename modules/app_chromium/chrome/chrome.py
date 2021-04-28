import sqlite3
import datetime
import json


def _count_microseconds(microseconds):
    time = datetime.timedelta(microseconds=microseconds)
    return str(time)


def _convert_timestamp(timestamp):
    if timestamp == 0:
        time = ''
        return time
    elif len(str(timestamp)) <= 18:
        try:
            time = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=timestamp)
            time = str(time).replace(' ', 'T') + 'Z'
            return time
        except OverflowError as e:
            print(f'Convert Time Error : {str(e)}')
            return ''
    else:
        time = timestamp
        return time


def _convert_unixtimestamp(timestamp):
    time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
    return time


def _convert_strdate_to_datetime(strdate):
    # day_of_week = strdate[0:3]
    month_dic = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}

    day = strdate[5:7]
    try:
        month = month_dic[strdate[8:11]]
    except KeyError:
        return '0'
    year = strdate[12:16]
    timestamp = strdate[17:25]

    time = year + '-' + month + '-' + day + 'T' + timestamp + 'Z'
    return time


def _bookmark_dir_tree(row, path, bookmark_result):
    if row['type'] == 'folder':
        path = path + '/' + row['name']

        for row in row['children']:
            _bookmark_dir_tree(row, path, bookmark_result)

    if row['type'] == 'url':
        try:
            date_added = ''
            guid = ''
            id = ''
            last_visited_desktop = ''
            name = ''
            bookmark_type = ''
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
                    if type(row['name']) == str and ("\'" or "\"") in row['name']:
                        name = row['name'].replace("\'", "\'\'").replace('\"', '\"\"')
                    else:
                        name = row['name']

                if column == 'type':
                    bookmark_type = row['type']

                if column == 'url':
                    url = row['url']

            bookmark = [date_added, guid, id, last_visited_desktop, name, bookmark_type, url, path]
            bookmark_result.append(bookmark)

        except KeyError:
            print('KeyError')


def chrome_search_terms(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute(
            'select urls.last_visit_time, urls.url, keyword_search_terms.term '
            'from keyword_search_terms, urls where keyword_search_terms.url_id = urls.id order by last_visit_time asc')
        result = cur.fetchall()
    except:
        #print("[Web/Chrome] Search Terms " + "\033[31m" + "Main Query Error" + "\033[0m")
        result = []

    search_terms = []

    for row in result:

        date = _convert_timestamp(row[0])

        if type(row[1]) == str and ("\'" or "\"") in row[1]:
            url = row[1].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            url = row[1]

        if type(row[2]) == str and ("\'" or "\"") in row[2]:
            search_word = row[2].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            search_word = row[2]

        google_search = "://www.google.co"
        naver_search = "://search.naver.com/"
        daum_search = "://search.daum.net/"
        youtube_search = "://www.youtube.com/"

        if google_search in url:
            search_site = "Google"
        elif naver_search in url:
            search_site = "Naver"
        elif daum_search in url:
            search_site = "Daum"
        elif youtube_search in url:
            search_site = "Youtube"
        else:
            search_site = "others"

        outputformat = [url, search_word, date, search_site]

        search_terms.append(outputformat)

    conn.close()

    return search_terms


def chrome_visit_urls(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute(
            'select urls.url, urls.last_visit_time, urls.title, urls.visit_count, urls.typed_count '
            'from urls order by last_visit_time asc')
        result = cur.fetchall()
    except:
        # print("[Web/Chrome] Visit Urls " + "\033[31m" + "Main Query Error" + "\033[0m")
        result = []

    visit_urls = []

    for row in result:

        if type(row[0]) == str and ("\'" or "\"") in row[0]:
            url = row[0].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            url = row[0]

        last_visited_time = _convert_timestamp(row[1])

        if type(row[2]) == str and ("\'" or "\"") in row[2]:
            title = row[2].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            title = row[2]

        visit_count = row[3]
        typed_count = row[4]

        outputformat = [url, last_visited_time, title, visit_count, typed_count]

        visit_urls.append(outputformat)

    conn.close()

    return visit_urls


def chrome_visit_history(file):
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
        print("[Web/Chrome] Visit History " + "\033[31m" + "id-url dict query error" + "\033[0m")
        id_url_dict = {}

    try:
        cur.execute('select id, title from urls')
        id_title = cur.fetchall()
        id_title_dict = dict(id_title)
    except:
        print("[Web/Chrome] Visit History " + "\033[31m" + "id-title dict query error" + "\033[0m")
        id_title_dict = {}

    try:
        cur.execute('select id, url from visits')
        id_url_visits = cur.fetchall()
    except:
        print("[Web/Chrome] Visit History " + "\033[31m" + "id-url-from-visits query error" + "\033[0m")
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
        print("[Web/Chrome] Visit History " + "\033[31m" + "id-name-seg query error" + "\033[0m")
        id_name_seg_dict = {}

    transition_mask = 255  # 0xFF
    transition_dict = {'0': 'LINK', '1': 'TYPED', '2': 'AUTO_BOOKMARK', '3': 'AUTO_SUBFRAME', '4': 'MANUAL_SUBFRAME',
                       '5': 'GENERATED', '6': 'START_PAGE', '7': 'FORM_SUBMIT', '8': 'RELOAD', '9': 'KEYWORD',
                       '10': 'KEYWORD_GENERATED'}

    qualifiers_mask = 4294967040  # 0x
    qualifiers_first_dict = {'1': 'CHAIN_START', '2': 'CHAIN_END', '4': 'CLIENT_REDIRECT',
                             '8': 'SERVER_REDIRECT', 'c': 'IS_REDIRECT_MASK',
                             '6': 'CHAIN_END, CLIENT_REDIRECT', 'a': 'CHAIN_END, SERVER_REDIRECT',
                             '3': 'CHAIN_START, CHAIN_END'}
    qualifiers_second_dict = {'1': 'FORWARD_BACK', '2': 'FROM_ADDRESS_BAR', '3': 'FORWARD_BACK, FROM_ADDRESS_BAR',
                              '4': 'HOME_PAGE'}
    try:
        cur.execute(
            'select url, visit_time, from_visit, transition, segment_id, visit_duration from visits order by id asc')
        result = cur.fetchall()
    except:
        # print("[Web/Chrome] Visit History " + "\033[31m" + "Main Query Error" + "\033[0m")
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

        try:
            title = id_title_dict[row[0]]
        except:
            title = ''

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
            transition = 'Unknown : %s' % unknown_transition

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


def chrome_download(file):
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
        # print("[Web/Chrome] Downloads " + "\033[31m" + "Main Query Error" + "\033[0m")
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


def chrome_top_sites(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    cur.execute('SELECT name FROM sqlite_master WHERE type=\'table\';')
    table_list = cur.fetchall()

    if ('top_sites',) in table_list:
        try:
            cur.execute('select url, title, url_rank from top_sites order by url_rank asc ')
            result = cur.fetchall()
        except:
            # print("[Web/Chrome] Top Sites " + "\033[31m" + "Main Query Error" + "\033[0m")
            result = []
    elif ('thumbnails',) in table_list:
        try:
            cur.execute('select url, title, url_rank from thumbnails order by url_rank asc ')
            result = cur.fetchall()
        except:
            # print("[Web/Chrome] Top Sites " + "\033[31m" + "Main Query Error" + "\033[0m")
            result = []
    else:
        print("[Web/Chrome] Top Sites " + "\033[31m" + "Main Query Table Name Error" + "\033[0m")
        result = []

    top_sites = []

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

        top_sites.append(outputformat)

    conn.close()

    return top_sites


def chrome_shortcuts(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute(
            'select text, fill_into_edit, url, contents, description, keyword, last_access_time, number_of_hits '
            'from omni_box_shortcuts order by last_access_time asc ')
        result = cur.fetchall()
    except:
        # print("[Web/Chrome] Shortcuts " + "\033[31m" + "Main Query Error" + "\033[0m")
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


def chrome_favicons(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('select favicon_bitmaps.id, favicon_bitmaps.icon_id, favicons.url, favicon_bitmaps.last_updated, '
                    'favicon_bitmaps.last_requested, favicon_bitmaps.image_data, favicon_bitmaps.width, '
                    'favicon_bitmaps.height from favicons, favicon_bitmaps where favicons.id = favicon_bitmaps.icon_id'
                    ' order by favicon_bitmaps.id asc')
        result = cur.fetchall()
    except:
        # print("[Web/Chrome] Favicons " + "\033[31m" + "Main Query Error" + "\033[0m")
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


def chrome_cookies(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('pragma table_info(\'cookies\')')
        result = cur.fetchall()
    except:
        print("[Web/Chrome] Cookies " + "\033[31m" + "column check query error" + "\033[0m")
        result = []

    column_list = []
    for row in result:
        column_list.append(row[1])

    if 'samestie' in column_list:
        try:
            cur.execute(
                'select creation_utc, host_key, name, path, expires_utc, is_secure, is_httponly, last_access_utc, '
                'has_expires, is_persistent, priority, encrypted_value, samesite from cookies order by creation_utc asc')
            result = cur.fetchall()
        except:
            # print("[Web/Chrome] Cookies " + "\033[31m" + "Main Query Error" + "\033[0m")
            result = []
    else:
        try:
            cur.execute(
                'select creation_utc, host_key, name, path, expires_utc, is_secure, is_httponly, last_access_utc, '
                'has_expires, is_persistent, priority, encrypted_value from cookies order by creation_utc asc')
            result = cur.fetchall()
        except:
            # print("[Web/Chrome] Cookies " + "\033[31m" + "Main Query Error" + "\033[0m")
            result = []

    cookies = []

    for row in result:

        creation_utc = _convert_timestamp(row[0])
        host_key = row[1]
        name = row[2]
        path = row[3]
        expires_utc = _convert_timestamp(row[4])
        is_secure = row[5]
        is_httponly = row[6]
        last_access_utc = _convert_timestamp(row[7])
        has_expires = row[8]
        is_persistent = row[9]
        priority = row[10]
        encrypted_value = row[11]

        if len(row) == 13:
            samesite = row[12]
        else:
            samesite = ''

        outputformat = [creation_utc, host_key, name, path, expires_utc, is_secure, is_httponly, last_access_utc,
                        has_expires, is_persistent, priority, encrypted_value, samesite]

        cookies.append(outputformat)

    conn.close()

    return cookies


def chrome_autofill(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute(
            'select name, value, value_lower, date_created, date_last_used, count from autofill order by rowid asc')
        result = cur.fetchall()
    except:
        # print("[Web/Chrome] Autofill " + "\033[31m" + "Main Query Error" + "\033[0m")
        result = []

    autofill = []

    for row in result:

        name = row[0]

        if type(row[1]) == str and ("\'" or "\"") in row[1]:
            value = row[1].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            value = row[1]

        if type(row[2]) == str and ("\'" or "\"") in row[2]:
            value_lower = row[2].replace("\'", "\'\'").replace('\"', '\"\"')
        else:
            value_lower = row[2]

        date_created = _convert_unixtimestamp(row[3])
        date_last_used = _convert_unixtimestamp(row[4])
        count = row[5]

        outputformat = [name, value, value_lower, date_created, date_last_used, count]

        autofill.append(outputformat)

    conn.close()

    return autofill


def chrome_logindata(file):
    if isinstance(file, str):
        conn = sqlite3.connect(file)
    else:
        conn = sqlite3.connect(file.read())
    cur = conn.cursor()

    try:
        cur.execute('pragma table_info(\'logins\')')
        result = cur.fetchall()
    except:
        print("[Web/Chrome] Login Data " + "\033[31m" + "column check query error" + "\033[0m")
        result = []

    column_list = []
    for row in result:
        column_list.append(row[1])

    query = 'select origin_url, action_url, username_element, username_value, password_element, password_value, ' \
            'signon_realm, date_created, form_data, blacklisted_by_user, scheme, password_type, times_used, ' \
            'date_synced, display_name, icon_url, federation_url, skip_zero_click, generation_upload_status, ' \
            'possible_username_pairs, submit_element'

    if 'date_last_used' and 'preferred' in column_list:
        query += ', preferred, date_last_used'
    elif 'preferred' not in column_list:
        query += ', date_last_used'
    else:
        query += ', preferred'

    query += ' from logins'

    try:
        cur.execute(query)
        result = cur.fetchall()
    except:
        # print("[Web/Chrome] Login Data " + "\033[31m" + "Main Query Error" + "\033[0m")
        result = []

    login_datas = []

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

        if len(row) == 22:
            if row[21] < 10000000000000000:             # row[21]이 preferred일 경우
                preferred = row[21]
                date_last_used = ''
            else:                                       # row[21]이 date_last_used일 경우
                preferred = ''
                date_last_used = _convert_timestamp(row[21])
        elif len(row) == 23:
            preferred = row[21]
            date_last_used = _convert_timestamp(row[22])
        else:
            preferred = ''
            date_last_used = ''

        output_format = [origin_url, action_url, username_element, username_value, password_element, password_value,
                         signon_realm, date_created, form_data, blacklisted_by_user, scheme, password_type, times_used,
                         date_synced, display_name, icon_url, federation_url, skip_zero_click, generation_upload_status,
                         possible_username_pairs, submit_element, preferred, date_last_used]

        login_datas.append(output_format)

    conn.close()

    return login_datas


def chrome_bookmarks(file):
    with open(file, 'r', encoding='UTF-8') as f:
        json_data = json.load(f)

        bookmark_result = []
        bookmarks_dir_list = list(json_data["roots"].keys())

        for dir in bookmarks_dir_list:

            if type(json_data["roots"][dir]) == dict:

                if "children" in json_data["roots"][dir].keys():

                    for row in json_data["roots"][dir]['children']:
                        path = '/roots' + '/' + dir

                        _bookmark_dir_tree(row, path, bookmark_result)
                else:
                    pass
            else:
                pass

    return bookmark_result


def chrome_domain_analysis(file):
    with open(file, 'r', encoding='UTF-8') as f:
        try:
            json_data = json.load(f)
        except ValueError:
            return []
        preferences_list = list(json_data.keys())

        domain_result = []

        if 'profile' in preferences_list:

            try:  # todo : temporary fix 201021
                urls = json_data['profile']['content_settings']['exceptions']['site_engagement']

                for url in urls:

                    domain = url
                    urls[url].keys()

                    if 'expiration' in urls[url].keys():
                        expiration = urls[url]['expiration']
                    else:
                        expiration = ''

                    if 'last_modified' in urls[url].keys():
                        last_modified = _convert_timestamp(int(urls[url]['last_modified']))
                    else:
                        last_modified = ''

                    if 'model' in urls[url].keys():
                        model = urls[url]['model']
                    else:
                        model = ''

                    last_engagement_time = _convert_timestamp(int(urls[url]['setting']['lastEngagementTime']))
                    last_shortcut_launch_time = _convert_timestamp(int(urls[url]['setting']['lastShortcutLaunchTime']))
                    points_added = urls[url]['setting']['pointsAddedToday']
                    raw_score = urls[url]['setting']['rawScore']

                    output_format = [domain, expiration, last_modified, model, last_engagement_time,
                                     last_shortcut_launch_time, points_added, raw_score]
                    domain_result.append(output_format)

            except:
                domain_result = []

    return domain_result


def chrome_google_account(file):
    with open(file, 'r', encoding='UTF-8') as f:
        json_data = json.load(f)
        preferences_list = list(json_data.keys())

        account_list = []
        if 'account_info' in preferences_list:
            accounts = json_data['account_info']

            if len(accounts) == 0:
                return account_list

            else:
                for row in accounts:

                    if 'account_id' in row.keys():
                        account_id = row['account_id']
                    else:
                        account_id = ''
                    if 'email' in row.keys():
                        email = row['email']
                    else:
                        email = ''
                    if 'full_name' in row.keys():
                        full_name = row['full_name']
                    else:
                        full_name = ''
                    if 'given_name' in row.keys():
                        first_name = row['given_name']
                    else:
                        first_name = ''
                    if 'locale' in row.keys():
                        locale = row['locale']
                    else:
                        locale = ''
                    if 'hd' in row.keys():
                        host_domain = row['hd']
                    else:
                        host_domain = ''
                    if 'is_child_account' in row.keys():
                        is_child_account = row['is_child_account']
                    else:
                        is_child_account = ''
                    if 'is_under_advanced_protection' in row.keys():
                        is_under_advanced_protection = row['is_under_advanced_protection']
                    else:
                        is_under_advanced_protection = ''
                    if 'last_download_image_url_with_size' in row.keys():
                        last_download_image_url = row['last_download_image_url_with_size']
                    else:
                        last_download_image_url = ''
                    if 'picture_url' in row.keys():
                        picture_url = row['picture_url']
                    else:
                        picture_url = ''

                    outputformat = [account_id, email, full_name, first_name, locale, host_domain, is_child_account,
                                    is_under_advanced_protection, last_download_image_url, picture_url]
                    account_list.append(outputformat)

                return account_list
        else:
            return account_list


def chrome_zoom_level(file):
    with open(file, 'r', encoding='UTF-8') as f:
        json_data = json.load(f)
        preferences_list = list(json_data.keys())

        if 'partition' in preferences_list:

            try:
                record_check = len(json_data['partition']['per_host_zoom_levels']['x'])

                if record_check == 0:
                    zoom_level_list = []
                    return zoom_level_list

                else:
                    zoom_level_record = json_data['partition']['per_host_zoom_levels']['x']
                    url_record = json_data['partition']['per_host_zoom_levels']['x'].keys()
                    zoom_level_list = []

                    for url in url_record:
                        record = zoom_level_record[url]

                        zoom_level = record['zoom_level']
                        last_modified_time = _convert_timestamp(int(record['last_modified']))

                        outputformat = [url, zoom_level, last_modified_time]
                        zoom_level_list.append(outputformat)
                    return zoom_level_list

            except:
                zoom_level_list = []
                return zoom_level_list
        else:
            zoom_level_list = []
            return zoom_level_list
