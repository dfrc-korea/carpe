import sys
import pytsk3
import datetime
# this library part of libewf is what allows us to access expert witness format images
import pyewf
import argparse
import hashlib


class ewf_Img_Info(pytsk3.Img_Info):
  def __init__(self, ewf_handle):
    self._ewf_handle = ewf_handle
    super(ewf_Img_Info, self).__init__(
        url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

  def close(self):
    self._ewf_handle.close()

  def read(self, offset, size):
    self._ewf_handle.seek(offset)
    return self._ewf_handle.read(size)

  def get_size(self):
    return self._ewf_handle.get_media_size()

filenames = pyewf.glob("Windows10x64.E01")

ewf_handle = pyewf.handle()

ewf_handle.open(filenames)

img_info = ewf_Img_Info(ewf_handle)

partitionTable = pytsk3.Volume_Info(img_info)


for partition in partitionTable:
  print(partition.addr, partition.desc, "%s (%s)" % (partition.start, partition.start * 512), partition.len)
  # If the partition is labeled as NTFS it uses the imagehandle and offset to access the file system
  if b'NTFS' in partition.desc:
    filesystemObject = pytsk3.FS_Info(img_info, offset =(partition.start *512))
    # Opens $MFT in the file system
    fileobject = filesystemObject.open("/$MFT")
    # Prints metadata about $MFT
    print ("File Inode:", fileobject.info.meta.addr)
    print ("File Name:", fileobject.info.name.name)
    print ("File Creation Time:", datetime.datetime.fromtimestamp(fileobject.info.meta.crtime).strftime('%Y-%m-%d %H:%M:%S'))
    # Creates a filename combining the partition # and files name then prints it to the console
    outFileName = str(partition.addr) + str(fileobject.info.name.name)
    print (outFileName)
    # Creates/opens a file to write to using the file name specified above
    outfile = open(outFileName, 'w')
    # Stores the data in the file opened above starting at beginning of file and ending at last byte
    filedata = fileobject.read_random(0, fileobject.info.meta.size)
    # Creates md5 hash object
    md5hash = hashlib.md5()
    # Hashes the data of the specified variable filedata
    md5hash.update(filedata)
    # Prints the md5 hash out in hexidecimal form
    print ("MD5 Hash",md5hash.hexdigest())
    # Creates a sha1 hash object
    sha1hash = hashlib.sha1()
    # Hashes the data in filedata using sha1
    sha1hash.update(filedata)
    # Prints the sha1 hash out in hexidecimal form
    print ("SHA1 Hash",sha1hash.hexdigest())
    # Writes the date stored in filedata to the new file created
    outfile.write(str(filedata))
    # Closes the file the data was copied to
    outfile.close