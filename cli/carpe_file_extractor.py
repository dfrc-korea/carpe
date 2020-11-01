#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import pytsk3

BUFF_SIZE = 1024 * 1024


class CarpeFileExtractor(object):
    """docstring for Carpe_FS_Alloc_Info"""

    def __init__(self):
        super(CarpeFileExtractor, self).__init__()
        self._output_path = None
        self._img_full_path = None
        self._file_path = None

    def set_config(self, output_path, img_path, file_path):
        self._output_path = output_path
        self._img_full_path = img_path
        self._file_path = file_path

    def extract(self):
        if len(self._file_path) == 0:
            print("no input!")
        else:
            self.extract_a_file(self._img_full_path, self._file_path)

    def extract_a_file(self, img_path, file_name):
        # Now open and read the file specified

        # Step 1: get an IMG_INFO object (url can be any URL that AFF4 can handle)
        img = pytsk3.Img_Info(img_path)

        # Step 2: Open the filesystem
        fs = pytsk3.FS_Info(img)

        # Step 3: Open the file using the inode
        f = fs.open(file_name)

        # Step 4: Read all the data and print to stdout
        offset = 0

        entry_info = []
        for i in f:
            if i.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA:
                if i.info.name is None:
                    entry_info.append([file_name, i.info.size])
        for entry in entry_info:
            file_2 = open(self._output_path + entry[0], "wb")
            while offset < entry[1]:
                available_to_read = min(BUFF_SIZE, entry[1] - offset)
                data = f.read_random(offset, available_to_read, 1)
                if not data:
                    break
                offset += len(data)
                file_2.write(data)
            file_2.close()


def main():
    file_extractor = CarpeFileExtractor()
    file_extractor.set_config(img_path=sys.argv[0], output_path=sys.argv[1], file_path=sys.argv[2])
    file_extractor.extract()


if __name__ == '__main__':
    if not main():
        sys.exit(1)
    else:
        sys.exit(0)
