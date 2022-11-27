import Evtx.Evtx as evtx
import xml.etree.ElementTree as XML
import html.parser


class Eventlog_Total_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    event_id = ''
    time_created = ''
    source = ''
    data = ''
    user_sid = ''


ns = ''
tag = lambda v: ns + v if ns else v


def EventlogTotal(real_file_path, filename):
    result = []
    eventlog_count = 0

    with evtx.Evtx(filename) as log:
        for i, rec in enumerate(log.records()):

            xml_str = rec.xml().replace('\x00', '')

            if xml_str != '':
                root = XML.fromstring(xml_str)  # Event Tag
                assert len(XML._namespaces(root)) == 2

                event_total_information = Eventlog_Total_Information()
                result.append(event_total_information)
                result[eventlog_count].event_id = root[0][1].text
                if 'TimeCreated' in root[0][5].tag:
                    result[eventlog_count].time_created = root[0][5].get('SystemTime').replace(' ', 'T') + 'Z'
                else:
                    result[eventlog_count].time_created = root[0][7].get('SystemTime').replace(' ', 'T') + 'Z'
                result[eventlog_count].user_sid = root[0][-1].get('UserID')
                result[eventlog_count].source = real_file_path
                result[eventlog_count].data = html.unescape(xml_str)
                eventlog_count = eventlog_count + 1
    return result
