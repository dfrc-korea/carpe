import datetime

def format_timestamp(timestamp, time_zone):
    if timestamp is None or timestamp == '' or timestamp == 0:
        return ''
    try:
        timestamp = timestamp + datetime.timedelta(seconds=32400)
        return timestamp.astimezone(time_zone).isoformat()
    except:
        # TODO: 1970.01.02 timezone error 수정
        return ''
