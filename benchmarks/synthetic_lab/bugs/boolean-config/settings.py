"""Parse text configuration."""


def parse_bool(value, default=False):
    return default if value is None else bool(value)
