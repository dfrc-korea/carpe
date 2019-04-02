
#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2011, Michael Cohen <scudette@gmail.com>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import gc
import pdb
import sys, os
import time

import images
import pytsk3

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from utility import carpe_db



class Fls(object):

  FILE_TYPE_LOOKUP = {
      pytsk3.TSK_FS_NAME_TYPE_UNDEF: "-",
      pytsk3.TSK_FS_NAME_TYPE_FIFO: "p",
      pytsk3.TSK_FS_NAME_TYPE_CHR: "c",
      pytsk3.TSK_FS_NAME_TYPE_DIR: "d",
      pytsk3.TSK_FS_NAME_TYPE_BLK: "b",
      pytsk3.TSK_FS_NAME_TYPE_REG: "r",
      pytsk3.TSK_FS_NAME_TYPE_LNK: "l",
      pytsk3.TSK_FS_NAME_TYPE_SOCK: "h",
      pytsk3.TSK_FS_NAME_TYPE_SHAD: "s",
      pytsk3.TSK_FS_NAME_TYPE_WHT: "w",
      pytsk3.TSK_FS_NAME_TYPE_VIRT: "v"}

  META_TYPE_LOOKUP = {
      pytsk3.TSK_FS_META_TYPE_REG: "r",
      pytsk3.TSK_FS_META_TYPE_DIR: "d",
      pytsk3.TSK_FS_META_TYPE_FIFO: "p",
      pytsk3.TSK_FS_META_TYPE_CHR: "c",
      pytsk3.TSK_FS_META_TYPE_BLK: "b",
      pytsk3.TSK_FS_META_TYPE_LNK: "h",
      pytsk3.TSK_FS_META_TYPE_SHAD: "s",
      pytsk3.TSK_FS_META_TYPE_SOCK: "s",
      pytsk3.TSK_FS_META_TYPE_WHT: "w",
      pytsk3.TSK_FS_META_TYPE_VIRT: "v"}

  ATTRIBUTE_TYPES_TO_PRINT = [
      pytsk3.TSK_FS_ATTR_TYPE_NTFS_IDXROOT,
      pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA,
      pytsk3.TSK_FS_ATTR_TYPE_DEFAULT]

  def __init__(self):
    super(Fls, self).__init__()
    self._fs_info = None
    self._img_info = None
    self._long_listing = False
    self._recursive = False


  def list_directory(self, directory, stack=None, path=None):
    stack.append(directory.info.fs_file.meta.addr)
    
    for directory_entry in directory:
      #print directory_entry.info.meta.type
      #file/directory name
      #print directory_entry.info.name.name

      prefix = "+" * (len(stack) - 1)
      if prefix:
        prefix += " "

      # Skip ".", ".." or directory entries without a name.
      if (not hasattr(directory_entry, "info") or
          not hasattr(directory_entry.info, "name") or
          not hasattr(directory_entry.info.name, "name") or
          directory_entry.info.name.name in [".", ".."]):
        continue

      #print path
      self.print_directory_entry(directory_entry, prefix=prefix, path=path)  
      #print "[*]"
      
      if self._recursive:
        try:
          sub_directory = directory_entry.as_directory()
          inode = directory_entry.info.meta.addr

          # This ensures that we don't recurse into a directory
          # above the current level and thus avoid circular loops.
          if inode not in stack:
            path.append((directory_entry.info.name.name).decode('utf-8','replace'))
            
            self.list_directory(sub_directory, stack, path)

        except IOError:
          pass

    stack.pop(-1)
    if (len(path) > 0):
      path.pop(-1)

  def open_directory(self, inode_or_path):
    inode = None
    path = None
    if inode_or_path is None:
      path = "/"
    elif inode_or_path.startswith("/"):
      path = inode_or_path
    else:
      inode = inode_or_path

    # Note that we cannot pass inode=None to fs_info.opendir().
    if inode:
      directory = self._fs_info.open_dir(inode=inode)
    else:
      directory = self._fs_info.open_dir(path=path)

    return directory

  def open_file_system(self, offset):
    self._fs_info = pytsk3.FS_Info(self._img_info, offset=offset)

  def open_image(self, image_type, filenames):
    # List the actual files (any of these can raise for any reason).
    self._img_info = images.SelectImage(image_type, filenames)

  def parse_options(self, options):
    self._long_listing = getattr(options, "long_listing", False)
    self._recursive = getattr(options, "recursive", False)

  def print_directory_entry(self, directory_entry, prefix="", path=None):
      
      meta = directory_entry.info.meta
      name = directory_entry.info.name
      
      name_type = "-"
      if name:
        name_type = self.FILE_TYPE_LOOKUP.get(int(name.type), "-")

      meta_type = "-"
      if meta:
        meta_type = self.META_TYPE_LOOKUP.get(int(meta.type), "-")

      directory_entry_type = "{0:s}/{1:s}".format(name_type, meta_type)

      for attribute in directory_entry:
        mtime = directory_entry.info.meta.mtime
        atime = directory_entry.info.meta.atime
        ctime = directory_entry.info.meta.crtime
        inode_type = int(attribute.info.type)
        if inode_type in self.ATTRIBUTE_TYPES_TO_PRINT:
          if self._fs_info.info.ftype in [
              pytsk3.TSK_FS_TYPE_NTFS, pytsk3.TSK_FS_TYPE_NTFS_DETECT]:
            inode = "{0:d}-{1:d}-{2:d}".format(
                meta.addr, int(attribute.info.type), attribute.info.id)
          else:
            inode = "{0:d}".format(meta.addr)

          attribute_name = attribute.info.name
          if attribute_name and attribute_name not in ["$Data", "$I30"]:
            
            #filename = name.name+":"+attribute.info.name
            filename = "{0:s}:{1:s}".format((name.name).decode('utf-8','replace'), (attribute.info.name).decode('utf-8','replace'))

          else:
            filename = (name.name).decode('utf-8','replace')

          temp = str(filename)
          temp = temp.split(".")

          if (len(temp)==1 or (str(directory_entry_type) =="d/d")):
            file_extension=""
          else:
            file_extension = temp[-1]

          if meta and name:
            data="{0:s}|{1:s}|{2:s}|{3:s}|{4:s}|{5:s}|{6:s}|{7:s}".format(str(directory_entry_type), str(inode), str("root/" +"/".join(path)), str(filename), str(mtime), str(atime), str(ctime), str(file_extension))
            db_test = carpe_db.Mariadb()
            conn=db_test.open()
            query=db_test.query_builder("1", data, "file")
            data=db_test.execute_query(conn,query)
            db_test.close(conn)