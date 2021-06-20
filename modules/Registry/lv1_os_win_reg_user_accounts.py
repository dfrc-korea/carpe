from datetime import datetime, timedelta
import binascii

import modules.Registry.convert_util as cu
from modules import logger

class User_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    user_name = ''
    full_name = ''
    type_of_user = ''
    account_description = ''
    security_identifier = ''
    user_group = ''
    login_script = ''
    profile_path = ''
    account_created_time = ''
    last_login_time = ''
    last_password_change_time = ''
    last_incorrect_password_login_time = ''
    login_count = ''
    account_disabled = ''
    password_required = ''
    password_hint = ''
    lm_hash = ''
    ntlm_hash = ''
    backup_flag = ''
    source_location = []


def USERACCOUNTS(reg_sam, reg_software):
    user_list = []
    user_count = 0

    try:
        sam_users = reg_sam.find_key(r"SAM\Domains\Account\Users")
    except Exception as exception:
        logger.error(exception)

    try:
         #Local User 계정
        for sam_subkey in sam_users.subkeys():
            if sam_subkey.name() != 'Names':
                user_information = User_Information()
                user_list.append(user_information)
                user_list[user_count].source_location = []
                user_list[user_count].source_location.append('SAM-SAM/Domains/Account/Users')
                user_list[user_count].security_identifier = int(sam_subkey.name(), 16)
                user_list[user_count].type_of_user = 'Local User'
                for same_subkey_value in sam_subkey.values():
                    if same_subkey_value.name() == 'F':
                        user_list[user_count].last_login_time = (datetime(1601, 1, 1) + timedelta(microseconds=int(binascii.b2a_hex(same_subkey_value.data()[8:16][::-1]), 16)/10)).isoformat() + 'Z'
                        user_list[user_count].last_password_change_time = (datetime(1601, 1, 1) + timedelta(microseconds=int(binascii.b2a_hex(same_subkey_value.data()[24:32][::-1]), 16)/10)).isoformat() + 'Z'
                        user_list[user_count].last_incorrect_password_login_time = (datetime(1601, 1, 1) + timedelta(microseconds=int(binascii.b2a_hex(same_subkey_value.data()[40:48][::-1]), 16)/10)).isoformat() + 'Z'
                        if bin(same_subkey_value.data()[56])[-1] == '0':
                            # 0 : Enabled, pw_required - Yes
                            # 1: Disabled, pw_required - No
                            user_list[user_count].account_disabled = 0
                            user_list[user_count].password_required = 0
                        elif bin(same_subkey_value.data()[56])[-1] == '1':
                            user_list[user_count].account_disabled = 1
                            user_list[user_count].password_required = 1
                        user_list[user_count].login_count = int(binascii.b2a_hex(same_subkey_value.data()[66:67]), 16)
                    elif same_subkey_value.name() == 'V':
                        user_list[user_count].user_name = same_subkey_value.data()[204 + int(binascii.b2a_hex(same_subkey_value.data()[12:16][::-1]), 16):204 + int(binascii.b2a_hex(same_subkey_value.data()[12:16][::-1]), 16) + int(binascii.b2a_hex(same_subkey_value.data()[16:20][::-1]), 16)].decode('utf-16')
                        user_list[user_count].full_name = same_subkey_value.data()[204 + int(binascii.b2a_hex(same_subkey_value.data()[24:28][::-1]), 16):204 + int(binascii.b2a_hex(same_subkey_value.data()[24:28][::-1]), 16) + int(binascii.b2a_hex(same_subkey_value.data()[28:32][::-1]), 16)].decode('utf-16')
                        user_list[user_count].account_description = same_subkey_value.data()[204 + int(binascii.b2a_hex(same_subkey_value.data()[36:40][::-1]), 16):204 + int(binascii.b2a_hex(same_subkey_value.data()[36:40][::-1]), 16) + int(binascii.b2a_hex(same_subkey_value.data()[40:44][::-1]), 16)].decode('utf-16')
                        if user_list[user_count].password_required == 'Yes':
                            #user_list[user_count].ntlm_hash = str(binascii.b2a_hex(same_subkey_value.data()[204 + int(binascii.b2a_hex(same_subkey_value.data()[168:172][::-1]),16):204 + int(binascii.b2a_hex(same_subkey_value.data()[168:172][::-1]),16) + int(binascii.b2a_hex(same_subkey_value.data()[172:176][::-1]),16)]))[1:]
                            user_list[user_count].ntlm_hash = ''
                    elif same_subkey_value.name() == 'UserPasswordHint':
                        try:
                            user_list[user_count].password_hint = same_subkey_value.data().decode().replace('\x00', '')
                        except UnicodeDecodeError:
                            user_list[user_count].password_hint = ''
                user_count = user_count + 1
            else:
                for same_subkey_value in sam_subkey.subkeys():
                    for user in user_list:
                        if same_subkey_value.name() == user.user_name:
                           user.account_created_time = same_subkey_value.last_written_timestamp().isoformat()+'Z'

        # Built-In 계정
        user_key = reg_software.find_key(r"Microsoft\Windows NT\CurrentVersion\ProfileList")
        for user_subkey in user_key.subkeys():
            for user_subkey_value in user_subkey.values():
                if user_subkey_value.name() == 'ProfileImagePath':
                    if 'S-1-5-21' not in user_subkey.name():
                        user_information = User_Information()
                        user_list.append(user_information)
                        user_list[user_count].source_location = []
                        user_list[user_count].source_location.append('SOFTWARE-Microsoft/Windows NT/CurrentVersion/ProfileList')
                        user_list[user_count].security_identifier = user_subkey.name()
                        user_list[user_count].profile_path = user_subkey_value.data().replace('\\', '/').replace('\x00', '')
                        user_list[user_count].type_of_user = 'Built-in'
                        user_count = user_count + 1
                    else:
                        for user in user_list:
                            if user.security_identifier == int(user_subkey.name().split('-')[-1]):
                                user.security_identifier = user_subkey.name()
                                user.profile_path = user_subkey_value.data().replace('\\', '/').replace('\x00','')
                                break
                            else:
                                user_information = User_Information()
                                user_list.append(user_information)
                                user_list[user_count].source_location = []
                                user_list[user_count].source_location.append('SOFTWARE-Microsoft/Windows NT/CurrentVersion/ProfileList')
                                user_list[user_count].type_of_user = 'Domain User'
                                user_list[user_count].security_identifier = user_subkey.name()
                                user_list[user_count].user_name = (user_subkey_value.data().replace('\\', '/').replace('\x00', '')).split('/')[-1]
                                user_list[user_count].profile_path = user_subkey_value.data().replace('\\', '/').replace('\x00', '')
                                user_count = user_count + 1
                                break

        # LOGIN SCRIPT - Winlogon - 자동 로그인 스크립트 여부
        user_key = reg_software.find_key(r"Microsoft\Windows NT\CurrentVersion\Winlogon")
        for user_subkey in user_key.subkeys():
            if 'Auto' in user_subkey.name():
                for user in user_list:
                    for user_subkey_value in user_subkey.values():
                        if user_subkey_value.name() == 'DefaultUserName':
                            if user_subkey_value.data() == user.user_name:
                                user.login_script = 'Yes'
                                user.source_location.append('SOFTWARE-Microsoft/Windows NT/CurrentVersion/Winlogon')
    except Exception as exception:
        logger.error(exception)
    return user_list


