from datetime import datetime, timedelta
import binascii
import struct
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


def USERACCOUNTS(reg_sam, reg_software, reg_system):
    user_list = []
    user_count = 0
    F_data = reg_sam.find_key(r"SAM\Domains\Account").value('F').data()
    V_data = None
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
                        if int(binascii.b2a_hex(same_subkey_value.data()[8:16][::-1]), 16) != 0:
                            user_list[user_count].last_login_time = (datetime(1601, 1, 1) + timedelta(microseconds=int(binascii.b2a_hex(same_subkey_value.data()[8:16][::-1]), 16)/10)).isoformat() + 'Z'
                        else:
                            user_list[user_count].last_login_time =''
                        if int(binascii.b2a_hex(same_subkey_value.data()[24:32][::-1]), 16) !=0:
                            user_list[user_count].last_password_change_time = (datetime(1601, 1, 1) + timedelta(microseconds=int(binascii.b2a_hex(same_subkey_value.data()[24:32][::-1]), 16)/10)).isoformat() + 'Z'
                        else:
                            user_list[user_count].last_password_change_time = ''
                        if int(binascii.b2a_hex(same_subkey_value.data()[40:48][::-1]), 16) !=0:
                            user_list[user_count].last_incorrect_password_login_time = (datetime(1601, 1, 1) + timedelta(microseconds=int(binascii.b2a_hex(same_subkey_value.data()[40:48][::-1]), 16)/10)).isoformat() + 'Z'
                        else:
                            user_list[user_count].last_incorrect_password_login_time = ''

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
                        V_data = same_subkey_value.data()
                        user_list[user_count].user_name = same_subkey_value.data()[204 + int(binascii.b2a_hex(same_subkey_value.data()[12:16][::-1]), 16):204 + int(binascii.b2a_hex(same_subkey_value.data()[12:16][::-1]), 16) + int(binascii.b2a_hex(same_subkey_value.data()[16:20][::-1]), 16)].decode('utf-16')
                        user_list[user_count].full_name = same_subkey_value.data()[204 + int(binascii.b2a_hex(same_subkey_value.data()[24:28][::-1]), 16):204 + int(binascii.b2a_hex(same_subkey_value.data()[24:28][::-1]), 16) + int(binascii.b2a_hex(same_subkey_value.data()[28:32][::-1]), 16)].decode('utf-16')
                        user_list[user_count].account_description = same_subkey_value.data()[204 + int(binascii.b2a_hex(same_subkey_value.data()[36:40][::-1]), 16):204 + int(binascii.b2a_hex(same_subkey_value.data()[36:40][::-1]), 16) + int(binascii.b2a_hex(same_subkey_value.data()[40:44][::-1]), 16)].decode('utf-16')
                        # if user_list[user_count].password_required == 0:
                        #     #user_list[user_count].ntlm_hash = str(binascii.b2a_hex(same_subkey_value.data()[204 + int(binascii.b2a_hex(same_subkey_value.data()[168:172][::-1]),16):204 + int(binascii.b2a_hex(same_subkey_value.data()[168:172][::-1]),16) + int(binascii.b2a_hex(same_subkey_value.data()[172:176][::-1]),16)]))[1:]
                        #     user_list[user_count].ntlm_hash = '1'
                    elif same_subkey_value.name() == 'UserPasswordHint':
                        try:
                            user_list[user_count].password_hint = same_subkey_value.data().decode().replace('\x00', '')
                        except UnicodeDecodeError:
                            user_list[user_count].password_hint = ''

                #ntml_hash_calculating
                if V_data != None:
                    user_list[user_count].ntlm_hash = get_ntlm(F_data,V_data,reg_system,int(sam_subkey.name(),16))
                    V_data = None
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


def get_ntlm(F_data,V_data,reg_system,RID):
    '''
    I interpreted and reused code from:
    https://github.com/rapid7/rex-powershell/blob/master/spec/file_fixtures/powerdump.ps1
    As of Win10 v1607 (>10.0.14393), the HASH encoding changed ...
    Accompanying blog post: http://www.insecurity.be/blog/2018/01/21/retrieving-ntlm-hashes-and-what-changed-technical-writeup/
    '''
    import hashlib


    #print('#################### By Tijl Deneut ###########################')
    #print('This scripts requires \'pycrypto\' to run (which requires http://aka.ms/vcpython27 on Windows)')
    #print('Let me guide you, you require psexec to extract stuff from the registry')
    #print('Please open the code to add the required data')
    ## What I need from you:
    # > User RID (e.g. for Administrator this is '500' or '1F4'), can be found with
    # wmic useraccount where name='Administrator' get sid
    #RID = 0x3e9
    # > RegistryHash for user ID above, can be found with cmd as System:
    # reg query "hklm\sam\sam\domains\account\users\000001F4" | find "V" > %temp%\adminenchash.txt && notepad %temp%\adminenchash.txt
    HexRegHash = V_data
    # > RegistryHash for encrypted System Key, can be found with cmd as System:
    # reg query "hklm\SAM\SAM\Domains\Account" /v F | find "BINARY" > %temp%\sysk.txt && notepad %temp%\sysk.txt
    HexRegSysk = F_data
    # > hBootKey Class Names, 4 values can be found with regedit as System:
    # 'HKLM\System\CurrentControlSet\Control\Lsa' as text and open with notepad
    #From_system = reg_system.find_key(r"ControlSet001\Control\Lsa")
    jd = reg_system.find_key(r"ControlSet001\Control\Lsa\JD").classname()
    skew1 = reg_system.find_key(r"ControlSet001\Control\Lsa\Skew1").classname()
    gbg = reg_system.find_key(r"ControlSet001\Control\Lsa\GBG").classname()
    data = reg_system.find_key(r"ControlSet001\Control\Lsa\Data").classname()
    # input('Press Enter to continue')

    import binascii, os
    from hashlib import md5
    os.system('cls' if os.name == 'nt' else 'clear')

    ## Data and key as hex string ('ABCDEFGH')
    def decryptRC4(data, key):
        data = binascii.unhexlify(data)
        key = binascii.unhexlify(key)
        S = list(range(256))
        j = 0
        for i in range(256):
            j = (j + S[i] + key[i % len(key)]) % 256
            S[i], S[j] = S[j], S[i]
        i = 0
        j = 0
        result = ''
        for char in data:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            # result += bytes((char ^ S[(S[i] + S[j]) % 256]),'utf-8')
            temp = hex(char ^ S[(S[i] + S[j]) % 256]).replace('0x', '')
            if len(temp) == 1:
                temp = '0' + temp
            result += temp

            # print(result.encode('utf-8'))
        return (result.encode('utf-8'))

    ## Data and key as hex string ('ABCDEFGH')
    def decryptAES(data, key, iv):
        try:
            from Crypto.Cipher import AES
        except:
            print('Error: Crypto not found, please run "pip install pycrypto" as admin')
        # data = binascii.unhexlify(data)
        #key = binascii.unhexlify(key)
        # iv = binascii.unhexlify(iv)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cipher.decrypt(data)

    ## Data and key as hex string ('ABCDEFGH')
    def decryptDES(data, key):
        try:
            from Crypto.Cipher import DES
        except:
            print('Error: Crypto not found, please run "pip install pycrypto" as admin')
        #data = binascii.unhexlify(data)
        key = binascii.unhexlify(key)
        cipher = DES.new(key, DES.MODE_ECB)
        return binascii.hexlify(cipher.decrypt(data))

    def str_to_key(dessrc):
        bkey = dessrc
        keyarr = []
        for i in range(0, len(bkey)):
            if i % 2 ==0 : keyarr.append(int(bkey[i:i+2],16))
        bytearr = []
        bytearr.append(keyarr[0] >> 1)
        bytearr.append(((keyarr[0] & 0x01) << 6) | keyarr[1] >> 2)
        bytearr.append(((keyarr[1] & 0x03) << 5) | keyarr[2] >> 3)
        bytearr.append(((keyarr[2] & 0x07) << 4) | keyarr[3] >> 4)
        bytearr.append(((keyarr[3] & 0x0F) << 3) | keyarr[4] >> 5)
        bytearr.append(((keyarr[4] & 0x1F) << 2) | keyarr[5] >> 6)
        bytearr.append(((keyarr[5] & 0x3F) << 1) | keyarr[6] >> 7)
        bytearr.append(keyarr[6] & 0x7F)
        result = ''
        for b in bytearr:
            bit = bin(b * 2)[2:].zfill(8)
            if bit.count('1') % 2 == 0:  ## Even parity so RMB bitflip needed
                result += hex((b * 2) ^ 1)[2:].zfill(2)
            else:
                result += hex(b * 2)[2:].zfill(2)
        return result

    ################# MAIN FUNCTION IN STEPS #################
    RegHash = HexRegHash
    UsernameOffset = RegHash[0xc] + 0xcc
    UsernameLength = RegHash[0xc + 4]
    Username = RegHash[UsernameOffset:UsernameOffset + UsernameLength].decode('utf-16')
    #print(('Username (offset 0xc): ' + Username + "\n"))

    #print('####### ---- STEP1, extract the double encrypted NTLM Hash ---- #######')
    Offset = HexRegHash[0xA8 :(0xA8 + 4)][::-1]  ## Offset like 'a0010000'
    NTOffset = int(binascii.b2a_hex(Offset),16) + int(b'0xcc',16)  ## Offset like 0x1a0+0xcc=0x26c
    Length = HexRegHash[0xAC:(0xAC + 4)][::-1]  ## Length like '14000000'
    NTLength = int(binascii.b2a_hex(Length),16)  ## Length like 0x14 (pre 1607) or 0x38 (since 1607)
    # print('Offset is '+NTOffset+' and length is '+Length)
    Hash = HexRegHash[(NTOffset + 4): (NTOffset + 4 + NTLength)][:16]  ## Only 16 bytes needed
    if NTLength == 0x38:
        #print('Detected New Style Hash (AES), need IV')
        Hash = HexRegHash[(NTOffset + 24): (NTOffset + 24 + NTLength)][:16]  ## Only 16 bytes needed
        IV = HexRegHash[(NTOffset + 8):(NTOffset + 24)]  ## IV needed to AES decrypt later
    elif NTLength != 0x14:
        return ''
    #print('####### ---- STEP2, Combine the hBootKey ---- #######')
    Scrambled = jd + skew1 + gbg + data
    hBootkey = Scrambled[8*2:8*2+2]+Scrambled[5*2:5*2+2]+Scrambled[4*2:4*2+2]+Scrambled[2*2:2*2+2]
    hBootkey += Scrambled[11*2:11*2+2]+Scrambled[9*2:9*2+2]+Scrambled[13*2:13*2+2]+Scrambled[3*2:3*2+2]
    hBootkey += Scrambled[0*2:0*2+2]+Scrambled[6*2:6*2+2]+Scrambled[1*2:1*2+2]+Scrambled[12*2:12*2+2]
    hBootkey += Scrambled[14*2:14*2+2]+Scrambled[10*2:10*2+2]+Scrambled[15*2:15*2+2]+Scrambled[7*2:7*2+2]

    hBootVersion = int(binascii.b2a_hex(HexRegSysk[0x00:(0x00 + 1)]), 16)  ## First byte contains version
    if hBootVersion == 3:  ## AES encrypted!
        #print('Detected New Style hBootkey Hash too (AES), needs IV')
        hBootIV = HexRegSysk[0x78:(0x78 + 16)]  ## 16 Bytes iv
        encSysk = HexRegSysk[0x88:(0x88 + 32)][:16]  ## Only 16 bytes needed
        Syskey = decryptAES(encSysk, binascii.unhexlify(hBootkey), hBootIV)
    else:
        Part = binascii.unhexlify(HexRegSysk[0x70:(0x70 + 16)])
        Qwerty = b'!@#$%^&*()qwertyUIOPAzxcvbnmQQQQQQQQQQQQ)(*@&%' + b"\x00"
        hBootkey = binascii.unhexlify(hBootkey)
        Digits = b'0123456789012345678901234567890123456789' + b"\x00"
        RC4Key = binascii.hexlify(md5(Part + Qwerty + hBootkey + Digits).digest())
        encSysk = HexRegSysk[0x80:(0x80 + 32)][:16]  ## Only 16 bytes needed
        Syskey = decryptRC4(encSysk, RC4Key)
    #print(('Your Full Syskey/SAMKey should be ', Syskey, "\n"))

    #print('####### ---- STEP4, use SAM-/Syskey to RC4/AES decrypt the Hash ---- #######')
    HexRID = hex(RID)[2:].zfill(8)  ## 500 becomes '000001f4'
    HexRID = binascii.unhexlify(
        "".join(map(str.__add__, HexRID[-2::-2], HexRID[-1::-2])))  ## '000001f4' becomes 'f4010000'
    if hex(NTLength) == '0x14':  ## RC4 Encrypted Hash
        NTPASSWORD = 'NTPASSWORD' + "\x00"
        SYSKEY = Syskey
        HashRC4Key = md5.new(SYSKEY + HexRID + NTPASSWORD).digest()
        EncryptedHash = decryptRC4(Hash,HashRC4Key)  ## Hash from STEP1, RC4Key from step 3 (76f1327b198c0731ae2611dab42716ea)
    if hex(NTLength) == '0x38':  ## AES Encrypted Hash
        EncryptedHash = decryptAES(Hash, Syskey, IV)  # 494e7ccb2dad245ec2094db427a37ebf6731aed779271e6923cb91a7f6560b0d
    #print(('Your encrypted Hash should be ', EncryptedHash, "\n"))  ## a291d14b768a6ac455a0ab9d376d8551

    #print('####### ---- STEP5, use DES derived from RID to fully decrypt the Hash ---- #######')
    DESSOURCE1 = (format(HexRID[0],'02x') + format(HexRID[1],'02x') + format(HexRID[2],'02x')
                  + format(HexRID[3],'02x') + format(HexRID[0],'02x') + format(HexRID[1],'02x')
                  + format(HexRID[2],'02x')) ##f4010000 becomes f4010000f40100
    DESSOURCE2 = (format(HexRID[3],'02x') + format(HexRID[0],'02x') + format(HexRID[1],'02x')
                  + format(HexRID[2],'02x') + format(HexRID[3],'02x') + format(HexRID[0],'02x')
                  + format(HexRID[1],'02x'))
    ## Nextup: The DESSOURCEs above are converted from 7 byte to 8 byte keys (using Odd Parity):
    DESKEY1 = str_to_key(DESSOURCE1)
    DESKEY2 = str_to_key(DESSOURCE2)
    DecryptedHash = decryptDES(EncryptedHash[:8], DESKEY1) + decryptDES(EncryptedHash[8:], DESKEY2)
    #print(('Your decrypted NTLM Hash should be ', DecryptedHash))  ## 32ed87bdb5fdc5e9cba88547376818d4 which is '123456'
    #print(str(RID) + ':aad3b435b51404eeaad3b435b51404ee:', DecryptedHash, "\n")
    print(DecryptedHash)
    return DecryptedHash.decode('utf-8')