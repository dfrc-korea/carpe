import sqlite3


def main(par_id, input_db):
    con = sqlite3.connect(input_db)
    cur = con.cursor()

    cur.execute('select * from tsk_files')
    item = get_column_dict(cur)

    file_info = []
    id = 1
    for data in cur:
        for idx, i in enumerate(item):
            item[i] = data[idx]
        # id, file_id, par_id, inode, name, meta_seq, type, dir_type, meta_type, meta_flags, size, (m, a, c, e)time,
        # (m, a, c, e)time_nano, additional_(m, a, c, e)time, ads, mode, uid, gid, md5, sha1, sha3, parent_path,
        # extension, parent_id, bookmark, sig_type, rds_existed
        file_info.append([id, item['obj_id'], par_id, '', item['meta_seq'], item['type'], item['dir_type'],
                          item['meta_type'], item['meta_flags'], item['size'], item['mtime'], item['atime'],
                          item['ctime'], item['crtime'], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, item['mode'],
                          item['uid'], item['gid'], item['md5'], '', '', item['parent_path'], item['extension'],
                          0, 0, item['mime_type'], ''])
        id += 1

    return file_info

def get_column_dict(cur):
    return {desc[0]: None for desc in cur.description}
