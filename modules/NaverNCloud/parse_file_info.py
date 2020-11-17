import sqlite3
import datetime

# Convert Windows Filetime[xxxxxxxx:xxxxxxxx] to Datetime
# Windows Filetime 을 Datetime으로 변환
def convert_filetime(dwLowDateTime, dwHighDateTime):
    date = datetime.datetime(1601, 1, 1, 0, 0, 0)
    temp_time = dwHighDateTime
    temp_time <<= 32
    temp_time |= dwLowDateTime
    return date + datetime.timedelta(microseconds=temp_time / 10)

# Convert decimal to hex
# 10진수를 16진수로 변환
def decimal_to_hex(num):
    # map for decimal to hexa, 0-9 are
    # straightforward, alphabets a-f used
    # for 10 to 15.
    m = dict.fromkeys(range(16), 0)

    digit = ord('0')
    c = ord('a')

    for i in range(16):
        if (i < 10):
            m[i] = chr(digit)
            digit += 1
        else:
            m[i] = chr(c)
            c += 1

    # string to be returned
    res = ""

    # check if num is 0 and directly return "0"
    if (not num):
        return "0"

        # if num > 0, use normal technique as
    # discussed in other post
    if (num > 0):
        while (num):
            res = m[num % 16] + res
            num //= 16

    # if num < 0, we need to use the elaborated
    # trick above, lets see this
    else:
        # store num in a u_int, size of u_it is greater,
        # it will be positive since msb is 0
        n = num + 2 ** 32

        # use the same remainder technique.
        while (n):
            res = m[n % 16] + res
            n //= 16

    return res

# Connect Database (TODO: Search location)
# conn = sqlite3.connect(r"C:\Users\user\AppData\Local\Naver\NaverNDrive\cso14\SyncLog\ODSyncLog.db")

#
def parse_file_infomation(path):
    with sqlite3.connect(path) as conn:

        cursor = conn.cursor()

        # Query table of user
        # 사용자 계정의 테이블 정보 조회
        # tb_file_info : user's table name information
        # sync_user_table_name : 사용자 계정의 테이블 이름이 담길 변수
        cursor.execute("SELECT tb_file_info FROM tb_sync_conf_info;")
        for table_name in cursor.fetchone():
            sync_user_table_name = table_name

        # Query file information
        # 동기화된 파일 정보 조회
        # file_name : whole file path
        # file_time : file 수정한 날짜/시간 (TODO: CHECK) / Timestamp format : Windows Filetime [xxxxxxxx:xxxxxxxx] 뒤에 소수점 나오는 건 뭐지
        # file_size : file size (byte)
        # dir_flag : A value of directory is 1, or 0
        cursor.execute("SELECT file_name, file_time, file_size FROM " + sync_user_table_name + " WHERE dir_flag == 0;")

        naverncloud_file_info = []

        # 실제 테이블의 컬럼 명
        # row[0] : file_name
        # row[1] : file_time
        # row[2] : file_size
        #
        # file_time 형태 : Windows Filetime [xxxxxxxx:xxxxxxxx]
        # divide_windows_filetime : ':' 기준으로 file_time의 앞과 뒤 분리
        for row in cursor.fetchall():
            sync_user_table_windows_filetime = row[1]

            divide_windows_filetime = str(sync_user_table_windows_filetime).split(':')

            # 분리된 file_time의 앞부분이 양수일 경우
            if int(divide_windows_filetime[0]) > 0:
                sync_user_table_datetime = convert_filetime(int(divide_windows_filetime[0]), int(divide_windows_filetime[1]))
                # print(str(row[0]) + " | " + str(row[2]) + " | " + str(sync_user_table_datetime))
                db_file_info = (str(row[0]), str(row[2]), str(sync_user_table_datetime))
                naverncloud_file_info.append(db_file_info)


            # 분리된 file_time의 앞부분이 음수일 경우
            # 음수의 10진수를 양수의 10진수로 변환
            elif int(divide_windows_filetime[0]) < 0:
                # decimal_to_hex 함수를 통해 음수의 10진수를 16진수로 변환
                convert_hex = decimal_to_hex(int(divide_windows_filetime[0]))
                # 변환된 16진수를 다시 10진수로 변환
                convert_hex_to_decimal = int(convert_hex, 16)
                sync_user_table_datetime = convert_filetime(convert_hex_to_decimal, int(divide_windows_filetime[1]))
                # print(str(row[0]) + " | " + str(row[2]) + " | " + str(sync_user_table_datetime))
                db_file_info = (str(row[0]), str(row[2]), str(sync_user_table_datetime))
                naverncloud_file_info.append(db_file_info)

        return naverncloud_file_info
