def format_timestamp(timestamp):
    if timestamp is None:
        return 'N/A'
    return timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')