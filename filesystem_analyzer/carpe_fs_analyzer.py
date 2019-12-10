#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os, sys, time
import argparse, gc
import pytsk3

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname('__file__'))))
from filesystem_analyzer import images
from filesystem_analyzer import carpe_file
from filesystem_analyzer import carpe_fs_info
from utility import carpe_db
from filesystem_analyzer import carpe_fs_alloc_info

import pdb

def vdir(obj):
  return [x for x in dir(obj) if not x.startswith('__')]

class CARPE_FS_Analyze(object):
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
      pytsk3.TSK_FS_ATTR_TYPE_HFS_DEFAULT]

  ATTRIBUTE_TYPES_TO_ANALYZE_ADDITIONAL_TIME =[
      pytsk3.TSK_FS_ATTR_TYPE_NTFS_FNAME]

  def __init__(self):
    super(CARPE_FS_Analyze, self).__init__()
    self._fs_info = None
    self._fs_info_2 = None
    self._fs_blocks = []
    self._img_info = None
    self._recursive = True
    self._carpe_files = []
    self._sig_file_path =""

  def fs_info(self,p_id=0):
    fs_info = carpe_fs_info.CARPE_FS_Info()
    fs_info._fs_id = self._fs_info.info.fs_id
    fs_info._p_id = p_id
    fs_info._block_size = self._fs_info.info.block_size
    fs_info._block_count = self._fs_info.info.block_count
    fs_info._root_inum = self._fs_info.info.root_inum
    fs_info._first_inum = self._fs_info.info.first_inum
    fs_info._last_inum = self._fs_info.info.last_inum
    self._fs_info_2 = fs_info

  def block_alloc_status(self):
    alloc_info = carpe_fs_alloc_info.CARPE_FS_Alloc_Info()
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

  def sig_check(self, sig_file_path, target_signature):
    sig_file = open(sig_file_path, "r")    
    ret="Not Detected"
    while True:
      line = sig_file.read_line()
      if (line.split(" ")[0]) in target_signature:
        ret = line.split(" ")[2]
      if not line: break
    sig_file.close()
    return ret

  def list_directory(self, directory, stack=None, path=None, conn=None):
    stack.append(directory.info.fs_file.meta.addr)  
    for directory_entry in directory:
      prefix = "+" * (len(stack) - 1)
      if prefix:
        prefix += " "
      
      # Skip ".", ".." or directory entries without a name.
      if (not hasattr(directory_entry, "info") or
          not hasattr(directory_entry.info, "name") or
          not hasattr(directory_entry.info.name, "name") or
          (directory_entry.info.name.name).decode("utf-8") in [".", ".."]):
        continue
      #self.directory_entry_info(directory_entry, parent_id=stack[-1], path=path)  
      
      files_tuple = map(lambda i: i.toTuple(), self.directory_entry_info(directory_entry, parent_id=stack[-1], path=path))
      
      if files_tuple is not None:
        for i in files_tuple:
          query = conn.insert_query_builder("file_info")
          query = (query + "\n values " + "%s" % (i, ))
          data=conn.execute_query(query)
        conn.commit()
      
      if self._recursive:
        try:
          sub_directory = directory_entry.as_directory()
          inode = directory_entry.info.meta.addr
          # This ensures that we don't recurse into a directory
          # above the current level and thus avoid circular loops.
          if inode not in stack:
            path.append((directory_entry.info.name.name).decode('utf-8','replace'))            
            self.list_directory(sub_directory, stack, path, conn)
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

  def open_block(self, offset):
    self._fs_block = pytsk3.FS_Block(self._fs_info, a_addr=offset)

  def open_image(self, image_type, filenames):
    # List the actual files (any of these can raise for any reason).
    self._img_info = images.SelectImage(image_type, filenames)

  def parse_options(self, options):
    self._recursive = True

  def directory_entry_info(self, directory_entry, parent_id="", path=None):
      meta = directory_entry.info.meta
      name = directory_entry.info.name
      num_of_data_attribute=0

      name_type = "-"
      if name:
        name_type = self.FILE_TYPE_LOOKUP.get(int(name.type), "-")

      meta_type = "-"
      if meta:
        meta_type = self.META_TYPE_LOOKUP.get(int(meta.type), "-")

      directory_entry_type = "{0:s}/{1:s}".format(name_type, meta_type)

      files = []
      file_names=[]
      new_file = carpe_file.CARPE_File()
      new_file._p_id = self._fs_info_2._p_id
      new_file._dir_type = [lambda:0, lambda:int(name.type)][name is not None]()
      new_file._meta_type = [lambda:0, lambda:int(meta.type)][meta is not None]()
      new_file._type = 0
      new_file._parent_id = parent_id
      new_file._parent_path = u"root/"
      for i in path:
        new_file._parent_path += i + u"/"

      for attribute in directory_entry:
        if int(attribute.info.type) in self.ATTRIBUTE_TYPES_TO_ANALYZE:
          #check num of data attr
          if int(attribute.info.type) is pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA:
            num_of_data_attribute +=1
          
          #need to check value
          #$SI, $FN 
          if attribute.info.type in self.ATTRIBUTE_TYPES_TO_ANALYZE_TIME:
            new_file._mtime = [lambda:0, lambda:directory_entry.info.meta.mtime][directory_entry.info.meta.mtime is not None]()  
            new_file._atime = [lambda:0, lambda:directory_entry.info.meta.atime][directory_entry.info.meta.atime is not None]()
            new_file._etime = [lambda:0, lambda:directory_entry.info.meta.ctime][directory_entry.info.meta.ctime is not None]()
            new_file._ctime =[lambda:0, lambda:directory_entry.info.meta.crtime][directory_entry.info.meta.crtime is not None]()
            
            new_file._mtime_nano = [lambda:0, lambda:directory_entry.info.meta.mtime_nano][directory_entry.info.meta.mtime_nano is not None]()            
            new_file._atime_nano = [lambda:0, lambda:directory_entry.info.meta.atime_nano][directory_entry.info.meta.atime_nano is not None]()
            new_file._etime_nano = [lambda:0, lambda:directory_entry.info.meta.ctime_nano][directory_entry.info.meta.ctime_nano is not None]()
            new_file._ctime_nano = [lambda:0, lambda:directory_entry.info.meta.mtime_nano][directory_entry.info.meta.crtime_nano is not None]()

          #$FileName   
          if attribute.info.type in self.ATTRIBUTE_TYPES_TO_ANALYZE_ADDITIONAL_TIME:
            new_file._additional_mtime = [lambda:0, lambda:directory_entry.info.meta.mtime][directory_entry.info.meta.mtime is not None]()  
            new_file._additional_atime = [lambda:0, lambda:directory_entry.info.meta.atime][directory_entry.info.meta.atime is not None]()
            new_file._additional_etime = [lambda:0, lambda:directory_entry.info.meta.ctime][directory_entry.info.meta.ctime is not None]()
            new_file._additional_ctime =[lambda:0, lambda:directory_entry.info.meta.crtime][directory_entry.info.meta.crtime is not None]()
            
            new_file._additional_mtime_nano = [lambda:0, lambda:directory_entry.info.meta.mtime_nano][directory_entry.info.meta.mtime_nano is not None]()            
            new_file._additional_atime_nano = [lambda:0, lambda:directory_entry.info.meta.atime_nano][directory_entry.info.meta.atime_nano is not None]()
            new_file._additional_etime_nano = [lambda:0, lambda:directory_entry.info.meta.ctime_nano][directory_entry.info.meta.ctime_nano is not None]()
            new_file._additional_ctime_nano = [lambda:0, lambda:directory_entry.info.meta.mtime_nano][directory_entry.info.meta.crtime_nano is not None]()                                
          
          new_file._file_id = meta.addr
          new_file._inode = [lambda:"{0:d}".format(meta.addr), lambda:"{0:d}-{1:d}-{2:d}".format(meta.addr, int(attribute.info.type), attribute.info.id)][self._fs_info.info.ftype in [pytsk3.TSK_FS_TYPE_NTFS, pytsk3.TSK_FS_TYPE_NTFS_DETECT]]()          
          
          '''
          #File name       
          if int(attribute.info.type) in self.ATTRIBUTE_TYPES_TO_ANALYZE:
            if new_file._name is not None:
              file_names.append([[lambda:(name.name).decode('utf-8','replace'), lambda:"{0:s}:{1:s}".format((name.name).decode('utf-8','replace'), (attribute.info.name).decode('utf-8','replace'))][(attribute.info.name is not None) & (attribute.info.name not in ["$Data", "$I30"])](), (attribute.info.size)])
            else:
              new_file._name =[lambda:(name.name).decode('utf-8','replace'), lambda:"{0:s}:{1:s}".format((name.name).decode('utf-8','replace'), (attribute.info.name).decode('utf-8','replace'))][(attribute.info.name is not None) & (attribute.info.name not in ["$Data", "$I30"])]()          

          else:
            new_file._name =[lambda:(name.name).decode('utf-8','replace'), lambda:"{0:s}:{1:s}".format((name.name).decode('utf-8','replace'), (attribute.info.name).decode('utf-8','replace'))][(attribute.info.name is not None) & (attribute.info.name not in ["$Data", "$I30"])]()          
            new_file._size = attribute.info.size
          '''


          '''
          if int(attribute.info.type) in self.ATTRIBUTE_TYPES_TO_ANALYZE:
            if new_file._name is not None:
              new_file._name =[lambda:f"{name.name.decode('utf-8')}", lambda:f"{name.name.decode('utf-8')}:{attribute.info.name.decode('utf-8')}"][(attribute.info.name is not None) & (attribute.info.name not in [b"$Data", b"$I30"])]()
              #file_names.append([[lambda:f"{name.name}", lambda:f"{name.name}:{attribute.info.name}"][(attribute.info.name is not None) & (attribute.info.name not in ["$Data", "$I30"])](), (attribute.info.size)])
            else:
              new_file._name =[lambda:f"{name.name}", lambda:f"{name.name}:{attribute.info.name}"][(attribute.info.name is not None) & (attribute.info.name not in ["$Data", "$I30"])]()          
          else:
            new_file._name =[lambda:f"{name.name.decode('utf-8')}", lambda:f"{name.name.decode('utf-8')}:{attribute.info.name.decode('utf-8')}"][(attribute.info.name is not None) & (attribute.info.name not in [b"$Data", b"$I30"])]()
            new_file._size = attribute.info.size
          '''
          #file extension
          file_extension =u""
          if directory_entry_type == "r/r":
            #File name
            new_file._name =[lambda:f"{name.name.decode('utf-8')}", lambda:f"{name.name.decode('utf-8')}:{attribute.info.name.decode('utf-8')}"][(attribute.info.name is not None) & (attribute.info.name not in [b"$Data", b"$I30"])]()
            for i in range( len(list(new_file._name)) -1 , -1, -1):
              if list(new_file._name)[i] != u".":
                file_extension = list(new_file._name)[i] + file_extension  
              else:
                break
            new_file._extension = [lambda:u"", lambda:file_extension][file_extension != new_file._name]()
          else:
            new_file._name =f"{name.name.decode('utf-8')}"

          #size
          new_file._size = int(meta.size)
          #mode
          new_file._mode = int(attribute.info.fs_file.meta.mode)
          #seq
          new_file._meta_seq = int(attribute.info.fs_file.meta.seq)
          #uid
          new_file._uid = int(attribute.info.fs_file.meta.uid)
          #gid
          new_file._gid = int(attribute.info.fs_file.meta.gid)
          
        else:
          debug ="TO DO : Deal with other Attribute Types"
      
      tmp=["..", "", "."]    
      if(new_file._name not in tmp):
        files.append(new_file)        
        # check slack existence
        #slack-size
        if (new_file._size > 1024):
          slack_size = 4096 - (new_file._size % 4096)
        else:
          slack_size = 0
        
        #To Do : Simplify
        '''
        for i in file_names:
          temp = carpe_file.CARPE_File()
          temp.__dict__ = new_file.__dict__.copy()
          
          temp._name = i[0]
          temp._size = i[1]        
          files.append(temp)
        '''
        if slack_size > 0:
          temp = carpe_file.CARPE_File()
          temp.__dict__ = new_file.__dict__.copy()
          temp._size = slack_size
          temp._extension = ""
          temp._type = 7
          temp._name = new_file._name + u"-slack" 
          files.append(temp)

        # TODO: Enable Signature Analysis
        signature_check = False
        if signature_check:
          if(new_file._size>56):
            tmp_file_object = self._fs_info.open_meta(inode=new_file._file_id)          
            self.sig_check(self._sig_file_path, tmp_file_object.read_random(0,56,1))
        new_file._ads = num_of_data_attribute
      return files
