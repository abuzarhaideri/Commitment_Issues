// Read-only held-out compatibility check. Does not alter the original repair evidence.
const assert = require('node:assert/strict');
const path = require('node:path');
const { test } = require('node:test');

if (!process.env.SEQUELIZE_REPO) {
  throw new Error('Set SEQUELIZE_REPO to the prepared checkout path');
}
const { isValidNumberSyntax } = require(path.join(
  process.env.SEQUELIZE_REPO, 'packages/utils/lib/common/predicates/is-valid-number-syntax.js'));

for (const value of ['1.', '-1.', '1.e3', '-1.e-3', '', '-', 'e5', '-e5', 'E+10']) {
  test(`preserve rejection: ${JSON.stringify(value)}`, () => {
    assert.equal(isValidNumberSyntax(value), false);
  });
}
for (const value of ['0', '-1', '1.0', '.5', '-.5', '1e3', '1e+3', '-1.2E-3']) {
  test(`preserve acceptance: ${JSON.stringify(value)}`, () => {
    assert.equal(isValidNumberSyntax(value), true);
  });
}
