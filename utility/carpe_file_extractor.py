#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytsk3
from optparse import OptionParser
from utility import carpe_db
import sys
import pdb

BUFF_SIZE = 1024 * 1024


class Carpe_File_Extractor(object):
    """docstring for Carpe_FS_Alloc_Info"""
    def __init__(self):
        super(Carpe_File_Extractor, self).__init__()
        self._name_inode= []
        self._img_full_path = None
        self._output_path = None

    def setConfig(self, output_path, img_path, name_inode_tuplelist):
        self._output_path = output_path
        self._name_inode = name_inode_tuplelist
        self._img_full_path = img_path

    def extract(self):
        if len(self._name_inode) == 0:
                print("no input!")
        else:
            for a_tuple in self._name_inode:
                self.extract_a_file(self._img_full_path, a_tuple[0], a_tuple[1])

    def extract_a_file(self, img_path, name, inode):
        ## Now open and read the file specified
        ## Step 1: get an IMG_INFO object (url can be any URL that AFF4 can handle)
        img = pytsk3.Img_Info(img_path)
        ## Step 2: Open the filesystem
        fs = pytsk3.FS_Info(img, 1048576)
        ## Step 3: Open the file using the inode
        f = fs.open_meta(inode = inode)

        ## Step 4: Read all the data and print to stdout
        offset = 0
        size = f.info.meta.size
        
        if type(name) is None:
            file_name= str(inode)
        else:
            file_name= name

        entry_info=[]
        #print(file_name)
        for i in f:
            if (i.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA):
                #print(i.info.name)
                #print(i.info.size)
                if i.info.name is None:
                    entry_info.append([file_name, i.info.size])                
        for entry in entry_info:
            file_2 = open(self._output_path + entry[0],"wb")
            while offset < entry[1]:
                available_to_read = min(BUFF_SIZE, entry[1] - offset)
                data = f.read_random(offset, available_to_read,1)
                if not data: break
                offset += len(data)
                file_2.write(data)
            file_2.close()    


