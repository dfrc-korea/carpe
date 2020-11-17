import sys
import os
import argparse
import enum
import math
import json
import binascii

from ctypes import *
from struct import *
from dataclasses import dataclass, field
from collections import defaultdict


class _MSSQLPageHeader(LittleEndianStructure):
    _fields_ = [
        ('headerversion', c_uint8),
        ('type', c_uint8),
        ('typeflagbits', c_uint8),
        ('level', c_uint8),
        ('flagbits', c_uint16),
        ('indexid', c_uint16),
        ('previouspageid', c_uint32),
        ('previousfileid', c_uint16),
        ('pminlen', c_uint16),
        ('nextpageid', c_uint32),
        ('nextfileid', c_uint16),
        ('slotcnt', c_uint16),
        ('objectid', c_uint32),
        ('freecnt', c_uint16),
        ('freedata', c_uint16),
        ('pageid', c_uint32),
        ('fileid', c_uint16),
        ('reservedcnt', c_uint16),
        ('lsn1', c_uint32),
        ('lsn2', c_uint32),
        ('lsn3', c_uint16),
        ('xactreserved', c_uint16),
        ('xdesidpart2', c_uint32),
        ('xdesidpart1', c_uint16),
        ('ghostreccnt', c_uint16),
        ('tornbits', c_uint32)
    ]


def _memcpy(buf, fmt):
    return cast(c_char_p(buf), POINTER(fmt)).contents


@dataclass(order=True)
class SchemeInfo:
    tobjectid: int = 0
    colorder: int = 0
    xtype: int = 0
    utype: int = 0
    colsize: int = 0
    colname: str = ''
    datatype: str = ''
    kindofcol: int = 0
    ismax: bool = False
    precisionofnumeric: int = 0
    scaleofnumeric: int = 0
    precisionoftime: int = 0


class Columntype(enum.Enum):
    STATIC_COLUMN = 1
    VARIABLE_COLUMN = 2


@dataclass(order=True)
class RowInfo:
    staticlength: int = 0
    numoftotalcol: int = 0
    numofstaticcol: int = 0
    numofvariablecol: int = 0
    checklastcolumn: bool = False
    numofbitcol: int = 0


@dataclass(order=True)
class TableInfo:
    tobjectid: int = 0
    tablename: str = ''
    numofcolumns: int = 0
    pobjectid: int = 0
    partitionid: int = 0


@dataclass(order=True, frozen=True)
class RowId:
    fileId: int = None
    pageId: int = None
    slotNumber: int = None


@dataclass(order=True)
class LobInfo:
    timestamp: int = None
    link: set = ()


class MSSQL():
    def __init__(self):
        self.filepath = ''
        self.fHandle = ''
        self.fbuf = ''
        self.pagesize = 8192

    def open(self, filepath):
        try:
            self.fHandle = open(filepath, 'rb')
        except:
            print('File open error : ' + filepath)
            return 1
        self.filepath = filepath
        print('Open ' + filepath)

    def read(self, offset, size):
        buf = ''
        try:
            self.fHandle.seek(offset)
            buf = self.fHandle.read(size)
        except:
            print('File read error')
        return buf

    def close(self):
        self.fHandle.close()

    def getPageHeader(self, buf):
        pageheader = _memcpy(buf[:sizeof(_MSSQLPageHeader)], _MSSQLPageHeader)
        return pageheader

    def getRowOffsetArray(self, buf, pageheader):
        fmt = '<' + str(pageheader.slotcnt) + 'H'
        rowoffsetarray = reversed(unpack(fmt, buf[-pageheader.slotcnt * 2:]))
        rowoffsetarray = list(filter(lambda x: x != 0, rowoffsetarray))
        return rowoffsetarray


class MSSQLRecovery():
    def __init__(self, mssql):
        self.mssql = mssql
        self.pages = defaultdict(lambda: 0)  # pageMap
        self.systemschemesmap = defaultdict(list)
        self.userschemesmap = defaultdict(list)
        self.tablelist = []
        self.of = None

    def scanPages(self, filename):
        # print('MDF Page Scan')
        pagenumber = 0
        jsonFilename = os.path.abspath(os.path.splitext(filename)[0] + '.json')

        if os.path.isfile(jsonFilename):
            pages = json.load(open(jsonFilename))
            for pagenumber, objectid in pages.items():
                self.pages[int(pagenumber)] = objectid
        else:
            while True:
                buf = self.mssql.read(self.mssql.pagesize * pagenumber, self.mssql.pagesize)
                if not buf:
                    break

                if buf[0x01] != 0x01:
                    pagenumber += 1
                    continue

                pageheader = self.mssql.getPageHeader(buf)
                self.pages[pagenumber] = pageheader.objectid
                pagenumber += 1

                del buf

            json.dump(self.pages, open(jsonFilename, 'w'))

    def getSystemTableColumnInfo(self):
        # print('Get System Table Column Information')

        systemTable = [('sysschobjs', 0x22), ('sysiscols', 0x37), ('sysrowsets', 0x05), ('sysallocunits', 0x07)]

        syscol_page = defaultdict(list, {k: v for k, v in self.pages.items() if v == 0x29})
        for _, t_objectID in systemTable:
            for k, v in syscol_page.items():
                buf = self.mssql.read(k * self.mssql.pagesize, self.mssql.pagesize)
                pageheader = self.mssql.getPageHeader(buf)

                if pageheader.flagbits & 0x100:
                    self._tornbits(buf)

                rowoffsetarray = sorted(self.mssql.getRowOffsetArray(buf, pageheader))

                for offset in rowoffsetarray:
                    tboID = unpack('<I', buf[offset + 0x4: offset + 0x8])[0]

                    if tboID != t_objectID:
                        continue

                    colRecordLen = unpack('<H', buf[offset + 0x33: offset + 0x35])[0]
                    if colRecordLen <= 0:
                        continue

                    colData = buf[offset: offset + colRecordLen]

                    scInfo = SchemeInfo()
                    scInfo.ismax = False
                    scInfo.tobjectid = t_objectID
                    scInfo.colorder = unpack('<H', colData[0x0A: 0x0C])[0]
                    scInfo.xtype = colData[0x0E]
                    scInfo.utype = unpack('<I', colData[0x0F: 0x13])[0]
                    scInfo.colsize = unpack('<H', colData[0x13: 0x15])[0]
                    if scInfo.colsize >= 0xFFFF:
                        scInfo.colsize = 0x10
                        scInfo.ismax = True
                    scInfo.colname = colData[0x35:].decode('utf-16')
                    scInfo.datatype = self._getTypeName(scInfo.xtype, scInfo.utype)
                    if scInfo.datatype == 'numeric' or scInfo.datatype == 'decimal':
                        scInfo.precisionofnumeric = colData[0x15]
                        scInfo.scaleofnumeric = colData[0x16]
                        scInfo.datatype = scInfo.datatype + '({}, {})'.format(str(scInfo.precisionofnumeric),
                                                                              str(scInfo.scaleofnumeric))
                    elif scInfo.datatype == 'time' or scInfo.datatype == 'datetime2' or scInfo.datatype == 'datetimeoffset':
                        scInfo.precisionoftime = colData[0x16]
                        scInfo.datatype = scInfo.datatype + '({})'.format(str(scInfo.precisionoftime))
                    self.systemschemesmap[t_objectID].append(scInfo)

                del buf

    def getTableInfo(self):
        # print('Get Table Information')

        sysschobjs_page = defaultdict(list, {k: v for k, v in self.pages.items() if v == 0x22})  # sysschobjs
        sysschobjs_schemes = self.systemschemesmap[0x22]  # sysschobjs
        sysschobjs_schemes = sorted(sysschobjs_schemes, key=lambda SchemeInfo: SchemeInfo.colorder)

        rowinfo = RowInfo()

        if len(sysschobjs_schemes) == 0:
            return False

        for schema in sysschobjs_schemes:
            self._tableSchemeAnalyzer(schema, rowinfo)

        if len(sysschobjs_schemes) != rowinfo.numoftotalcol:
            return False

        for k, v in sysschobjs_page.items():
            buf = self.mssql.read(k * self.mssql.pagesize, self.mssql.pagesize)
            pageheader = self.mssql.getPageHeader(buf)

            if pageheader.flagbits & 0x100:
                self._tornbits(buf)

            rowoffsetarray = sorted(self.mssql.getRowOffsetArray(buf, pageheader))

            recordlen = rowoffsetarray[1:] + [self.mssql.pagesize - len(rowoffsetarray) * 2]
            for offset, length in zip(rowoffsetarray, recordlen):
                tbinfo = TableInfo()

                if self._parseTableInfoRecord(buf[offset:], length - offset, tbinfo, sysschobjs_schemes,
                                              rowinfo) == True:
                    self.tablelist.append(tbinfo)

            del buf

        if len(self.tablelist) == 0:
            return False
        else:
            return True

    def getColumnInfo(self):
        # print('Get Column Information')

        syscolpars_page = defaultdict(list, {k: v for k, v in self.pages.items() if v == 0x29})

        for tableinfo in self.tablelist:
            tobjectid = tableinfo.tobjectid

            for k, v in syscolpars_page.items():
                buf = self.mssql.read(k * self.mssql.pagesize, self.mssql.pagesize)
                pageheader = self.mssql.getPageHeader(buf)

                if pageheader.flagbits & 0x100:
                    self._tornbits(buf)

                rowoffsetarray = sorted(self.mssql.getRowOffsetArray(buf, pageheader))

                for offset in rowoffsetarray:
                    tboId = unpack('<I', buf[offset + 0x04:offset + 0x08])[0]
                    if tboId != tobjectid:
                        continue

                    colRecordLen = unpack('<H', buf[offset + 0x33:offset + 0x35])[0]
                    if colRecordLen <= 0:
                        continue

                    colData = buf[offset:offset + colRecordLen]

                    scinfo = SchemeInfo()
                    scinfo.ismax = False
                    scinfo.tobjectid = tobjectid
                    scinfo.colorder = unpack('<H', colData[0x0A:0x0C])[0]
                    scinfo.xtype = colData[0x0E]
                    scinfo.utype = unpack('<I', colData[0x0F:0x13])[0]
                    scinfo.colsize = unpack('<H', colData[0x13:0x15])[0]
                    if scinfo.colsize >= 0xFFFF:
                        scinfo.colsize = 0x10
                        scinfo.ismax = True
                    scinfo.colname = colData[0x35:].decode('utf-16')
                    scinfo.datatype = self._getTypeName(scinfo.xtype, scinfo.utype)
                    if scinfo.datatype == 'numeric' or scinfo.datatype == 'decimal':
                        scinfo.precisionofnumeric = colData[0x15]
                        scinfo.scaleofnumeric = colData[0x16]
                        scinfo.datatype = scinfo.datatype + '({}, {})'.format(str(scinfo.precisionofnumeric),
                                                                              str(scinfo.scaleofnumeric))
                    elif scinfo.datatype == 'time' or scinfo.datatype == 'datetime2' or scinfo.datatype == 'datetimeoffset':
                        scinfo.precisionoftime = colData[0x16]
                        scinfo.datatype = scinfo.datatype + '({})'.format(str(scinfo.precisionoftime))
                    self.userschemesmap[tobjectid].append(scinfo)

                del buf

    def getKeyColumnInfo(self):
        # print('Get Key Column Information')

        sysiscols_page = defaultdict(list, {k: v for k, v in self.pages.items() if v == 0x37})
        sysiscols_schemes = self.systemschemesmap[0x37]
        sysiscols_schemes = sorted(sysiscols_schemes, key=lambda SchemeInfo: SchemeInfo.colorder)

        rowinfo = RowInfo()

        if len(sysiscols_schemes) == 0:
            return False

        for schema in sysiscols_schemes:
            self._tableSchemeAnalyzer(schema, rowinfo)

        if len(sysiscols_schemes) != rowinfo.numoftotalcol:
            return False

        for tableinfo in self.tablelist:
            tobjectid = tableinfo.tobjectid

            for k, v in sysiscols_page.items():
                buf = self.mssql.read(k * self.mssql.pagesize, self.mssql.pagesize)
                pageheader = self.mssql.getPageHeader(buf)

                if pageheader.flagbits & 0x100:
                    self._tornbits(buf)

                rowoffsetarray = sorted(self.mssql.getRowOffsetArray(buf, pageheader))

                recordlen = rowoffsetarray[1:] + [self.mssql.pagesize - len(rowoffsetarray) * 2]
                for offset, length in zip(rowoffsetarray, recordlen):
                    indexcolumnid = 0
                    columnid = 0
                    if self._parseIndexInfoRecord(buf[offset:], length - offset, sysiscols_schemes, rowinfo, tobjectid,
                                                  indexcolumnid, columnid) == True:
                        if (indexcolumnid != 0) and (columnid != 0) and (indexcolumnid != columnid):
                            self._changeOrdinal(sysiscols_schemes, indexcolumnid, columnid, '', tobjectid)

                del buf

        return True

    def getPageObjectId(self):
        # print('Get Page Object Id')

        sysrowsets_page = defaultdict(list, {k: v for k, v in self.pages.items() if v == 0x05})
        sysrowsets_schemes = self.systemschemesmap[0x05]
        sysrowsets_schemes = sorted(sysrowsets_schemes, key=lambda SchemeInfo: SchemeInfo.colorder)

        rowinfo = RowInfo()

        if len(sysrowsets_schemes) == 0:
            return False

        for schema in sysrowsets_schemes:
            self._tableSchemeAnalyzer(schema, rowinfo)

        if len(sysrowsets_schemes) != rowinfo.numoftotalcol:
            return False

        for tableinfo in self.tablelist:
            tobjectid = tableinfo.tobjectid
            isFindId = False

            for k, v in sysrowsets_page.items():
                if isFindId:
                    break

                buf = self.mssql.read(k * self.mssql.pagesize, self.mssql.pagesize)
                pageheader = self.mssql.getPageHeader(buf)

                if pageheader.flagbits & 0x100:
                    self._tornbits(buf)

                rowoffsetarray = sorted(self.mssql.getRowOffsetArray(buf, pageheader))

                recordlen = rowoffsetarray[1:] + [self.mssql.pagesize - len(rowoffsetarray) * 2]
                for offset, length in zip(rowoffsetarray, recordlen):
                    tableinfo.partitionid = self._parseObjectInfoRecord(buf[offset:], length - offset,
                                                                        sysrowsets_schemes, rowinfo, tobjectid)
                    if tableinfo.partitionid != 0:
                        if (self._searchSysallocunits(tableinfo)):
                            isFindId = True
                            break

                del buf

        return True

    def recovery(self, output_path):
        # print('Recovery MSSQL')

        for tableinfo in self.tablelist:
            table_scheme = self.userschemesmap[tableinfo.tobjectid]
            table_scheme = sorted(table_scheme, key=lambda SchemeInfo: SchemeInfo.colorder)

            self.of = open(output_path + os.sep + tableinfo.tablename + ".sql", 'w', -1, 'utf-8')

            create_query = 'create table ' + tableinfo.tablename
            colinfo = []
            rowinfo = RowInfo()

            if len(table_scheme) == 0:
                continue

            for schema in table_scheme:
                self._tableSchemeAnalyzer(schema, rowinfo)

            if len(table_scheme) != rowinfo.numoftotalcol:
                continue

            for schema in table_scheme:
                if schema.datatype == 'varchar' or schema.datatype == 'nvarchar' or \
                        schema.datatype == 'char' or schema.datatype == 'nchar' or \
                        schema.datatype == 'binary' or schema.datatype == 'varbinary':
                    if schema.ismax:
                        colinfo.append(schema.colname + ' ' + schema.datatype + '(max)')
                    else:
                        if schema.datatype == 'nvarchar' or schema.datatype == 'nchar':
                            colinfo.append(
                                schema.colname + ' ' + schema.datatype + '(' + str(int(schema.colsize / 2)) + ')')
                        else:
                            colinfo.append(schema.colname + ' ' + schema.datatype + '(' + str(schema.colsize) + ')')
                else:
                    colinfo.append(schema.colname + ' ' + schema.datatype)

            create_query = create_query + '(' + ','.join(colinfo) + ')\n'
            self.of.write(create_query)
            # run query
            table_page = defaultdict(list, {k: v for k, v in self.pages.items() if v == tableinfo.pobjectid})

            for k, v in table_page.items():
                if k == 3276283:
                    a = 0

                buf = self.mssql.read(k * self.mssql.pagesize, self.mssql.pagesize)
                pageheader = self.mssql.getPageHeader(buf)
                if pageheader.type != 0x01:
                    continue

                if pageheader.flagbits & 0x100:
                    self._tornbits(buf)

                # print('Carving... PageID : ' + str(k) + ', Table : ' + tableinfo.tablename)

                rowoffsetarray = sorted(self.mssql.getRowOffsetArray(buf, pageheader))

                startOffsetOfRowOffsetArray = self.mssql.pagesize - len(rowoffsetarray) * 2

                nextoffsetarray = rowoffsetarray[1:]
                nextoffsetarray.append(startOffsetOfRowOffsetArray)

                if len(rowoffsetarray) == 0:  # all record data is unallocated
                    self._scanForUnallocatedArea(buf, 0x60, self.mssql.pagesize - 0x60, rowinfo, tableinfo.tablename,
                                                 table_scheme)

                if len(rowoffsetarray) != 0 and rowoffsetarray[0] != 0x60:  # 1st area
                    self._scanForUnallocatedArea(buf, 0x60, rowoffsetarray[0] - 0x60, rowinfo, tableinfo.tablename,
                                                 table_scheme)

                for cur, nxt in zip(rowoffsetarray, nextoffsetarray):  # 2nd and 3rd area
                    recordLen, isAlive = self._calcRecordLen(buf[cur:], rowinfo)
                    if isAlive:
                        currentoffset = cur + recordLen
                        lenofunalloc = nxt - (cur + recordLen)
                    else:
                        currentoffset = cur
                        lenofunalloc = nxt - cur
                    if cur + recordLen == nxt:
                        continue

                    self._scanForUnallocatedArea(buf, currentoffset, lenofunalloc, rowinfo, tableinfo.tablename,
                                                 table_scheme)

            self.of.close()

    def _getTypeName(self, xtype, utype):
        if xtype == 0x7F:
            return 'bigint'
        elif xtype == 0x68:
            return 'bit'
        elif xtype == 0x28:
            return 'date'
        elif xtype == 0x2A:
            return 'datetime2'
        elif xtype == 0x6A:
            return 'decimal'
        elif xtype == 0xF0:
            if utype == 0x80:
                return 'hierarchyid'
            elif utype == 0x81:
                return 'geometry'
            elif utype == 0x82:
                return 'geography'
            else:
                return 'unknown'
        elif xtype == 0x38:
            return 'int'
        elif xtype == 0xEF:
            return 'nchar'
        elif xtype == 0x6C:
            return 'numeric'
        elif xtype == 0x3A:
            return 'smalldatetime'
        elif xtype == 0x7A:
            return 'smallmoney'
        elif xtype == 0xBD:
            return 'timestamp'
        elif xtype == 0x24:
            return 'uniqueidentifier'
        elif xtype == 0xAD:
            return 'binary'
        elif xtype == 0xAF:
            return 'char'
        elif xtype == 0x3D:
            return 'datetime'
        elif xtype == 0x2B:
            return 'datetimeoffset'
        elif xtype == 0x3E:
            return 'float'
        elif xtype == 0x3C:
            return 'money'
        elif xtype == 0x3B:
            return 'real'
        elif xtype == 0x34:
            return 'smallint'
        elif xtype == 0x62:
            return 'sql_variant'
        elif xtype == 0x29:
            return 'time'
        elif xtype == 0x30:
            return 'tinyint'
        elif xtype == 0xF1:
            return 'xml'
        elif xtype == 0xA5:
            return 'varbinary'
        elif xtype == 0x22:
            return 'image'
        elif xtype == 0xE7:
            if utype == 0xE7:
                return 'nvarchar'
            elif utype == 0x100:
                return 'sysname'
            else:
                return 'unknown'
        elif xtype == 0xA7:
            return 'varchar'
        elif xtype == 0x23:
            return 'text'
        elif xtype == 0x63:
            return 'ntext'
        else:
            return 'unknown'

    def _tableSchemeAnalyzer(self, schema, rowinfo):
        if schema.datatype == 'bigint' or schema.datatype == 'date' or \
                schema.datatype == 'geography' or schema.datatype == 'geometry' or \
                schema.datatype == 'real' or schema.datatype == 'int' or \
                schema.datatype == 'float' or schema.datatype == 'char' or \
                schema.datatype == 'nchar' or schema.datatype == 'binary' or \
                schema.datatype == 'tinyint' or schema.datatype == 'smallint' or \
                schema.datatype == 'rowversion' or schema.datatype == 'money' or \
                schema.datatype == 'smallmoney' or schema.datatype == 'uniqueidentifier' or \
                schema.datatype.find('numeric') != -1 or schema.datatype.find('decimal') != -1 or \
                schema.datatype.find('time') != -1:
            schema.kindofcol = Columntype.STATIC_COLUMN
            rowinfo.numofstaticcol += 1
            rowinfo.staticlength += schema.colsize
        elif schema.datatype == 'bit':
            schema.kindofcol = Columntype.STATIC_COLUMN
            if rowinfo.numofbitcol % 8 == 0:
                rowinfo.staticlength += 1
            rowinfo.numofstaticcol += 1
            rowinfo.numofbitcol += 1
        elif schema.datatype == 'varchar' or schema.datatype == 'nvarchar' or \
                schema.datatype == 'varbinary' or schema.datatype == 'hierarchyid' or \
                schema.datatype == 'sql_variant' or schema.datatype == 'xml' or \
                schema.datatype == 'sysname':
            schema.kindofcol = Columntype.VARIABLE_COLUMN
            rowinfo.numofvariablecol += 1
            rowinfo.checklastcolumn = True
        elif schema.datatype == 'text' or schema.datatype == 'image' or \
                schema.datatype == 'ntext':
            schema.kindofcol = Columntype.VARIABLE_COLUMN
            rowinfo.numofvariablecol += 1
            rowinfo.checklastcolumn = False
        rowinfo.numoftotalcol = schema.colorder

    def _parseTableInfoRecord(self, buf, recordlen, tableinfo, schemlist, rowinfo):
        # raise NotImplementedError
        lenofnullbitmap = math.ceil(rowinfo.numoftotalcol / 8)
        offsetoftotalnumofcol = unpack('<H', buf[0x02: 0x04])[0]
        totalnumofcol = unpack('<H', buf[offsetoftotalnumofcol:offsetoftotalnumofcol + 0x02])[0]

        if rowinfo.numoftotalcol != totalnumofcol:
            return False

        staticoffset = 1 + 1 + 2  # statusBit A + statusBit B + OffsetOfTotalNumOfCol

        if rowinfo.numofvariablecol != 0:
            variableoffset = staticoffset + rowinfo.staticlength + 2 + lenofnullbitmap
            numofvariablecol = unpack('<H', buf[variableoffset: variableoffset + 0x02])[0]
            variableoffset += 2
            variableoffset += (2 * numofvariablecol)
            variablecollenoffset = staticoffset + rowinfo.staticlength + 2 + lenofnullbitmap + 2

        bitpos = 0
        numberofbitcol = 0

        for schema in schemlist:
            if schema.kindofcol == Columntype.STATIC_COLUMN:
                columnlength = schema.colsize
                if schema.datatype == 'bit':
                    if numberofbitcol % 8 == 0:
                        bitpos = staticoffset
                        columnbuff = buf[bitpos:bitpos + columnlength]
                        staticoffset += columnlength
                    else:
                        columnbuff = buf[bitpos:bitpos + columnlength]
                    numberofbitcol += 1
                else:
                    if (columnlength + staticoffset) > recordlen:
                        break

                    if columnlength < self.mssql.pagesize:
                        columnbuff = buf[staticoffset: staticoffset + columnlength]
                    else:
                        break
                    staticoffset += columnlength
            elif schema.kindofcol == Columntype.VARIABLE_COLUMN:
                variablecollen = unpack('<H', buf[variablecollenoffset:variablecollenoffset + 0x02])[0]

                if variablecollen > 0x8000:
                    variablecollen -= 0x8000
                columnlength = variablecollen - variableoffset

                variablecollenoffset += 2
                if (variableoffset < self.mssql.pagesize) and (variablecollen < self.mssql.pagesize):
                    if (variableoffset + columnlength <= recordlen) and (columnlength < self.mssql.pagesize):
                        columnbuff = buf[variableoffset:variableoffset + columnlength]
                        variableoffset += columnlength

            # add nullbit check

            if schema.colname == 'id':
                tableinfo.tobjectid = unpack('<I', columnbuff[:4])[0]
            elif schema.colname == 'name':
                tableinfo.tablename = columnbuff.decode('utf-16')
            elif schema.colname == 'type':
                tabletype = columnbuff.decode('utf-8')[0]
            elif schema.colname == 'intprop':
                tableinfo.numofcolumns = unpack('<I', columnbuff[:4])[0]

            del columnbuff

        if tableinfo.tobjectid != 0 and tableinfo.tablename != '' and tabletype == 'U':
            return True
        else:
            return False

    def _parseIndexInfoRecord(self, buf, recordlen, schemlist, rowinfo, objectid, indexcolumnid, columnid):
        lenofnullbitmap = math.ceil(rowinfo.numoftotalcol / 8)
        offsetoftotalnumofcol = unpack('<H', buf[0x02: 0x04])[0]
        totalnumofcol = unpack('<H', buf[offsetoftotalnumofcol:offsetoftotalnumofcol + 0x02])[0]

        if rowinfo.numoftotalcol != totalnumofcol:
            return False

        staticoffset = 1 + 1 + 2  # statusBit A + statusBit B + OffsetOfTotalNumOfCol

        if rowinfo.numofvariablecol != 0:
            variableoffset = staticoffset + rowinfo.staticlength + 2 + lenofnullbitmap
            numofvariablecol = unpack('<H', buf[variableoffset: variableoffset + 0x02])[0]
            variableoffset += 2
            variableoffset += (2 * numofvariablecol)
            variablecollenoffset = staticoffset + rowinfo.staticlength + 2 + lenofnullbitmap + 2

        bitpos = 0
        numberofbitcol = 0

        for schema in schemlist:
            if schema.kindofcol == Columntype.STATIC_COLUMN:
                columnlength = schema.colsize
                if schema.datatype == 'bit':
                    if numberofbitcol % 8 == 0:
                        bitpos = staticoffset
                        columnbuff = buf[bitpos:bitpos + columnlength]
                        staticoffset += columnlength
                    else:
                        columnbuff = buf[bitpos:bitpos + columnlength]
                    numberofbitcol += 1
                else:
                    if (columnlength + staticoffset) > recordlen:
                        break

                    if columnlength < self.mssql.pagesize:
                        columnbuff = buf[staticoffset: staticoffset + columnlength]
                    else:
                        break
                    staticoffset += columnlength
            elif schema.kindofcol == Columntype.VARIABLE_COLUMN:
                variablecollen = unpack('<H', buf[variablecollenoffset:variablecollenoffset + 0x02])[0]

                if variablecollen > 0x8000:
                    variablecollen -= 0x8000
                columnlength = variablecollen - variableoffset

                variablecollenoffset += 2
                if (variableoffset < self.mssql.pagesize) and (variablecollen < self.mssql.pagesize):
                    if (variableoffset + columnlength <= recordlen) and (columnlength < self.mssql.pagesize):
                        columnbuff = buf[variableoffset:variableoffset + columnlength]
                        variableoffset += columnlength

            # add nullbit check
            if schema.colname == 'idmajor':
                tboId = unpack('<I', columnbuff[:4])[0]
            elif schema.colname == 'status':
                tbStatus = unpack('<I', columnbuff[:4])[0]
            elif schema.colname == 'subid':
                indexcolumnid = unpack('<I', columnbuff[:4])[0]
            elif schema.colname == 'intprop':
                columnid = unpack('<I', columnbuff[:4])[0]

            del columnbuff

        if (tboId != objectid) or ~(tbStatus & 2):
            return False
        else:
            return True

    def _changeOrdinal(self, schemlist, indexcolumnid, columnid, colname, objectid):
        table_schemes = self.userschemesmap[objectid]

        for schema in table_schemes:
            if colname != '':
                if schema.colname == colname:
                    tmpOrdinal = schema.colorder
                    schema.colorder = indexcolumnid
            else:
                if schema.colorder == columnid:
                    tmpOrdinal = columnid
                    schema.colorder = indexcolumnid

        for schema in table_schemes:
            if (schema.colorder < tmpOrdinal) and (schema.colData > indexcolumnid):
                schema.colorder += 1

    def _parseObjectInfoRecord(self, buf, recordlen, schemlist, rowinfo, objectid):
        lenofnullbitmap = math.ceil(rowinfo.numoftotalcol / 8)
        offsetoftotalnumofcol = unpack('<H', buf[0x02: 0x04])[0]
        totalnumofcol = unpack('<H', buf[offsetoftotalnumofcol:offsetoftotalnumofcol + 0x02])[0]
        partitionid = 0

        if rowinfo.numoftotalcol != totalnumofcol:
            return False

        staticoffset = 1 + 1 + 2  # statusBit A + statusBit B + OffsetOfTotalNumOfCol

        if rowinfo.numofvariablecol != 0:
            variableoffset = staticoffset + rowinfo.staticlength + 2 + lenofnullbitmap
            numofvariablecol = unpack('<H', buf[variableoffset: variableoffset + 0x02])[0]
            variableoffset += 2
            variableoffset += (2 * numofvariablecol)
            variablecollenoffset = staticoffset + rowinfo.staticlength + 2 + lenofnullbitmap + 2

        bitpos = 0
        numberofbitcol = 0

        for schema in schemlist:
            if schema.kindofcol == Columntype.STATIC_COLUMN:
                columnlength = schema.colsize
                if schema.datatype == 'bit':
                    if numberofbitcol % 8 == 0:
                        bitpos = staticoffset
                        columnbuff = buf[bitpos:bitpos + columnlength]
                        staticoffset += columnlength
                    else:
                        columnbuff = buf[bitpos:bitpos + columnlength]
                    numberofbitcol += 1
                else:
                    if (columnlength + staticoffset) > recordlen:
                        break

                    if columnlength < self.mssql.pagesize:
                        columnbuff = buf[staticoffset: staticoffset + columnlength]
                    else:
                        break
                    staticoffset += columnlength
            elif schema.kindofcol == Columntype.VARIABLE_COLUMN:
                variablecollen = unpack('<H', buf[variablecollenoffset:variablecollenoffset + 0x02])[0]

                if variablecollen > 0x8000:
                    variablecollen -= 0x8000
                columnlength = variablecollen - variableoffset

                variablecollenoffset += 2
                if (variableoffset < self.mssql.pagesize) and (variablecollen < self.mssql.pagesize):
                    if (variableoffset + columnlength <= recordlen) and (columnlength < self.mssql.pagesize):
                        columnbuff = buf[variableoffset:variableoffset + columnlength]
                        variableoffset += columnlength

            # add nullbit check

            if schema.colname == 'rowsetid':
                partitionid = unpack('<Q', columnbuff[:8])[0]
            elif schema.colname == 'idmajor':
                tboId = unpack('<I', columnbuff[:4])[0]

            # del columnbuff

        if (partitionid == 0) or (tboId != objectid):
            return 0
        else:
            return partitionid

    def _searchSysallocunits(self, tableinfo):
        sysallocunits_page = defaultdict(list, {k: v for k, v in self.pages.items() if v == 0x07})
        sysallocunits_schemes = self.systemschemesmap[0x07]
        sysallocunits_schemes = sorted(sysallocunits_schemes, key=lambda SchemeInfo: SchemeInfo.colorder)

        rowinfo = RowInfo()

        if len(sysallocunits_schemes) == 0:
            return False

        for schema in sysallocunits_schemes:
            self._tableSchemeAnalyzer(schema, rowinfo)

        if len(sysallocunits_schemes) != rowinfo.numoftotalcol:
            return False

        for k, v in sysallocunits_page.items():
            buf = self.mssql.read(k * self.mssql.pagesize, self.mssql.pagesize)
            pageheader = self.mssql.getPageHeader(buf)

            if pageheader.flagbits & 0x100:
                self._tornbits(buf)

            rowoffsetarray = sorted(self.mssql.getRowOffsetArray(buf, pageheader))

            recordlen = rowoffsetarray[1:] + [self.mssql.pagesize - len(rowoffsetarray) * 2]
            for offset, length in zip(rowoffsetarray, recordlen):
                allocationid = self._parseAllocUnitInfoRecord(buf[offset:], length - offset, sysallocunits_schemes,
                                                              rowinfo, tableinfo)
                if allocationid != 0:
                    tableinfo.pobjectid = ((allocationid) - ((allocationid >> 48) << 48)) >> 16

        return True

    def _parseAllocUnitInfoRecord(self, buf, recordlen, schemlist, rowinfo, tableinfo):
        lenofnullbitmap = math.ceil(rowinfo.numoftotalcol / 8)
        offsetoftotalnumofcol = unpack('<H', buf[0x02: 0x04])[0]
        totalnumofcol = unpack('<H', buf[offsetoftotalnumofcol:offsetoftotalnumofcol + 0x02])[0]
        allocationid = 0

        if rowinfo.numoftotalcol != totalnumofcol:
            return False

        staticoffset = 1 + 1 + 2  # statusBit A + statusBit B + OffsetOfTotalNumOfCol

        if rowinfo.numofvariablecol != 0:
            variableoffset = staticoffset + rowinfo.staticlength + 2 + lenofnullbitmap
            numofvariablecol = unpack('<H', buf[variableoffset: variableoffset + 0x02])[0]
            variableoffset += 2
            variableoffset += (2 * numofvariablecol)
            variablecollenoffset = staticoffset + rowinfo.staticlength + 2 + lenofnullbitmap + 2

        bitpos = 0
        numberofbitcol = 0

        for schema in schemlist:
            if schema.kindofcol == Columntype.STATIC_COLUMN:
                columnlength = schema.colsize
                if schema.datatype == 'bit':
                    if numberofbitcol % 8 == 0:
                        bitpos = staticoffset
                        columnbuff = buf[bitpos:bitpos + columnlength]
                        staticoffset += columnlength
                    else:
                        columnbuff = buf[bitpos:bitpos + columnlength]
                    numberofbitcol += 1
                else:
                    if (columnlength + staticoffset) > recordlen:
                        break

                    if columnlength < self.mssql.pagesize:
                        columnbuff = buf[staticoffset: staticoffset + columnlength]
                    else:
                        break
                    staticoffset += columnlength
            elif schema.kindofcol == Columntype.VARIABLE_COLUMN:
                variablecollen = unpack('<H', buf[variablecollenoffset:variablecollenoffset + 0x02])[0]

                if variablecollen > 0x8000:
                    variablecollen -= 0x8000
                columnlength = variablecollen - variableoffset

                variablecollenoffset += 2
                if (variableoffset < self.mssql.pagesize) and (variablecollen < self.mssql.pagesize):
                    if (variableoffset + columnlength <= recordlen) and (columnlength < self.mssql.pagesize):
                        columnbuff = buf[variableoffset:variableoffset + columnlength]
                        variableoffset += columnlength

            # add nullbit check

            if schema.colname == 'ownerid':
                pid = unpack('<Q', columnbuff[:8])[0]
            elif schema.colname == 'type':
                flag = columnbuff[0]
            elif schema.colname == 'auid':
                allocationid = unpack('<Q', columnbuff[:8])[0]

            del columnbuff

        if (pid == 0) or (pid != tableinfo.partitionid) or (flag != 0x01):
            return 0
        else:
            return allocationid

    def _tornbits(self, buf):
        tornbit = unpack('<I', buf[0x3c:0x40])[0]

        tornbit = tornbit >> 2

        offset = 0x3ff

        while offset < self.mssql.pagesize:
            changeData = tornbit & 0x03
            buf[offset] = buf[offset] & 0xfc
            buf[offset] = buf[offset] | changeData
            tornbit = tornbit >> 2
            offset += 0x200

    def _calcRecordLen(self, buf, rowinfo):
        # record idetification exception code is needed
        isAlive = True
        if buf[0] != 0x10 and buf[0] != 0x30 and buf[0] != 0x3c and buf[0] != 0x1c:
            return 0, isAlive

        if buf[0] & 0x0C == 0x0C:
            isAlive = False

        offsetOftotalNumOfCol = unpack('<H', buf[0x2:0x4])[0]

        totalNumOfCol = unpack('<H', buf[offsetOftotalNumOfCol:offsetOftotalNumOfCol + 2])[0]

        if totalNumOfCol != rowinfo.numoftotalcol:
            return 0, isAlive

        lenOfNullBitmap = math.ceil(rowinfo.numoftotalcol / 8)

        recordLen = 0

        recordLen += 4  # StatusBit A(1 byte) + StatusBit B(1 byte) + Offset of number of column(2 bytes)
        recordLen += rowinfo.staticlength  # Static column length
        recordLen += (2 + lenOfNullBitmap)

        if (rowinfo.numofvariablecol == 0 or buf[0] == 0x10 or buf[0] == 0x1c):
            return recordLen, isAlive
        else:
            numOfVariableCol = unpack('<H', buf[recordLen:recordLen + 2])[0]
            recordLen = unpack('<H', buf[recordLen + numOfVariableCol * 2:recordLen + (numOfVariableCol + 1) * 2])[0]
            if recordLen > 0x8000:
                recordLen -= 0x8000

            return recordLen, isAlive

    def _scanForUnallocatedArea(self, buf, currentoffset, lenofunalloc, rowinfo, tablename, schemlist):
        if currentoffset + lenofunalloc > self.mssql.pagesize:
            return False

        recordsLen = 0  # 미할당 영역에 복구 대상 레코드가 여러 개일 경우

        while recordsLen < lenofunalloc:
            # 복구
            # print("** Recovery from offset : " + str(currentoffset))
            recordLen, _ = self._calcRecordLen(buf[currentoffset + recordsLen:], rowinfo)  # 복구 대상 레코드 길이
            if recordsLen + recordLen > lenofunalloc or recordLen == 0:
                break
            query = self._parseUnallocatedRecord(buf[currentoffset + recordsLen:], recordLen, rowinfo, schemlist)

            query = "insert into " + tablename + " values (" + query + ")\n"
            self.of.write(query)
            recordsLen += recordLen

        return True

    def _parseUnallocatedRecord(self, buf, recordlen, rowinfo, schemlist):
        lenofnullbitmap = math.ceil(rowinfo.numoftotalcol / 8)
        offsetoftotalnumofcol = unpack('<H', buf[0x02:0x04])[0]
        totalnumofcol = unpack('<H', buf[offsetoftotalnumofcol:offsetoftotalnumofcol + 0x02])[0]

        if rowinfo.numoftotalcol != totalnumofcol:
            return False

        staticoffset = 1 + 1 + 2  # statusBit A + statusBit B + OffsetOfTotalNumberOfCol

        if rowinfo.numoftotalcol != 0:
            variableoffset = staticoffset + rowinfo.staticlength + 2 + lenofnullbitmap
            numofvariablecol = unpack('<H', buf[variableoffset: variableoffset + 0x02])[0]
            variableoffset += 2
            variableoffset += (2 * numofvariablecol)
            variablecollenoffset = staticoffset + rowinfo.staticlength + 2 + lenofnullbitmap + 2

        bitpos = 0
        numberofbitcol = 0

        query = []
        isLob = False

        for schema in schemlist:
            if schema.kindofcol == Columntype.STATIC_COLUMN:
                columnlength = schema.colsize
                if schema.datatype == 'bit':
                    if numberofbitcol % 8 == 0:
                        bitpos = staticoffset
                        columnbuff = buf[bitpos:bitpos + columnlength]
                        staticoffset += columnlength
                    else:
                        columnbuff = buf[bitpos:bitpos + columnlength]
                    numberofbitcol += 1
                else:
                    if (columnlength + staticoffset) > recordlen:
                        break

                    if columnlength < self.mssql.pagesize:
                        columnbuff = buf[staticoffset: staticoffset + columnlength]
                    else:
                        break
                    staticoffset += columnlength
            elif schema.kindofcol == Columntype.VARIABLE_COLUMN:
                variablecollen = unpack('<H', buf[variablecollenoffset:variablecollenoffset + 0x02])[0]

                if variablecollen > 0x8000:
                    variablecollen -= 0x8000
                    isLob = True
                columnlength = variablecollen - variableoffset

                variablecollenoffset += 2
                if (variableoffset < self.mssql.pagesize) and (variablecollen < self.mssql.pagesize):
                    if (variableoffset + columnlength <= recordlen) and (columnlength < self.mssql.pagesize):
                        columnbuff = buf[variableoffset:variableoffset + columnlength]
                        variableoffset += columnlength

            output = self._decodeValue(columnbuff, columnlength, schema, numberofbitcol, isLob)
            query.append(output)
            isLob = False

        query_str = ','.join(query)

        return query_str

    def _decodeValue(self, buff, length, schema, numberofbitcol, isLob):
        output = ''
        if schema.datatype == "tinyint":
            output = str(unpack('<B', buff)[0])
        elif schema.datatype == "smallint":
            output = str(unpack('<H', buff)[0])
        elif schema.datatype == "int":
            output = "'" + str(unpack('<I', buff)[0]) + "'"
        elif schema.datatype == "bigint":
            output = str(unpack('<Q', buff)[0])
        elif schema.datatype == "real":
            output = str(unpack('<f', buff)[0])
        elif schema.datatype == "float":
            output = str(unpack('<d', buff)[0])
        elif schema.datatype in ("datetime", "smalldatetime", "money", "smallmoney"):
            output = "cast(0x" + binascii.b2a_hex(bytes(reversed(buff))).decode('utf8') + " as " + schema.datatype + ")"
        elif schema.datatype == "date":
            output = "cast(0x" + binascii.b2a_hex(buff).decode('utf8') + " as date)"
        elif "time" in schema.datatype:
            output = "cast(0x%02x" % schema.precisionoftime + binascii.b2a_hex(buff).decode('utf8') + " as time)"
        elif "numeric" in schema.datatype or "decimal" in schema.datatype:
            output = "convert(" + schema.datatype + ",0x%02x%02x0001" % (
            schema.precisionofnumeric, schema.scaleofnumeric) + \
                     binascii.b2a_hex(buff[1:]).decode('utf8') + ")"
        elif schema.datatype == "char":
            output = "'" + buff.decode('utf8') + "'"
        elif schema.datatype == "varchar":
            if isLob:  # Large object
                output = "'" + self._parseLobRecord(buff).decode('utf8') + "'"
            else:
                output = "'" + buff.decode('utf8') + "'"
        elif schema.datatype == "nchar":
            output = "'" + buff.decode('utf16') + "'"  # xml, text, ntext, image
        elif schema.datatype == "nvarchar":
            if isLob:  # Large object
                output = "'" + self._parseLobRecord(buff).decode('utf16') + "'"
            else:
                output = "'" + buff.decode(
                    'utf16') + "'"  # hierarchyid, geometry, geography, uniqueidentifier, sql_variant
        elif schema.datatype == "binary":
            output = '0x' + (binascii.b2a_hex(buff)).decode('utf8')
        elif schema.datatype == "varbinary":
            if isLob:  # 8bytes => lob header (type(2 byptes) / level(1 byte) / unused(1 byte) / updateseq(4 bytes))
                output = '0x' + (binascii.b2a_hex(self._parseLobRecord(buff))).decode('utf8')
            else:
                output = '0x' + (binascii.b2a_hex(buff)).decode('utf8')
        elif schema.datatype in ("text", "ntext", "image"):
            lobpos = set()
            byte_output = b''
            timestamp = unpack('<I', buff[0:4])[0]
            pageId = unpack('<I', buff[0x08:0x0C])[0]
            fileId = unpack('<H', buff[0x0C:0x0E])[0]
            slotNumber = unpack('<H', buff[0x0E:0x10])[0]
            rowid = RowId(fileId, pageId, slotNumber)
            self._reconstructLOBData(0, rowid, timestamp, lobpos)

            lobpos = sorted(lobpos)
            for _, rowid, row_offset in lobpos:
                lob_buf = self.mssql.read(rowid.pageId * self.mssql.pagesize, self.mssql.pagesize)
                pageheader = self.mssql.getPageHeader(lob_buf)

                if pageheader.flagbits & 0x100:
                    self._tornbits(lob_buf)
                if lob_buf[1] == 0x03 or lob_buf[1] == 0x04:
                    recordLen = unpack('<H', lob_buf[row_offset + 0x02:row_offset + 0x04])[0]
                    byte_output += lob_buf[row_offset + 0x0E:row_offset + recordLen]

            if schema.datatype == "text":
                output = "'" + byte_output.decode('utf8') + "'"
            elif schema.datatype == "ntext":
                output = "'" + byte_output.decode('utf16') + "'"
            else:
                output = '0x' + (binascii.b2a_hex(byte_output)).decode('utf8')

        return output

    def _parseLobRecord(self, buff):
        byte_output = b''
        lobinfo = LobInfo()
        lobinfo.timestamp = unpack('<I', buff[0x06:0x0A])[0]
        offset = 0x0C
        while offset < len(buff):
            lobpos = set()
            length = unpack('<I', buff[offset:offset + 0x04])[0]
            pageId = unpack('<I', buff[offset + 0x04:offset + 0x08])[0]
            fileId = unpack('<H', buff[offset + 0x08:offset + 0x0A])[0]
            slotNumber = unpack('<H', buff[offset + 0x0A:offset + 0x0C])[0]
            rowid = RowId(fileId, pageId, slotNumber)
            if buff[0] & 0x02 != 0:
                self._reconstructLOBData(length, rowid, lobinfo.timestamp, lobpos, 0, length)
            else:
                self._reconstructLOBData(length, rowid, lobinfo.timestamp, lobpos)
            offset += 0x0C

            lobpos = sorted(lobpos)
            for _, rowid, row_offset in lobpos:
                lob_buf = self.mssql.read(rowid.pageId * self.mssql.pagesize, self.mssql.pagesize)
                pageheader = self.mssql.getPageHeader(lob_buf)

                if pageheader.flagbits & 0x100:
                    self._tornbits(lob_buf)
                if lob_buf[1] == 0x03 or lob_buf[1] == 0x04:
                    recordLen = unpack('<H', lob_buf[row_offset + 0x02:row_offset + 0x04])[0]
                    byte_output += lob_buf[row_offset + 0x0E:row_offset + recordLen]

        return byte_output

    def _reconstructLOBData(self, length, rowid, timestamp, lobpos, offset=0, size=0):
        # row-overflow
        lob_buf = self.mssql.read(rowid.pageId * self.mssql.pagesize, self.mssql.pagesize)
        pageheader = self.mssql.getPageHeader(lob_buf)

        if pageheader.flagbits & 0x100:
            self._tornbits(lob_buf)
        if lob_buf[1] == 0x03 or lob_buf[1] == 0x04:
            rowoffsetarray = self.mssql.getRowOffsetArray(lob_buf, pageheader)
            if len(rowoffsetarray) > rowid.slotNumber:
                row_offset = rowoffsetarray[rowid.slotNumber]
            elif len(rowoffsetarray) != 0:
                row_offset = rowoffsetarray[0]
            else:
                row_offset = 0x60

            recordLen = unpack('<H', lob_buf[row_offset + 0x02:row_offset + 0x04])[0]
            blob_timestamp = unpack('<I', lob_buf[row_offset + 0x04:row_offset + 0x08])[0]
            lob_type = unpack('<H', lob_buf[row_offset + 0x0C:row_offset + 0x0E])[0]
            if blob_timestamp == timestamp:  # allocated data
                if lob_type == 0:
                    pass
                elif lob_type == 2:  # internal
                    maxlinks = unpack('<H', lob_buf[row_offset + 0x0E:row_offset + 0x10])[0]
                    curlinks = unpack('<H', lob_buf[row_offset + 0x10:row_offset + 0x12])[0]
                    level = unpack('<H', lob_buf[row_offset + 0x12:row_offset + 0x14])[0]
                    link = 0
                    prv_offset = 0
                    while link < curlinks:
                        blob_offset = \
                        unpack('<I', lob_buf[row_offset + 0x14 + 0x10 * link:row_offset + 0x14 + 0x10 * link + 0x04])[0]
                        pageId = unpack('<I', lob_buf[
                                              row_offset + 0x14 + 0x10 * link + 0x08:row_offset + 0x14 + 0x10 * link + 0x0C])[
                            0]
                        fileId = unpack('<H', lob_buf[
                                              row_offset + 0x14 + 0x10 * link + 0x0C:row_offset + 0x14 + 0x10 * link + 0x0E])[
                            0]
                        slotNumber = unpack('<H', lob_buf[
                                                  row_offset + 0x14 + 0x10 * link + 0x0E:row_offset + 0x14 + 0x10 * link + 0x10])[
                            0]
                        blob_rowid = RowId(fileId, pageId, slotNumber)
                        self._reconstructLOBData(length, blob_rowid, timestamp, lobpos, blob_offset,
                                                 blob_offset - prv_offset)
                        prv_offset = blob_offset
                        link += 1
                elif lob_type == 3:  # data
                    lobpos.add((offset, rowid, row_offset))
                elif lob_type == 5:
                    maxlinks = unpack('<H', lob_buf[row_offset + 0x0E:row_offset + 0x10])[0]
                    curlinks = unpack('<H', lob_buf[row_offset + 0x10:row_offset + 0x12])[0]
                    level = unpack('<H', lob_buf[row_offset + 0x12:row_offset + 0x14])[0]
                    link = 0
                    prv_offset = 0
                    while link < curlinks:
                        blob_offset = \
                        unpack('<I', lob_buf[row_offset + 0x18 + 0x0C * link:row_offset + 0x18 + 0x0C * link + 0x04])[0]
                        pageId = unpack('<I', lob_buf[
                                              row_offset + 0x18 + 0x0C * link + 0x04:row_offset + 0x18 + 0x0C * link + 0x08])[
                            0]
                        fileId = unpack('<H', lob_buf[
                                              row_offset + 0x18 + 0x0C * link + 0x08:row_offset + 0x18 + 0x0C * link + 0x0A])[
                            0]
                        slotNumber = unpack('<H', lob_buf[
                                                  row_offset + 0x18 + 0x0C * link + 0x0A:row_offset + 0x18 + 0x0C * link + 0x0C])[
                            0]
                        blob_rowid = RowId(fileId, pageId, slotNumber)
                        self._reconstructLOBData(length, blob_rowid, timestamp, lobpos, blob_offset,
                                                 blob_offset - prv_offset)
                        prv_offset = blob_offset
                        link += 1
            else:  # unallocated data
                row_offset = 0x60
                while row_offset < self.mssql.pagesize:
                    recordLen = unpack('<H', lob_buf[row_offset + 0x02:row_offset + 0x04])[0]
                    blob_timestamp = unpack('<I', lob_buf[row_offset + 0x04:row_offset + 0x08])[0]
                    lob_type = unpack('<H', lob_buf[row_offset + 0x0C:row_offset + 0x0E])[0]
                    if blob_timestamp != timestamp:
                        if recordLen != 0:
                            row_offset += recordLen
                            continue
                        else:
                            break
                    if recordLen - 0xE != 0:
                        if lob_type == 0 or lob_type == 3:
                            lobpos.add((offset, rowid, row_offset))
                        elif lob_type == 5:
                            maxlinks = unpack('<H', lob_buf[row_offset + 0x0E:row_offset + 0x10])[0]
                            curlinks = unpack('<H', lob_buf[row_offset + 0x10:row_offset + 0x12])[0]
                            level = unpack('<H', lob_buf[row_offset + 0x12:row_offset + 0x14])[0]
                            link = 0
                            prv_offset = 0
                            while link < curlinks:
                                blob_offset = unpack('<I', lob_buf[
                                                           row_offset + 0x18 + 0x0C * link:row_offset + 0x18 + 0x0C * link + 0x04])[
                                    0]
                                pageId = unpack('<I', lob_buf[
                                                      row_offset + 0x18 + 0x0C * link + 0x04:row_offset + 0x18 + 0x0C * link + 0x08])[
                                    0]
                                fileId = unpack('<H', lob_buf[
                                                      row_offset + 0x18 + 0x0C * link + 0x08:row_offset + 0x18 + 0x0C * link + 0x0A])[
                                    0]
                                slotNumber = unpack('<H', lob_buf[
                                                          row_offset + 0x18 + 0x0C * link + 0x0A:row_offset + 0x18 + 0x0C * link + 0x0C])[
                                    0]
                                blob_rowid = RowId(fileId, pageId, slotNumber)
                                self._reconstructLOBData(length, blob_rowid, timestamp, lobpos, blob_offset,
                                                         blob_offset - prv_offset)
                                prv_offset = blob_offset
                                link += 1
                        break
                    else:
                        if recordLen != 0:
                            row_offset += recordLen
                        else:
                            break

        return True
