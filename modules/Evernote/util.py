def covnert_to_UNIX(evernote_timestamp):
    if evernote_timestamp is None:
        return evernote_timestamp
    return evernote_timestamp * 86400 - 62135683200


def _strip(str_data):
    if str_data is None:
        return str_data
    return str_data.strip("\x00").strip("\u200d")