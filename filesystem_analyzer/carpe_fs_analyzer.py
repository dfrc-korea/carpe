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
      pytsk3.TSK_FS_ATTR_TYPE_DEFAULT]

  def __init__(self):
    super(Carpe_FS_Analyze, self).__init__()
    self._fs_info = None
    self._fs_info_2 = None
    self._fs_blocks = []
    self._img_info = None
    self._recursive = True
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
    return alloc_info


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
          directory_entry.info.name.name in [".", ".."]):
        continue
      files_tuple = map(lambda i: i.toTuple(), self.directory_entry_info(directory_entry, parent_id=stack[-1], path=path))
      for i in files_tuple:
        query = conn.insert_query_builder("file_info")
        query = (query + " values " + "%s" % (i, )) + ";"
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

      name_type = "-"
      if name:
        name_type = self.FILE_TYPE_LOOKUP.get(int(name.type), "-")

      meta_type = "-"
      if meta:
        meta_type = self.META_TYPE_LOOKUP.get(int(meta.type), "-")

      directory_entry_type = "{0:s}/{1:s}".format(name_type, meta_type)

      files = []
      file_names=[]
      new_file = carpe_file.Carpe_File()
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
          #need to check value
          #$StandardInformation 
          if attribute.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_SI:

            new_file._si_mtime = [lambda:0, lambda:directory_entry.info.meta.mtime][directory_entry.info.meta.mtime is not None]()  
            new_file._si_atime = [lambda:0, lambda:directory_entry.info.meta.atime][directory_entry.info.meta.atime is not None]()
            new_file._si_etime = [lambda:0, lambda:directory_entry.info.meta.ctime][directory_entry.info.meta.ctime is not None]()
            new_file._si_ctime =[lambda:0, lambda:directory_entry.info.meta.crtime][directory_entry.info.meta.crtime is not None]()
            
            new_file._si_mtime_nano = [lambda:0, lambda:directory_entry.info.meta.mtime_nano][directory_entry.info.meta.mtime_nano is not None]()            
            new_file._si_atime_nano = [lambda:0, lambda:directory_entry.info.meta.atime_nano][directory_entry.info.meta.atime_nano is not None]()
            new_file._si_etime_nano = [lambda:0, lambda:directory_entry.info.meta.ctime_nano][directory_entry.info.meta.ctime_nano is not None]()
            new_file._si_ctime_nano = [lambda:0, lambda:directory_entry.info.meta.mtime_nano][directory_entry.info.meta.crtime_nano is not None]()                
          #$FileName   
          if attribute.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_FNAME:

            new_file._fn_mtime = [lambda:0, lambda:directory_entry.info.meta.mtime][directory_entry.info.meta.mtime is not None]()  
            new_file._fn_atime = [lambda:0, lambda:directory_entry.info.meta.atime][directory_entry.info.meta.atime is not None]()
            new_file._fn_etime = [lambda:0, lambda:directory_entry.info.meta.ctime][directory_entry.info.meta.ctime is not None]()
            new_file._fn_ctime =[lambda:0, lambda:directory_entry.info.meta.crtime][directory_entry.info.meta.crtime is not None]()
            
            new_file._fn_mtime_nano = [lambda:0, lambda:directory_entry.info.meta.mtime_nano][directory_entry.info.meta.mtime_nano is not None]()            
            new_file._fn_atime_nano = [lambda:0, lambda:directory_entry.info.meta.atime_nano][directory_entry.info.meta.atime_nano is not None]()
            new_file._fn_etime_nano = [lambda:0, lambda:directory_entry.info.meta.ctime_nano][directory_entry.info.meta.ctime_nano is not None]()
            new_file._fn_ctime_nano = [lambda:0, lambda:directory_entry.info.meta.mtime_nano][directory_entry.info.meta.crtime_nano is not None]()                                
          
          new_file._file_id = meta.addr
          

          new_file._inode = [lambda:"{0:d}".format(meta.addr), lambda:"{0:d}-{1:d}-{2:d}".format(meta.addr, int(attribute.info.type), attribute.info.id)][self._fs_info.info.ftype in [pytsk3.TSK_FS_TYPE_NTFS, pytsk3.TSK_FS_TYPE_NTFS_DETECT]]()          
           
          #File name       
          if attribute.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA:
            
            if new_file._name is not None:
              file_names.append([[lambda:(name.name).decode('utf-8','replace'), lambda:"{0:s}:{1:s}".format((name.name).decode('utf-8','replace'), (attribute.info.name).decode('utf-8','replace'))][(attribute.info.name is not None) & (attribute.info.name not in ["$Data", "$I30"])](), (attribute.info.size)])
            else:
              new_file._name =[lambda:(name.name).decode('utf-8','replace'), lambda:"{0:s}:{1:s}".format((name.name).decode('utf-8','replace'), (attribute.info.name).decode('utf-8','replace'))][(attribute.info.name is not None) & (attribute.info.name not in ["$Data", "$I30"])]()          
            
          else:
            new_file._name =[lambda:(name.name).decode('utf-8','replace'), lambda:"{0:s}:{1:s}".format((name.name).decode('utf-8','replace'), (attribute.info.name).decode('utf-8','replace'))][(attribute.info.name is not None) & (attribute.info.name not in ["$Data", "$I30"])]()          
            new_file._size = attribute.info.size

          #file extension
          file_extension =u""
          if directory_entry_type == "r/r":
            for i in range( len(list(new_file._name)) -1 , -1, -1):
              if list(new_file._name)[i] != u".":
                file_extension = list(new_file._name)[i] + file_extension  
              else:
                break
            new_file._extension = [lambda:u"", lambda:file_extension][file_extension != new_file._name]()          
          
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


      if (new_file._dir_type == 3):        
        files.append(new_file)
      elif (new_file._inode ==""):
        files=[]

      
      # check slack existence

      #slack-size
      if (new_file._size > 1024):
        slack_size = 4096 - (new_file._size % 4096)
      else:
        slack_size = 0
      
      #To Do : Simplification
      for i in file_names:
        temp = carpe_file.Carpe_File()
        temp.__dict__ = new_file.__dict__.copy()
        
        temp._name = i[0]
        temp._size = i[1]        
        files.append(temp)

      if slack_size > 0:
        temp = carpe_file.Carpe_File()
        temp.__dict__ = new_file.__dict__.copy()
        temp._size = slack_size
        temp._extension = ""
        temp._type = 7
        temp._name = new_file._name + u"-slack" 
        files.append(temp)
      
      return files