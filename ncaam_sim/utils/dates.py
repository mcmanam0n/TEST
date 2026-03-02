from datetime import datetime


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, '%Y-%m-%d')
