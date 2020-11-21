#!/usr/bin/env python
# -*- coding: utf-8 -*-


class MappingDocuments(object):

    def __init__(self):
        self.work_dir = None
        self.download_path = None
        self.ole_path = None

        self.id = None
        self.case_id = None
        self.case_name = None
        self.evdnc_id = None
        self.evdnc_name = None
        self.doc_id = None
        self.doc_type = None
        self.doc_type_sub = None
        self.full_path = None
        self.path_with_ext = None
        self.name = None
        self.ext = None
        self.creation_time = None
        self.last_access_time = None
        self.last_written_time = None
        self.original_size = None
        self.sha1_hash = None
        self.parent_full_path = None
        self.is_fail = None
        self.fail_code = None
        self.exclude_user_id = None

        # metadata
        self.has_metadata = None
        self.title = None
        self.subject = None
        self.author = None
        self.tags = None
        self.explanation = None
        self.lastsavedby = None
        self.lastprintedtime = None
        self.createdtime = None
        self.lastsavedtime = None
        self.comment = None
        self.revisionnumber = None
        self.category = None
        self.manager = None
        self.company = None
        self.programname = None
        self.totaltime = None
        self.creator = None
        self.trapped = None

        # content
        self.has_content = None
        self.content = None
        self.content_size = None
        self.is_damaged = None
        self.has_exif = None

        # MFT
        self.mft_st_created_time = None
        self.mft_st_last_modified_time = None
        self.mft_st_last_accessed_time = None
        self.mft_st_entry_modified_time = None
        self.mft_fn_created_time = None
        self.mft_fn_last_modified_time = None
        self.mft_fn_last_accessed_time = None
        self.mft_fn_entry_modified_time = None

        self.is_downloaded = None
        self.is_copied = None

