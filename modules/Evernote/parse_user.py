import sqlite3
import re
from modules.Evernote.util import covnert_to_iso, _strip


def parse_user(connection: sqlite3.Connection):
    cursor = connection.cursor()
    # 378 is BASE_ITEM which contains user data
    cursor.execute(
        f"""
        SELECT data, aid
        FROM attrs
        WHERE uid = 378
        AND (aid = 220 OR aid = 222 OR aid = 223)
        """,
    )

    def decode_aid(aid):
        if aid == 220:
            return "full_name"
        if aid == 222:
            return "email"
        # 223 is for image url which contains user id
        return "url_for_user_id"

    user_dict = {
        decode_aid(aid): _strip(data_blob.decode("utf-8"))
        for data_blob, aid in cursor.fetchall()
    }
    if "full_name" not in user_dict:
        user_dict["full_name"] = None
    url = user_dict["url_for_user_id"]
    forecut = re.sub(r".*user\/", r"", url)
    user_id = re.sub(r"\/photo", "", forecut)

    user_dict["user_id"] = user_id

    cursor.execute(
        f"""
            SELECT date_created
            FROM user_attr
            WHERE id = {user_id}
        """,
    )

    user_dict["created_time"] = covnert_to_iso(cursor.fetchone()[0])
    user_dict.pop("url_for_user_id", None)
    return user_dict