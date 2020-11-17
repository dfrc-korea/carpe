def format_timestamp(timestamp, time_zone):
    if timestamp is None:
        return ''
    return timestamp.astimezone(time_zone).isoformat()
