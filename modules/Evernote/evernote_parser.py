from modules.Evernote.parse_user import parse_user
from modules.Evernote.parse_notes import parse_notes
from modules.Evernote.parse_workchats import parse_workchats
import sqlite3


def main(exb_path):
    with sqlite3.connect(exb_path) as connection:
        user_dict = parse_user(connection)
        notes = parse_notes(connection)
        workchats = parse_workchats(connection)
        return {"user": user_dict, "notes": notes, "workchats": workchats}
