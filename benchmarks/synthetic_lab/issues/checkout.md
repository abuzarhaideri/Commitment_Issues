Checkout totals are wrong for quantities and discounts, and empty carts incur shipping.

Fix the pricing and checkout implementations. Prices and amounts are integer cents;
inputs contain nonnegative integer unit prices and quantities. A cart line costs
unit price times quantity, including zero quantity. Sum line costs for the subtotal.
Clamp the discount to [0, subtotal]. Free shipping applies when the subtotal AFTER
discount is at least 5000 cents; otherwise shipping is 500 cents. A cart with a
zero subtotal incurs no shipping, including empty carts and zero-quantity lines.
A nonzero cart fully discounted to zero still incurs 500 cents shipping.
The total is subtotal minus discount plus shipping. Preserve the existing summary
keys, iterable/generator support, and input immutability. Do not change tests.
