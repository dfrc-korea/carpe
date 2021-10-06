#
# syFolderId.py, 210720
#
import re
from modules.Registry.guid import GUID


def get_folder_name(file_name):

    folder_uuid = re.sub('knownfolder:', '', file_name)
    folder_uuid = folder_uuid.replace('{', '')
    folder_uuid = folder_uuid.replace('}', '')
    folder_name = GUID.get(folder_uuid)

    return folder_name
