import dateutil.parser as dp


def convert_iso8601_to_timestamp(iso: str) -> int:
    return int(dp.parse(iso).timestamp())
