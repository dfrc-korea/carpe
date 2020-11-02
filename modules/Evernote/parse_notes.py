import sqlite3
from modules.Evernote.util import covnert_to_iso, _strip


def parse_notes(connection: sqlite3.Connection):
    cursor = connection.cursor()
    cursor.execute(
        f"""
        SELECT uid, title, author, notebook, last_editor_id, place_name, latitude, longitude, date_created, date_updated, date_deleted, reminder_time, reminder_done_time
        FROM note_attr
    """
    )

    keys = [
        "uid",
        "title",
        "author",
        "notebook_name",
        "last_editor_id",
        "place_name",
        "latitude",
        "longitude",
        "created_time",
        "updated_time",
        "deleted_time",
        "reminder_time",
        "reminder_done_time",
    ]

    def parse_note_data(index, data):
        if index > 7 and data is not None:
            return covnert_to_iso(data)
        if type(data) == str:
            return _strip(data)
        return data

    note_dicts = [
        {keys[index]: parse_note_data(index, data) for index, data in enumerate(row)}
        for row in cursor.fetchall()
    ]

    cursor.execute(
        f"""
            SELECT uid, data
            FROM attrs
            WHERE aid = 34
        """
    )

    note_contents = {
        uid: _strip(data_blob.decode("utf-8")) for uid, data_blob in cursor.fetchall()
    }

    for note_dict in note_dicts:
        note_dict.update({"content": note_contents[note_dict["uid"]]})
        note_dict.pop("uid", None)
    return note_dicts
