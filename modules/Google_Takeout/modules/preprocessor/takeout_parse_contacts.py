import os


class Contacts(object):
    def parse_contacts(case):
        file_path = case.takeout_contacts_path
        if not os.path.exists(file_path):
            return False

        result = []
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            lines = [x.strip() for x in lines]
            size = len(lines)
            idx_list = [idx + 1 for idx, val in enumerate(lines) if val == 'END:VCARD']
            all_list_contacts = [lines[i: j] for i, j in zip([0] + idx_list, idx_list + ([size] if idx_list[-1] != size else []))]

            if all_list_contacts:
                for i in range(len(all_list_contacts)):
                    dic_contacts = {'category' : "", 'name':"", 'tel':"", 'email':"", 'photo':"", 'note':""}
                    Contacts.parse_contacts_information(dic_contacts, all_list_contacts[i])

                    result.append((dic_contacts['category'], dic_contacts['name'], dic_contacts['tel'], dic_contacts['email'], dic_contacts['photo'], dic_contacts['note']))
        return result

    def parse_contacts_information(dic_contacts, list_contacts):
        for i in range(len(list_contacts)):
            contents = list_contacts[i].replace('\\xad', '')
            list_value = contents.split(':', 1)

            if not list_value:
                continue

            if len(list_value) == 1:
                photo = list_contacts[i-1].lstrip('PHOTO:') + list_contacts[i]
                dic_contacts['photo'] = photo
            else:
                tag = list_value[0]
                value = list_value[1]
                if tag == 'BEGIN' or tag == 'END' or tag == 'N' or tag == 'VERSION' or tag == 'PHOTO':
                    continue
                else:
                    if tag == 'FN':
                        dic_contacts['name'] = value
                    elif tag == 'CATEGORIES':
                        dic_contacts['category'] = value
                    elif tag == 'TEL' or tag.find('TEL') >= 0:
                        if dic_contacts['tel'] != "":
                            dic_contacts['tel'] += ',' + value
                        else:
                            dic_contacts['tel'] = value
                    elif tag == 'NOTE':
                        dic_contacts['note'] = value
                    elif tag == 'EMAIL' or tag.find('EMAIL') >= 0:
                        if dic_contacts['email'] != "":
                            dic_contacts['email'] += ',' + value
                        else:
                            dic_contacts['email'] = value