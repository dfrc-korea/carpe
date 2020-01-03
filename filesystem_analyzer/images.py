#!/usr/bin/env python
# -*- coding: utf-8 -*-
import bisect
import sys

import pyewf
import pyvmdk
import pyvhdi
import pytsk3
import pyqcow

#import pyaff

class CARPE_Image(pytsk3.Img_Info):
  def __init__(self, img_hanle):
    super(CARPE_Image, self).__init__()
    self._partition_table = pytsk3.Volume_Info(img_hanle)

class vhdi_img_info(pytsk3.Img_Info):
  def __init__(self, vhdi_file):
    self._vhdi_file = vhdi_file
    super(vhdi_img_info, self).__init__(
        url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

  def close(self):
    self._vhdi_file.close()

  def read(self, offset, size):
    self._vhdi_file.seek(offset)
    return self._vhdi_file.read(size)

  def get_size(self):
    return self._vhdi_file.get_media_size()

class vmdk_img_info(pytsk3.Img_Info):
  def __init__(self, vmdk_handle):
    self._vmdk_handle = vmdk_handle
    super(vmdk_img_info, self).__init__(
        url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

  def close(self):
    self._vmdk_handle.close()

  def read(self, offset, size):
    self._vmdk_handle.seek(offset)
    return self._vmdk_handle.read(size)

  def get_size(self):
    return self._vmdk_handle.get_media_size()

class ewf_img_info(pytsk3.Img_Info):
  """
    An image info class which uses ewf as a backing reader.

    All we really need to do to provide TSK with the ability to read image formats
    is override the methods below.
  """
  def __init__(self, ewf_handle):
    # stores ewf_handle in class as new variable
    self._ewf_handle = ewf_handle
    super(ewf_img_info, self).__init__(
      url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)
  
  # The following methods override pytsk3's Img_Info methods which would not know how to handle the e01 image
  # close Closes a ewf object
  def close(self):
    self._ewf_handle.close()
  # end of close -----------------------------------
  
  # read allows an e01 file to be opened/read by specifying where the file system info is on the image
  def read(self, offset, size):
    self._ewf_handle.seek(offset)
    return self._ewf_handle.read(size)
  # end of read ------------------------------------------------
  
  # get_size gets the size of the image
  def get_size(self):
    return self._ewf_handle.get_media_size()

class QcowImgInfo(pytsk3.Img_Info):
  def __init__(self, filename):
    self._qcow_file = pyqcow.file()
    self._qcow_file.open(filename)
    super(QcowImgInfo, self).__init__(
        url='', type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

  def close(self):
    self._qcow_file.close()

  def read(self, offset, size):
    self._qcow_file.seek(offset)
    return self._qcow_file.read(size)

  def get_size(self):
    return self._qcow_file.get_media_size()

class SplitImage(pytsk3.Img_Info):
  """
    Virtualize access to split images.

    Note that unlike other tools (e.g. affuse) we do not assume that the images
    are the same size.
  """

  def __init__(self, *files):
    self.fds = []
    self.offsets = [0]
    offset = 0

    for fd in files:
      # Support either a filename or file like objects
      if not hasattr(fd, "read"):
        fd = open(fd, "rb")

      fd.seek(0,2)

      offset += fd.tell()
      self.offsets.append(offset)
      self.fds.append(fd)

    self.size = offset

    # Make sure to call the original base constructor.
    pytsk3.Img_Info.__init__(self, "")

  def get_size(self):
    return self.size

  def read(self, offset, length):
    """
      Read a buffer from the split image set.
      Handles the buffer straddling images.
    """
    result = ""

    # The total available size in the file
    length = int(length)
    length = min(length, int(self.size) - offset)

    while length > 0:
      data = self._ReadPartial(offset, length)
      if not data: break

      length -= len(data)
      result += data
      offset += len(data)

    return result

  def _ReadPartial(self, offset, length):
    """Read as much as we can from the current image."""
    # The part we need to read from.
    idx = bisect.bisect_right(self.offsets, offset + 1) - 1
    fd = self.fds[idx]

    # The offset this part is in the overall image
    img_offset = self.offsets[idx]
    fd.seek(offset - img_offset)

    # This can return less than length
    return fd.read(length)

def SelectImage(img_type, files):
  if img_type == "raw":
    return pytsk3.Img_Info(files)

  elif img_type == "ewf":
    filename = pyewf.glob(*files)
    ewf_handle = pyewf.handle()
    ewf_handle.open(filename)
    return ewf_img_info(ewf_handle)
  
  elif img_type == "vmdk":
    vmdk_handle = pyvmdk.handle()
    vmdk_handle.open(files)
    return vmdk_img_info(vmdk_handle)

  elif img_type == "vhdi":
    vhdi_handle = pyvhdi.file()
    vhdi_handle.open(files)
    return vhdi_img_info(vhdi_handle)

  elif img_type == "qcow":
    return QcowImgInfo(files[0])
    
''' 
  elif img_type == "aff":
    aff_handle = pyaff.handle()
'''