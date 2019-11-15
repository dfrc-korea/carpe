
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
from __future__ import print_function
import argparse
import gc
import pdb
import sys
import time

import images
import pytsk3

import carpe_file
import carpe_fs_info
import carpe_db
import carpe_fs_alloc_info


def vdir(obj):
  return [x for x in dir(obj) if not x.startswith('__')]



class Carpe_FS_Analyze(object):

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

  ATTRIBUTE_TYPES_TO_ANALYZE = [
      pytsk3.TSK_FS_ATTR_TYPE_NTFS_IDXROOT,
      pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA,
      pytsk3.TSK_FS_ATTR_TYPE_NTFS_FNAME,
      pytsk3.TSK_FS_ATTR_TYPE_NTFS_SI,
      pytsk3.TSK_FS_ATTR_TYPE_DEFAULT,
      pytsk3.TSK_FS_ATTR_TYPE_HFS_DEFAULT]
  ATTRIBUTE_TYPES_TO_ANALYZE_TIME = [
      pytsk3.TSK_FS_ATTR_TYPE_NTFS_SI,
      pytsk3.TSK_FS_ATTR_TYPE_HFS_DEFAULT
  ]
  ATTRIBUTE_TYPES_TO_ANALYZE_ADDITIONAL_TIME =[
      pytsk3.TSK_FS_ATTR_TYPE_NTFS_FNAME
      ]
  def __init__(self):
    super(Carpe_FS_Analyze, self).__init__()
    self._fs_info = None
    self._fs_info_2 = None
    self._fs_blocks = []
    self._img_info = None
    self._recursive = False
    self._carpe_files = []

  def fs_info(self,p_id=0):
    fs_info = carpe_fs_info.Carpe_FS_Info()
    fs_info._fs_id = self._fs_info.info.fs_id
    fs_info._p_id = p_id
    fs_info._block_size = self._fs_info.info.block_size
    fs_info._block_count = self._fs_info.info.block_count
    fs_info._root_inum = self._fs_info.info.root_inum
    fs_info._first_inum = self._fs_info.info.first_inum
    fs_info._last_inum = self._fs_info.info.last_inum
    self._fs_info_2 = fs_info

  def block_alloc_status(self):
    alloc_info = carpe_fs_alloc_info.Carpe_FS_Alloc_Info()
    skip = 0
    start = 0

    for n in range(0, self._fs_info_2._block_count):  
      if (skip == 0):
        if(self._fs_info.blockstat(n) == 0):
          start = n
          skip = 1
      else:
        if(self._fs_info.blockstat(n) == 1):
          alloc_info._unallock_blocks.append((start, n-1))
          skip = 0

      if(n == self._fs_info_2._block_count -1 and self._fs_info.blockstat(n) == 0):
        alloc_info._unallock_blocks.append((start, n))
    return alloc_info

  def my_join(tpl):
    return ', '.join(x if isinstance(x, str) else my_join(x) for x in tpl)  


  def open_file_system(self, offset):
    self._fs_info = pytsk3.FS_Info(self._img_info, offset=offset)

  def open_block(self, offset):
    self._fs_block = pytsk3.FS_Block(self._fs_info, a_addr=offset)

  def open_image(self, image_type, filenames):
    self._img_info = images.SelectImage(image_type, filenames)

  '''
  def open_volume():

  def split_partition():
  '''  

  def parse_options(self, options):
    self._recursive = True

def Main():
  """The main program function.
  Returns:
    A boolean containing True if successful or False if not.
  """
  args_parser = argparse.ArgumentParser(description=(
      "Lists a file system in a storage media image or device."))

  args_parser.add_argument(
      "images", nargs="+", metavar="IMAGE", action="store", type=str,
      default=None, help=("Storage media images or devices."))

  args_parser.add_argument(
      "inode", nargs="?", metavar="INODE", action="store",
      type=str, default=None, help=(
          "The inode or path to list. If [inode] is not given, the root "
          "directory is used"))
  # TODO: not implemented.
  # args_parser.add_argument(
  #     "-f", "--fstype", metavar="TYPE", dest="file_system_type",
  #     action="store", type=str, default=None, help=(
  #         "The file system type (use \"-f list\" for supported types)"))
  # TODO: not implemented.
  # args_parser.add_argument(
  #     "-l", dest="long_listing", action="store_true", default=False,
  #     help="Display long version (like ls -l)")

  args_parser.add_argument(
      "-o", "--offset", metavar="OFFSET", dest="offset", action="store",
      type=int, default=0, help="The offset into image file (in bytes)")

  args_parser.add_argument(
      "-r", "--recursive", dest="recursive", action="store_true",
      default=True, help="List subdirectories recursively.")

  args_parser.add_argument(
      "-p", "--partition_id", dest="partition_id", action="store",
      default=0, help="Partition ID.")

  args_parser.add_argument(
      "-i", "--imagetype", dest="image_type", action="store",
      default="raw", help="Imgae Type.")

  options = args_parser.parse_args()

  if not options.images:
    print('No storage media image or device was provided.')
    print('')
    args_parser.print_help()
    print('')
    return False

  #print (type(options))
  #print (options)

  fs = Carpe_FS_Analyze()
  #fs_alloc_info = carpe_fs_alloc_info.Carpe_FS_Alloc_Info()

  fs.parse_options(options)
  print(options.images)
  fs.open_image(options.image_type, options.images)
 
  db_connector = carpe_db.Mariadb()

  db_connector.open()


  for i in fs_alloc_info._unallock_blocks:
    query = db_connector.insert_query_builder("carpe_block_info")
    query = (query + "\n values " + "%s" % (i, ))

    print (query)
    raw_input
    data=db_connector.execute_query(query)
  db_connector.commit()
  
  return True

if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)

