import sqlite3
import struct
from modules.Evernote.util import covnert_to_iso, _strip


def parse_workchats(connection: sqlite3.Connection):
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT thread_uid, sender_id, body, sent_date
        FROM message_attr
    """
    )

    keys = ["thread_uid", "sender_id", "body", "sent_time"]

    workchat_dicts = [
        dict(
            {"sender_name": None},
            **{keys[index]: data for index, data in enumerate(row)},
        )
        for row in cursor.fetchall()
    ]

    for workchat_dict in workchat_dicts:
        UNIX_timestamp = covnert_to_iso(workchat_dict["sent_time"])
        if UNIX_timestamp is not None:
            workchat_dict["sent_time"] = UNIX_timestamp
        sender_id = workchat_dict["sender_id"]

        workchat_dict["sender_name"] = None
        if sender_id is not None:
            cursor.execute(
                f"""
                    SELECT contact_name
                    FROM identity_attr
                    WHERE user_id = {sender_id}
                """
            )
            sender_name = cursor.fetchone()[0]
            workchat_dict["sender_name"] = sender_name

    thread_uids = list(
        set([workchat_dict["thread_uid"] for workchat_dict in workchat_dicts])
    )

    cursor.execute(
        f"""
        SELECT uid, data
        FROM attrs
        WHERE uid IN ({','.join(['?']*len(thread_uids))})
        AND aid = 324
    """,
        thread_uids,
    )

    thread_uid_participant_tuples = cursor.fetchall()

    def get_participants(blob: bytes, cursor: sqlite3.Cursor):
        blobs_by_four_bytes = [blob[i : i + 4] for i in range(0, len(blob), 4)]
        # print(blobs_by_four_bytes)
        participant_uids = [
            struct.unpack("<i", participant)[0] for participant in blobs_by_four_bytes
        ]

        cursor.execute(
            f"""
                SELECT contact_name, contact_id
                FROM identity_attr
                WHERE uid in ({','.join(['?']*len(participant_uids))})
            """,
            participant_uids,
        )

        participant_names_and_ids = list(cursor.fetchall())

        return {
            "names": [_strip(name) for name, _ in participant_names_and_ids],
            "ids": [_strip(id) for _, id in participant_names_and_ids],
        }

    thread_uid_participant_dict = {
        thread_uid: get_participants(participants_blob, cursor)
        for thread_uid, participants_blob in thread_uid_participant_tuples
    }
    for workchat_dict in workchat_dicts:
        participants_dict = thread_uid_participant_dict[workchat_dict["thread_uid"]]
        workchat_dict["participants"] = participants_dict["names"]
        workchat_dict["participant_ids"] = participants_dict["ids"]
        workchat_dict.pop("thread_uid", None)
    return workchat_dicts