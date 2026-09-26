Inventory reservations are inconsistent across duplicate lines, exact-capacity
orders, and rejected multi-item orders. Fix reserve_order(stock, lines).

Each line is (sku, quantity). Aggregate repeated SKUs by adding quantities.
Only positive integers are valid; reject bool and other types with TypeError,
and nonpositive integers with ValueError. Exact available stock is sufficient.
A successful reservation deducts quantities and returns a separate dictionary
of reserved quantities. Failed reservations must leave stock unchanged.
Missing SKUs cannot be reserved. Empty orders return {} without changing stock.
Support one-pass iterables. Preserve public signatures and unrelated behavior.

Inspect the modules and tests; no solution patch is supplied. Tests and
verification infrastructure are read-only. Use supplied verification commands.
