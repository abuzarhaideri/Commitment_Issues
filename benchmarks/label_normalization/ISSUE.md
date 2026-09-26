Catalog label normalization changes the order users entered their labels.
Fix normalize_labels so normalized labels preserve their first occurrence order.
Keep trimming, Unicode case folding, duplicate/blank removal, iterable support,
and input immutability. Do not change the tests.
