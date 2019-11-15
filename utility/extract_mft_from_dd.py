
import pytsk3
from optparse import OptionParser
import argparse
import carpe_db
import sys
import pdb


BUFF_SIZE = 1024 * 1024

def Main():

    args_parser = argparse.ArgumentParser(description=("Lists a file system in a storage media image or device."))
    args_parser.add_argument("images", nargs="+", metavar="IMAGE", action="store", type=str, default=None, help=("Storage media images or devices."))
    options = args_parser.parse_args()


    img = pytsk3.Img_Info(options.images)
    ## Step 2: Open the filesystem
    fs = pytsk3.FS_Info(img)
    ## Step 3: Open the file using the inode
    f = fs.open_meta(inode = 0)

    ## Step 4: Read all the data and print to stdout
    offset = 0
    size = f.info.meta.size

    file_name= "$MFT"
    output_path="./"


    file_2 = open(output_path + file_name,"w")
    while offset < size:
        available_to_read = min(BUFF_SIZE, size - offset)
        data = f.read_random(offset, available_to_read,1)
        if not data: break
        offset += len(data)
        file_2.write(data)
    file_2.close()    

if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)

