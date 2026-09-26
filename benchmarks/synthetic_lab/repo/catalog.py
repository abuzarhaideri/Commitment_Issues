"""Normalize catalog labels while retaining first occurrence order."""


def normalize_labels(labels):
    seen = set()
    result = []
    for label in labels:
        normalized = label.strip().casefold()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
