import os


class Drive(object):
    def parse_filesystem_info(dic_drive, file_info):
        filename = os.path.basename(file_info)
        parentpath = file_info.split('Drive' + os.sep, 1)[1].strip(filename)
        idx_ext = filename.rfind('.')

        if idx_ext >= 1:
            extension = filename[idx_ext+1:]

        modified_time = int(os.stat(file_info).st_mtime)
        size = os.path.getsize(file_info)

        dic_drive['parentpath'] = 'Drive' + os.sep + str(parentpath)
        dic_drive['filename'] = str(filename)
        dic_drive['extension'] = str(extension)
        dic_drive['modified_time'] = modified_time
        dic_drive['bytes'] = int(size)
        dic_drive['filepath'] = str(file_info)

    def parse_drive(case):
        file_path = case.takeout_drive_path

        if not os.path.exists(file_path):
            return False

        list_filepath = []
        for dirpath, dirnames, filenames in os.walk(file_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                list_filepath.append(filepath)

        result = []
        for i in range(len(list_filepath)):
            dic_drive = {'parentpath':"", 'filename':"", 'extenstion':"", 'modified_time':0, 'bytes':0, 'filepath':""}
            Drive.parse_filesystem_info(dic_drive, list_filepath[i])

            result.append((dic_drive['parentpath'], dic_drive['filename'], dic_drive['extension'], dic_drive['modified_time'], dic_drive['bytes'], dic_drive['filepath']))

        return result
