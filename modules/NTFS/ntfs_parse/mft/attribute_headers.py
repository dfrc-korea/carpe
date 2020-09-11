from binascii import hexlify
import math

from modules.NTFS.ntfs_parse import reverse, reverse_hexlify, reverse_hexlify_int, filetime_to_datetime, FileAttributesFlag
from .common import _WIDTH, _INDENT, _BIG_BAR, _SMALL_BAR, _INDENTED_SMALL_BAR, AttributeTypeEnum, AttributeTypeEnumConverter


class AttributeHeader():
    TYPE_RAW = ('type', 0, 3)
    ATTRIBUTE_LENGTH = ('attribute length', 4,7)
    NON_RESIDENT_FLAG = ('non-resident flag', 8, 8)
    NAME_LENGTH = ('name length', 9, 9)
    NAME_OFFSET = ('name offset length', 10, 11)
    FLAGS = ('flags', 12,13)
    ATTRIBUTE_IDENTIFIER = ('attribute identifier', 14, 15)

    def __init__(self, data):
        attribute_length = int(reverse_hexlify(data[4:8]), 16)
        self.data = data[:attribute_length]

    ####################################################################################################################
    # Raw values

    @property
    def type_raw(self):
        return self.data[0:4]

    @property
    def attribute_length_raw(self):
        return self.data[4:8]

    @property
    def non_resident_flag_raw(self):
        return self.data[8:9]

    @property
    def name_length_raw(self):
        return self.data[9:10]

    @property
    def name_offset_raw(self):
        return self.data[10:12]

    @property
    def flags_raw(self):
        return self.data[12:14]

    @property
    def attribute_identifier_raw(self):
        return self.data[14:16]

    ####################################################################################################################
    # Interpreted values

    @property
    def type(self):
        return int(reverse_hexlify(self.type_raw), 16)

    @property
    def attribute_length(self):
        return int(reverse_hexlify(self.attribute_length_raw), 16)

    @property
    def non_resident_flag(self):
        return int(reverse_hexlify(self.non_resident_flag_raw), 16)

    @property
    def name_length(self):
        return int(hexlify(self.name_length_raw), 16)

    @property
    def name_offset(self):
        return int(reverse_hexlify(self.name_offset_raw), 16)

    @property
    def flags(self):
        return int(reverse_hexlify(self.flags_raw), 16)

    @property
    def attribute_identifier(self):
        return int(reverse_hexlify(self.attribute_identifier_raw), 16)

    ####################################################################################################################
    # Derived values

    @property
    def enum(self):
        return self._enum

    @property
    def is_resident(self):
        return not bool(self.non_resident_flag)

    @property
    def is_non_resident(self):
        return bool(self.non_resident_flag)

    @property
    def name(self):
         return self.data[self.name_offset : self.name_offset + 2 * self.name_length].decode('utf-16')

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return (
            (AttributeHeader.TYPE_RAW, self.type, self.type_raw),
            (AttributeHeader.ATTRIBUTE_LENGTH, self.attribute_length, self.attribute_length_raw),
            (AttributeHeader.NON_RESIDENT_FLAG, self.non_resident_flag, self.non_resident_flag_raw),
            (AttributeHeader.NAME_LENGTH, self.name_length, self.name_length_raw),
            (AttributeHeader.NAME_OFFSET, self.name_offset, self.name_offset_raw),
            (AttributeHeader.FLAGS, self.flags, self.flags_raw),
            (AttributeHeader.ATTRIBUTE_IDENTIFIER, self.attribute_identifier, self.attribute_identifier_raw)
        )

    def extra_pairs(self):
        return ()

    def writeout_parsed(self, out):
        # Writeout the normal header
        for (description, low, high), value, value_raw in self.all_fields_described():
            out.write('%s%-36s | %-5s | %-9s | %s\n' % (
                _INDENT,
                description,
                str(low) + '-' + str(high),
                value,
                hexlify(value_raw)))
        # Writeout other fields
        if len(self.extra_pairs()) > 0:
            out.write('\n')
        for key, val in self.extra_pairs():
            out.write('%s%-20s %s\n' % (_INDENT, key + ':', val))



class AttributeHeaderResident(AttributeHeader):
    CONTENT_SIZE = ('content size', 16, 19)
    CONTENT_OFFSET = ('content offset', 20, 21)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enum = AttributeTypeEnumConverter.from_identifier(self.type)


    ####################################################################################################################
    # Raw values

    @property
    def content_size_raw(self):
        return self.data[16:20]

    @property
    def content_offset_raw(self):
        return self.data[20:22]

    ####################################################################################################################
    # Interpreted values

    @property
    def content_size(self):
        return int(reverse_hexlify(self.content_size_raw), 16)

    @property
    def content_offset(self):
        return int(reverse_hexlify(self.content_offset_raw), 16)

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return super().all_fields_described() + (
            (AttributeHeaderResident.CONTENT_SIZE, self.content_size, self.content_size_raw),
            (AttributeHeaderResident.CONTENT_OFFSET, self.content_offset, self.content_offset_raw)
        )

    def extra_pairs(self):
        return (
            ('type', str(self.enum.value)),
            ('resident', str(self.is_resident)),
            ('non-resident', str(self.is_non_resident)),
            ('name', self.name)
        )


class RunList():
    RUN_OFFSET = 0
    RUN_LENGTH = 1

    def __init__(self, runlist_bytes):
        self.runlist_bytes = runlist_bytes
        self.runs = []
        self._parse()

    def _parse(self):
        current_runlist = self.runlist_bytes
        while len(current_runlist) > 2 and current_runlist[0] >= 0b00000001:
            run_offset_length = (current_runlist[0] & 0b11110000) >> 4
            run_length_length = current_runlist[0] & 0b00001111

            if run_offset_length > 0:
                run_offset_bytes = reverse(current_runlist[1+run_length_length : 1+run_length_length+run_offset_length])
                run_offset = int(hexlify(run_offset_bytes), 16)
                # Check whether the MSB is set, which means that it is signed and therefore negative
                if run_offset_bytes[0] >= 128:
                    run_offset -= 256 ** len(run_offset_bytes)
            else:
                run_offset = 0
            run_length = reverse_hexlify_int(current_runlist[1 : 1+run_length_length])
            self.runs.append((run_offset, run_length))
            current_runlist = current_runlist[1+run_length_length+run_offset_length:]

    @property
    def cleaned_runs(self):
        # In case of a sparse run, skip this one. We don't want to write useless zeros.
        # In some circumstances people choose to include them, because it makes it easier for indexing.
        return [tup for tup in self.runs if tup[self.RUN_OFFSET] != 0]

    def to_real_offset(self, virt_offset, cluster_size=4096):
        """Converts a virtual offset to an actual offset based on the start of the cluster run."""

        offset = 0
        # see in what run the virtual offset resides
        virt_cluster = math.floor(virt_offset / cluster_size)
        virt_cluster_remainder = virt_offset % cluster_size

        # Go through all runs, each time either returning the right location or progressing further looking for it.
        for run_offset, run_length in self.cleaned_runs:
            if virt_cluster >= run_length:
                # the offset we're looking for is beyond this run.
                offset += run_offset
                virt_cluster -= run_length
            else:
                # The virtual byte offset is in this run. Determine the exact offset.
                offset += run_offset + virt_cluster
                return offset * cluster_size + virt_cluster_remainder



class AttributeHeaderNonResident(AttributeHeader):
    RUNLIST_STARTING_VCN = ('runlist starting VCN', 16, 23)
    RUNLIST_ENDING_VCN = ('runlist ending VCN', 24, 31)
    RUNLIST_OFFSET = ('runlist offset', 32, 33)
    COMPRESSION_UNIT_SIZE = ('compression unit size', 34, 35)
    ATTRIBUTE_CONTENT_ALLOCATED_SIZE = ('attribute content allocated size', 40, 47)
    ATTRIBUTE_CONTENT_ACTUAL_SIZE = ('attribute content actual size', 48, 55)
    ATTRIBUTE_CONTENT_INITIALIZED_SIZE = ('attribute content initialized size', 56, 63)
    RUNLIST = ('runlist', '?', '+')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enum = AttributeTypeEnumConverter.from_identifier(self.type)
        self.runlist_extended = RunList(self.runlist_raw)


    ####################################################################################################################
    # Raw values

    @property
    def runlist_starting_vcn_raw(self):
        return self.data[16:24]

    @property
    def runlist_ending_vcn_raw(self):
        return self.data[24:32]

    @property
    def runlist_offset_raw(self):
        return self.data[32:34]

    @property
    def compression_unit_size_raw(self):
        return self.data[34:36]

    @property
    def attribute_content_allocated_size_raw(self):
        return self.data[40:48]

    @property
    def attribute_content_actual_size_raw(self):
        return self.data[48:56]

    @property
    def attribute_content_initialized_size_raw(self):
        return self.data[56:64]

    @property
    def runlist_raw(self):
        return self.data[self.runlist_offset : self.runlist_offset + self.attribute_length]

    ####################################################################################################################
    # Interpreted values

    @property
    def runlist_starting_vcn(self):
        return int(reverse_hexlify(self.runlist_starting_vcn_raw), 16)

    @property
    def runlist_ending_vcn(self):
        return int(reverse_hexlify(self.runlist_starting_vcn_raw), 16)

    @property
    def runlist_offset(self):
        return int(reverse_hexlify(self.runlist_offset_raw), 16)

    @property
    def compression_unit_size(self):
        # not checked yet if this is correct. see blz 257
        return int(reverse_hexlify(self.compression_unit_size_raw), 16)

    @property
    def attribute_content_allocated_size(self):
        return int(reverse_hexlify(self.attribute_content_allocated_size_raw), 16)

    @property
    def attribute_content_actual_size(self):
        return int(reverse_hexlify(self.attribute_content_actual_size_raw), 16)

    @property
    def attribute_content_initialized_size(self):
        return int(reverse_hexlify(self.attribute_content_initialized_size_raw), 16)

    @property
    def runlist(self):
        return hexlify(self.runlist_raw).decode()

    ####################################################################################################################
    # Derived values


    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return super().all_fields_described() + (
            (AttributeHeaderNonResident.RUNLIST_STARTING_VCN, self.runlist_starting_vcn, self.runlist_starting_vcn_raw),
            (AttributeHeaderNonResident.RUNLIST_ENDING_VCN, self.runlist_ending_vcn, self.runlist_ending_vcn_raw),
            (AttributeHeaderNonResident.RUNLIST_OFFSET, self.runlist_offset, self.runlist_offset_raw),
            (AttributeHeaderNonResident.COMPRESSION_UNIT_SIZE, self.compression_unit_size, self.compression_unit_size_raw),
            (AttributeHeaderNonResident.ATTRIBUTE_CONTENT_ALLOCATED_SIZE, self.attribute_content_allocated_size, self.attribute_content_allocated_size_raw),
            (AttributeHeaderNonResident.ATTRIBUTE_CONTENT_ACTUAL_SIZE, self.attribute_content_actual_size, self.attribute_content_actual_size_raw),
            (AttributeHeaderNonResident.ATTRIBUTE_CONTENT_INITIALIZED_SIZE, self.attribute_content_initialized_size, self.attribute_content_initialized_size_raw),
            (AttributeHeaderNonResident.RUNLIST, self.runlist, self.runlist_raw)
        )

    def extra_pairs(self):
        return (
            ('type', str(self.enum.value)),
            ('resident', str(self.is_resident)),
            ('non-resident', str(self.is_non_resident)),
            ('runlist', self.runlist_extended.runs),
            ('name', self.name)
        )
