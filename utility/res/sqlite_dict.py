TABLE_INFO = {
    "case_info": {
        "case_id": "VARCHAR PRIMARY KEY",
        "case_name": "TEXT",
        "administrator": "TEXT",
        "create_date": "DATETIME",
        "description": "TEXT"
    },

    "investigator": {
        "id": "TEXT PRIMARY KEY",
        "name": "TEXT",
        "password": "TEXT",
        "acl": "TEXT"
    },

    "evidence_info": {
        "evd_id": "VARCHAR PRIMARY KEY",
        "evd_name": "TEXT",
        "evd_path": "TEXT",
        "tmp_path": "TEXT",
        "case_id": "VARCHAR",
        "main_type": "TEXT",
        "sub_type": "TEXT",
        "timezone": "TEXT",
        "acquired_date": "DATETIME",
        "md5": "TEXT",
        "sha1": "TEXT",
        "sha3": "TEXT",
        "process_state": "INTEGER"
    },

    "partition_info": {
        "par_id": "VARCHAR PRIMARY KEY",
        "par_name": "TEXT",
        "evd_id": "VARCHAR",
        "par_type": "TEXT",
        "sector_size": "INTEGER",
        "par_size": "BIGINT",
        "md5": "TEXT",
        "sha1": "TEXT",
        "sha3": "TEXT",
        "start_sector": "BIGINT"
    },

    "file_info": {
        "file_id": "BIGINT",
        "par_id": "VARCHAR",
        "inode": "TEXT",
        "name": "TEXT",
        "meta_seq": "BIGINT",
        "type": "INTEGER",
        "dir_type": "INTEGER",
        "meta_type": "INTEGER",
        "meta_flags": "INTEGER",
        "size": "BIGINT",
        "mtime": "BIGINT",
        "atime": "BIGINT",
        "ctime": "BIGINT",
        "etime": "BIGINT",
        "mtime_nano": "BIGINT",
        "atime_nano": "BIGINT",
        "ctime_nano": "BIGINT",
        "etime_nano": "BIGINT",
        "additional_mtime": "BIGINT",
        "additional_atime": "BIGINT",
        "additional_ctime": "BIGINT",
        "additional_etime": "BIGINT",
        "additional_mtime_nano": "BIGINT",
        "additional_atime_nano": "BIGINT",
        "additional_ctime_nano": "BIGINT",
        "additional_etime_nano": "BIGINT",
        "mode": "INTEGER",
        "uid": "INTEGER",
        "gid": "INTEGER",
        "md5": "TEXT",
        "sha1": "TEXT",
        "sha3": "TEXT",
        "parent_path": "TEXT",
        "extension": "TEXT",
        "parent_id": "BIGINT",
        "bookmark": "BOOLEAN",
        "ads": "INTEGER",
        "sig_type": "TEXT",
        "rds_existed": "TEXT"
    }
}

CREATE_HELPER = {
    "case_info": "CREATE TABLE case_info ("
                 "case_id VARCHAR(100) NOT NULL, "
                 "case_name TEXT NOT NULL, "
                 "administrator TEXT NOT NULL, "
                 "create_date DATETIME NOT NULL, "
                 "description TEXT, "
                 "PRIMARY KEY(case_id));",

    "investigator": "CREATE TABLE investigator ("
                    "id varchar(255) NOT NULL, "
                    "name varchar(100) NOT NULL, "
                    "password varchar(100) NOT NULL, "
                    "acl TEXT NULL, "
                    "PRIMARY KEY(id));",

    "evidence_info": "CREATE TABLE evidence_info ("
                     "evd_id VARCHAR(100) NOT NULL, "
                     "evd_name TEXT NOT NULL, "
                     "evd_path TEXT NOT NULL, "
                     "tmp_path TEXT NOT NULL, "
                     "case_id VARCHAR(100) NOT NULL, "
                     "main_type TEXT NOT NULL, "
                     "sub_type TEXT NOT NULL, "
                     "timezone TEXT NOT NULL, "
                     "acquired_date DATETIME, "
                     "md5 TEXT, "
                     "sha1 TEXT, "
                     "sha3 TEXT, "
                     "process_state INT(11) DEFAULT 0, "
                     "PRIMARY KEY(evd_id), "
                     "FOREIGN KEY(case_id) REFERENCES case_info(case_id));",

    "partition_info": "CREATE TABLE partition_info ("
                      "par_id VARCHAR(100) NOT NULL, "
                      "par_name TEXT NOT NULL, "
                      "evd_id VARCHAR(100) NOT NULL, "
                      "par_type TEXT NOT NULL, "
                      "sector_size INT(11) NOT NULL DEFAULT 0, "
                      "cluster_size INT(11) NOT NULL DEFAULT 0, "
                      "par_size BIGINT NOT NULL DEFAULT 0, "
                      "md5 TEXT, "
                      "sha1 TEXT, "
                      "sha3 TEXT, "
                      "start_sector BIGINT NOT NULL, "
                      "filesystem TEXT DEFAULT NULL, "
                      "par_label TEXT DEFAULT NULL, "
                      "PRIMARY KEY(par_id), "
                      "FOREIGN KEY(evd_id) REFERENCES evidence_info(evd_id));",

    "file_info": "CREATE TABLE file_info ("
                 "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
                 "file_id BIGINT NOT NULL, "
                 "par_id VARCHAR(100) NOT NULL, "
                 "inode TEXT, "
                 "name TEXT NOT NULL, "
                 "meta_seq BIGINT, "
                 "type INTEGER, "
                 "dir_type INTEGER, "
                 "meta_type INTEGER, "
                 "meta_flags INTEGER, "
                 "size BIGINT, "
                 "mtime BIGINT, "
                 "atime BIGINT, "
                 "ctime BIGINT, "
                 "etime BIGINT, "
                 "mtime_nano BIGINT, "
                 "atime_nano BIGINT, "
                 "ctime_nano BIGINT, "
                 "etime_nano BIGINT, "
                 "additional_mtime BIGINT, "
                 "additional_atime BIGINT, "
                 "additional_ctime BIGINT, "
                 "additional_etime BIGINT, "
                 "additional_mtime_nano BIGINT, "
                 "additional_atime_nano BIGINT, "
                 "additional_ctime_nano BIGINT, "
                 "additional_etime_nano BIGINT, "
                 "ads INTEGER, "
                 "mode INTEGER, "
                 "uid INTEGER, "
                 "gid INTEGER, "
                 "md5 TEXT, "
                 "sha1 TEXT, "
                 "sha3 TEXT, "
                 "parent_path TEXT, "
                 "extension TEXT, "
                 "parent_id BIGINT, "
                 "bookmark BOOLEAN, "
                 "sig_type TEXT, "
                 "rds_existed TEXT, "
                 "FOREIGN KEY(par_id) REFERENCES partition_info(par_id));"
}