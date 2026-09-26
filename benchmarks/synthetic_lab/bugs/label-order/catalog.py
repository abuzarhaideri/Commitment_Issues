"""Normalize catalog labels for display and matching."""


def normalize_labels(labels):
    """Trim and case-fold labels, discard blanks, and remove duplicates."""
    normalized = [label.strip().casefold() for label in labels]
    return sorted(set(label for label in normalized if label))
