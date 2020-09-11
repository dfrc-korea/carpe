class FileAttributesFlag():
    """Flags as existent in the STANDARD_INFORMATION and FILE_NAME attributes

    https://msdn.microsoft.com/en-us/library/gg258117%28v=vs.85%29.aspx
    """

    ATTRIBUTES_TUPLE = (
        (0x1, 'READONLY'),
        (0x2, 'HIDDEN'),
        (0x4, 'SYSTEM'),
        (0x10, 'DIRECTORY'),
        (0x20, 'ARCHIVE'),
        (0x40, 'DEVICE'),
        (0x80, 'NORMAL'),
        (0x100, 'TEMPORARY'),
        (0x200, 'SPARSE_FILE'),
        (0x400, 'REPARSE_POINT'),
        (0x800, 'COMPRESSED'),
        (0x1000, 'OFFLINE'),
        (0x2000, 'NOT_CONTENT_INDEXED'),
        (0x4000, 'ENCRYPTED'),
        (0x8000, 'INTEGRITY_STREAM'),
        (0x10000, 'FILE_ATTRIBUTE_VIRTUAL'),
        (0X20000, 'NO_SCRUB_DATA'),
    )

    def __init__(self, flags):
        self.flags = flags

    def reason_list(self):
        return [second for first, second in self.ATTRIBUTES_TUPLE if self.flags & first]

    def is_read_only(self):
        return bool(self.flags & 0x1)

    def is_hidden(self):
        return bool(self.flags & 0x2)

    def is_system(self):
        return bool(self.flags & 0x4)

    def is_directory(self):
        return bool(self.flags & 0x10)

    def is_archive(self):
        return bool(self.flags & 0x20)

    def is_device(self):
        return bool(self.flags & 0x40)

    def is_normal(self):
        return bool(self.flags & 0x80)

    def is_temporary(self):
        return bool(self.flags & 0x100)

    def is_sparse_file(self):
        return bool(self.flags & 0x200)

    def is_reparse_point(self):
        return bool(self.flags & 0x400)

    def is_compressed(self):
        return bool(self.flags & 0x800)

    def is_offline(self):
        return bool(self.flags & 0x1000)

    def is_not_context_indexed(self):
        return bool(self.flags & 0x2000)

    def is_encrypted(self):
        return bool(self.flags & 0x4000)

    def is_integrity_stream(self):
        return bool(self.flags & 0x8000)

    def is_virtual(self):
        return bool(self.flags & 0x10000)

    def is_no_scrub_data(self):
        return bool(self.flags & 0x20000)