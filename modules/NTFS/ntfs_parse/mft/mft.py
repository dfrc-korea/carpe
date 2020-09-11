########################################################################################################################
# MFT class(es)
#
# It takes an image and a BootSector object. As the boot sector contains information on where the MFT is located, how
# big and entry is, how big a cluster is, etc, it is required for parsing the MFT.
#
# Right now it just parses the first MFT entry: the entry for the MFT itself.
#
# Issues:
#   -   It doesn't handle references to base records
#   -   Doesn't parse all attribute's contents. It does for:
#       -   StandardInformation
#       -   FileName
#   -   The FileAttributesFlag attribute for multiple attributes is not printed
#   -   Some attributes are not recognized at all: the MFT entry for $MFT states that there should be 6 attributes and
#       there is some trailing data that could be it, but I don't know how to parse it. It seems to be the 'end of
#       attributes' descriptor.
#   -   I can't think of other stuff right now but it must lack other things as well
########################################################################################################################

from collections import OrderedDict
import csv
import sys
import os

from .factories import AttributeTypeEnum
from .mft_entry import MFTEntry
from .attribute_headers import RunList

class MFT():
    MFT = 0

    def __init__(self, image_name=None, boot_sector=None):
        self.image_name = image_name
        self.mft_offset_bytes = boot_sector.byte_offset + boot_sector.mft_starting_cluster * boot_sector.cluster_size
        self.partition_offset_bytes = boot_sector.byte_offset
        self.sector_size = boot_sector.bytes_per_sector
        self.cluster_size = boot_sector.cluster_size
        self.mft_entry_size = boot_sector.mft_entry_size
        self.entries = OrderedDict()
        self.invalid_entries = OrderedDict()
        self.mft = self._parse_mft()

    def _parse_mft(self):
        with open(self.image_name, 'rb') as f:
            f.seek(self.mft_offset_bytes)
            image_byte_offset = self.mft_offset_bytes
            return MFTEntry(inum=0, image_byte_offset=image_byte_offset, data=f.read(self.mft_entry_size))

    def parse_all(self, num=None):
        with open(self.image_name, 'rb') as f:
            f.seek(self.mft_offset_bytes)

            mft = MFTEntry(inum=0, image_byte_offset=self.mft_offset_bytes, data=f.read(self.mft_entry_size))

            mft_runs = mft.attributes[AttributeTypeEnum.DATA][0].header.runlist_extended.cleaned_runs

            inum = 0

            run = mft_runs[0]
            offset = run[RunList.RUN_OFFSET] * self.cluster_size
            length = run[RunList.RUN_LENGTH]

            for run_index in range(len(mft_runs)):
                if run_index:
                    run = mft_runs[run_index]
                    offset = offset + run[RunList.RUN_OFFSET] * self.cluster_size
                    length = run[RunList.RUN_LENGTH]

                f.seek(self.partition_offset_bytes + offset)

                n_entries = int(length * self.cluster_size / self.mft_entry_size)

                for i in range(n_entries):
                    entry = MFTEntry(inum=inum,
                                    image_byte_offset=self.partition_offset_bytes + offset + i * self.cluster_size,
                                    data=f.read(self.mft_entry_size))
                    if entry.is_valid:
                        self.entries[inum] = entry
                    else:
                        self.invalid_entries[inum] = entry
                    inum += 1
                    if inum == num:
                        break

    def parse_inum(self, inum):
        runlist = self.mft.attributes[AttributeTypeEnum.DATA][0].header.runlist_extended
        with open(self.image_name, 'rb') as f:
            image_byte_offset = self.partition_offset_bytes + runlist.to_real_offset(inum * self.mft_entry_size, cluster_size=self.cluster_size)
            f.seek(image_byte_offset)
            entry = MFTEntry(inum=inum, image_byte_offset=image_byte_offset, data=f.read(self.mft_entry_size))
            self.entries[inum] = entry

    def parse_inums(self, inum_range=None):
        runlist = self.mft.attributes[AttributeTypeEnum.DATA][0].header.runlist_extended
        with open(self.image_name, 'rb') as f:
            # inum_ranges may look like [(0,11), (24,23), (40,40)]
            for first, last in inum_range.ranges:
                for inum in range(first, last + 1):
                    image_byte_offset = self.partition_offset_bytes + runlist.to_real_offset(inum * self.mft_entry_size, cluster_size=self.cluster_size)
                    f.seek(image_byte_offset)
                    entry = MFTEntry(inum=inum, image_byte_offset=image_byte_offset, data=f.read(self.mft_entry_size))
                    self.entries[inum] = entry
                    image_byte_offset += self.mft_entry_size

    def max_inum(self):
        return max(self.entries.keys(), key=int)

    def export_parsed(self, inum_range=None, export_file=None):
        if inum_range:
            iterator = inum_range.iterate
        else:
            iterator = self.entries.keys()        # 1) Write to file. Open file and pass descriptor
        if export_file:
            with open(export_file, 'w') as f:
                for inum in iterator:
                    self.entries[inum].writeout_parsed(f)
        # 2) To stdout. Pass sys.stdout
        else:
            for inum in iterator:
                self.entries[inum].writeout_parsed(sys.stdout)

    def export_csv(self, inum_range=None, export_file=None):
        formatted_columns = []
        if inum_range:
            iterator = inum_range.iterate
        else:
            iterator = self.entries.keys()
        # Any MFTEntry object will do, we just have easy access to MFT's own entry.
        formatted_columns.extend(self.mft.format_csv_column_headers())

        # 1) Write to file. Open file and pass descriptor
        if export_file:
            with open(export_file, 'w') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(formatted_columns)
                for inum in iterator:
                    formatted = []
                    formatted.extend(self.entries[inum].format_csv())
                    csv_writer.writerow(formatted)
        # 2) To stdout. Pass sys.stdout
        else:
            csv_writer = csv.writer(sys.stdout)
            csv_writer.writerow(formatted_columns)
            for inum in iterator:
                formatted = []
                formatted.extend(self.entries[inum].format_csv())
                csv_writer.writerow(formatted)

    def export_raw(self, inum_range=None, export_file=None):
        if inum_range:
            iterator = inum_range.iterate
        else:
            iterator = self.entries.keys()        # 1) Write to file. Open file and pass descriptor
        if export_file:
            with open(export_file, 'wb') as f:
                for inum in iterator:
                    self.entries[inum].writeout_raw(f)
        # 2) To stdout. Pass sys.stdout
        else:
            for inum in iterator:
                self.entries[inum].writeout_raw(sys.stdout.buffer)

    def extract_data(self, inum=None, output_file=None, stream=None):
        data_stream = self.entries[inum].attributes[AttributeTypeEnum.DATA][stream]
        if output_file:
            with open(self.image_name, 'rb') as in_file, open(output_file, 'wb') as out_file:
                if data_stream.header.is_resident:
                    self.extract_resident_data(attr=data_stream, out=out_file)
                else:
                    self.extract_non_resident_data(attr=data_stream, in_file=in_file, out_file=out_file)
        else:
            with open(self.image_name, 'rb') as in_file:
                if data_stream.header.is_resident:
                    self.extract_resident_data(attr=data_stream, out=sys.stdout.buffer)
                else:
                    self.extract_non_resident_data(attr=data_stream, in_file=in_file, out_file=sys.stdout.buffer)

    def extract_resident_data(self, attr=None, out=None):
        out.write(attr.content_data)

    def extract_non_resident_data(self, attr=None, in_file=None, out_file=None):
        runs = attr.header.runlist_extended.cleaned_runs

        # First the first entry, which is an absolute offset from the start of the partition
        offset, length = runs[0]

        in_file.seek(self.partition_offset_bytes + offset * self.cluster_size, os.SEEK_SET)
        prev_offset = in_file.tell()
        out_file.write(in_file.read(length * self.cluster_size))

        # The following runs, if existent, are offsets based on the previous location
        for offset, length in runs[1:]:
            in_file.seek(prev_offset + offset * self.cluster_size, os.SEEK_SET)
            prev_offset = in_file.tell()
            out_file.write(in_file.read(length * self.cluster_size))

    def print_statistics(self):
        print('%-20s %s' % ('Maxinum inum:', str(self.max_inum())))
        print('%-20s %s' % ('MFT entries:', str(len([entry for entry in self.entries if entry is not None]))))

    def output_name_mappings(self):
        for entry in self.entries.values():
            if AttributeTypeEnum.FILE_NAME in entry.attributes.keys():
                print('%-6d %s' % (entry.inum, entry.attributes[AttributeTypeEnum.FILE_NAME][0].name))


