"""Parse text configuration without treating 'false' as truthy."""


def parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        raise TypeError('Expected a boolean, string, or None')
    normalized = value.strip().casefold()
    if normalized in {'true', '1', 'yes', 'on'}:
        return True
    if normalized in {'false', '0', 'no', 'off'}:
        return False
    raise ValueError('Unrecognized boolean string')
