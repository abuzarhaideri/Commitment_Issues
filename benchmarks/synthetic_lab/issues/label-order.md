Label normalization sorts labels instead of retaining first occurrence order.
Fix normalize_labels to preserve that order after trimming and Unicode case
folding, removing duplicates and blanks. Keep iterable/generator support and
input immutability. Preserve all other modules. Do not modify tests.
