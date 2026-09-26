"""Paginate sequences using a one-based page number."""


def paginate(items, page, page_size):
    if page < 1 or page_size < 1:
        raise ValueError('Page and page size must be positive')
    start = (page - 1) * page_size
    return items[start:start + page_size]
