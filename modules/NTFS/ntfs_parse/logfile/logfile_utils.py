from binascii import hexlify


# Search for the fixup_value in the data, if found on the end of the sector then add the corresponding
#  value from the fixup_array in a dictionary with the offset.
# Function also counts the amount of times it found a match with the fixup_value
#  expected (default = 8)  because 8*512 = 4096
#
# input:
#   - data (4096 bytes)
# output:
#   - Boolean (True or False)
#   - True -> offset_dict with offsets and fixup_array values
def search_fixup(self, data):
    offset_dict = {}
    offset = self.SECTOR_SIZE - 2
    fixup_value = self.header.fixup_value
    count = 0
    # start at 510, read 2 bytes, repeat every 512.
    for x in range(offset, len(data), self.SECTOR_SIZE):
        if hexlify(data[x:x+2]) == fixup_value:
            count += 1
            start = int(x/offset-1) << 1
            stop = int(x/offset) << 1
            offset_dict[x] = self.header.fixup_array_raw[start:stop]
        else:
            print('Data: %s at offset %i is not fixup_value: %s' % (hexlify(data[x:x+2]), x, hexlify(fixup_value)))
    return offset_dict if count == self.SECTOR_AMOUNT else {}


# Replace the fixup values with the actual values from a offset dictionary
# Uses bytarray as it is mutable and memoryview to adjust the data.
#
# input:
#   - data (4096 bytes) ~~non writable~~
# output:
#   - data (4096 bytes) ~~non writable~~
def replace_fixup(self, data):
    # make it writeable through memoryview
    wdata = bytearray(data)
    v = memoryview(wdata)
    for offset in self.offset_dict.keys():
        # print('offset: %i -> old data: %s' % (offset, hexlify(wdata[offset:offset+2])))
        v[offset:offset+2] = self.offset_dict[offset]
        # print('offset: %i -> new data: %s' % (offset, hexlify(wdata[offset:offset+2])))
    # make it immutable again
    idata = bytes(wdata)
    return idata


def interpret(data):
    interpreted_data = ''
    for byte in range(len(data)):
        try:
            interpreted_data += data[byte:byte+1].decode() if data[byte:byte+1].decode().isprintable() else '.'
        except Exception as e:
            interpreted_data += '.'
    return interpreted_data


# print function to prettify the hex printed code
def writeout_as_xxd(data, out):
    for x in range(0, len(data), 16):
        interpreted = interpret(data[x:x+16])
        data_line = str(hexlify(data[x:x+16]))[2:-1]
        print_line = ''
        for i in range(0, len(data_line), 4):
            print_line += data_line[i:i+4] + ' '
        out.write('      %07x: %-40s %s\n' % (x, print_line, interpreted))


# mapper function for translating operation codes
def get_operation_type(opcode):
    _map = {
        0: 'No-Operation',                       # 0x00
        1: 'Compensation Log Record',            # 0x01
        2: 'Initialize File Record Segment',     # 0x02
        3: 'Deallocate File Record Segment',     # 0x03
        4: 'Write End of File Record Segment',   # 0x04
        5: 'Create Attribute',                   # 0x05
        6: 'Delete Attribute',                   # 0x06
        7: 'Update Resident Value',              # 0x07
        8: 'Update Nonresident Value',           # 0x08
        9: 'Update Mapping Pairs',               # 0x09
        10: 'Delete Dirty Clusters',             # 0x0A
        11: 'Set New Attribute Sizes',           # 0x0B
        12: 'Add Index Entry Root',              # 0x0C
        13: 'Delete Index Entry Root',           # 0x0D
        14: 'Add Index Entry Allocation',        # 0x0E
        15: 'Delete Index Entry Allocation',     # 0x0F
        # .
        18: 'Set Index Entry VCN Allocation',    # 0x12
        19: 'Update File Name Root',             # 0x13
        20: 'Update File Name Allocation',       # 0x14
        21: 'Set Bits in Nonresident Bitmap',    # 0x15
        22: 'Clear Bits in Nonresident Bitmap',  # 0x16
        # .
        25: 'Prepare Transaction',               # 0x19
        26: 'Commit Transaction',                # 0x1A
        27: 'Forget Transaction',                # 0x1B
        28: 'Open Non Resident Attribute',       # 0x1C
        # .
        31: 'Dirty Page Table Dump',             # 0x1F
        32: 'Transaction Table Dump',            # 0x20
        33: 'Update Record Data Root'            # 0x21
        # .
        # 37:                                    # 0x25
    }
    try:
        value = _map[opcode]
    except KeyError:  # if not in _map
        value = 'unknown'
    return value