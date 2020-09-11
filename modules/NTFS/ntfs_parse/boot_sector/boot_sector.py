########################################################################################################################
# BootSector class
#
# It takes an image and information on where it finds the required partition (you have to give it information that one
# would otherwise take from the MBR/GPT). mmls is a good tool to find the required information.
#
# It stores the 512 bytes and offers handles for the information within. These handles are grouped according to raw
# values, interpreted values and derived values. Take whatever you need. Not sure whether everything works correctly.
#
# Issues:
#   - According to Brian Carriers book the MFT cluster offset is in byte 48-55 and the mirror is in 56-63. In my case
#       (Windows 8.1 image) this seems to be swapped. "mft starting cluster: 786432", "mft mirror starting cluster: 2"
# Boot sector: Brian Carrier page 272
########################################################################################################################


import struct
from binascii import hexlify
from modules.NTFS.ntfs_parse import reverse, reverse_hexlify


class BootSector:
    OEM_NAME = 'OEM name'
    BYTES_PER_SECTOR = 'bytes per sector'
    SECTORS_PER_CLUSTER = 'sectors per cluster'
    TOTAL_NUMBER_OF_SECTORS = 'total number of sectors'
    MFT_STARTING_CLUSTER = 'mft starting cluster'
    MFT_MIRROR_STARTING_CLUSTER = 'mft mirror starting cluster'
    MFT_ENTRY_SIZE = 'mft entry size'
    SERIAL_NUMBER = 'serial number'

    CLUSTER_SIZE = 'cluster size'

    def __init__(self, image_name=None, offset_sectors=None, offset_bytes=None, sector_size=None):
        self.image_name = image_name
        if offset_sectors is not None:
            self.offset_bytes = offset_sectors * sector_size
        elif offset_bytes is not None:
            self.offset_bytes = offset_bytes
        else:
            self.offset_bytes = 0

        with open(self.image_name, 'rb') as f:
            f.seek(self.offset_bytes)
            self.data = f.read(512)

    ####################################################################################################################
    # Raw values

    @property
    def oem_name_raw(self):
        return self.data[3:11]

    @property
    def bytes_per_sector_raw(self):
        return self.data[11:13]

    @property
    def sectors_per_cluster_raw(self):
        return self.data[13:14]

    @property
    def total_number_of_sectors_raw(self):
        return self.data[40:48]

    @property
    def mft_starting_cluster_raw(self):
        return self.data[48:56]

    @property
    def mft_mirror_starting_cluster_raw(self):
        return self.data[56:64]

    @property
    def mft_entry_size_raw(self):
        return self.data[64:65]

    @property
    def serial_number_raw(self):
        return self.data[72:80]

    ####################################################################################################################
    # Interpreted values

    @property
    def oem_name(self):
        return self.oem_name_raw.decode()

    @property
    def bytes_per_sector(self):
        return int(reverse_hexlify(self.bytes_per_sector_raw), 16)

    @property
    def sectors_per_cluster(self):
        return int(hexlify(self.sectors_per_cluster_raw), 16)

    @property
    def total_number_of_sectors(self):
        return int(reverse_hexlify(self.total_number_of_sectors_raw), 16)

    @property
    def mft_starting_cluster(self):
        # Value resembles the amount of clusters from the start of the partition
        return int(reverse_hexlify(self.mft_starting_cluster_raw), 16)

    @property
    def mft_mirror_starting_cluster(self):
        # Value resembles the amount of clusters from the start of the partition
        return int(reverse_hexlify(self.mft_mirror_starting_cluster_raw), 16)

    @property
    def mft_entry_size(self):
        # val is either:
        #   - positive: it shows the number of clusters that are used for each entry
        #   - negative: it represents the base-2 log of the number of bytes.
        # it's negative when the size of a cluster is larger than a signle MFT entry
        val = struct.unpack('b', self.mft_entry_size_raw)[0]
        if val > 0:
            return val * self.cluster_size
        else:
            return 2**abs(val)

    @property
    def serial_number(self):
        return reverse_hexlify(self.serial_number_raw).decode()

    ####################################################################################################################
    # Derived values

    @property
    def cluster_size(self):
        return self.bytes_per_sector * self.sectors_per_cluster

    @property
    def byte_offset(self):
        return self.offset_bytes

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return (
            (BootSector.OEM_NAME, self.oem_name),
            (BootSector.BYTES_PER_SECTOR, self.bytes_per_sector),
            (BootSector.SECTORS_PER_CLUSTER, self.sectors_per_cluster),
            (BootSector.TOTAL_NUMBER_OF_SECTORS, self.total_number_of_sectors),
            (BootSector.MFT_STARTING_CLUSTER, self.mft_starting_cluster),
            (BootSector.MFT_MIRROR_STARTING_CLUSTER, self.mft_mirror_starting_cluster),
            (BootSector.MFT_ENTRY_SIZE, self.mft_entry_size),
            (BootSector.SERIAL_NUMBER, self.serial_number),
        )

    def print(self):
        print("Directly taken from the boot sector:")
        print("-----------------------------------------------------")
        for description, value in self.all_fields_described():
            print('\t%-30s"%s"' % (description + ':', value))
        print("Derived from the boot sector:")
        print("-----------------------------------------------------")
        print('\t%-30s"%s"' % (BootSector.CLUSTER_SIZE + ':', self.cluster_size))
