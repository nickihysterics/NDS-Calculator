const test = require("node:test");
const assert = require("node:assert/strict");
const {calculate, decimal} = require("../src/ui/calculator.js");
const cases = require("./calculation_cases.json");
for (const item of cases) test(item.id, () => {
  const result = calculate(item.raw, item.rate);
  assert.deepEqual([result.net, result.gross, result.vat, result.sumNet, result.sumGross].map(value => decimal(value)), item.expected);
});
for (const value of ["NaN", "Infinity", "-1", "1,2,3", "1000000001"]) test(`reject ${value}`, () => {
  assert.throws(() => calculate({gross: value}, "22"));
});
test("reject zero quantity and invalid rate", () => {
  assert.throws(() => calculate({gross: "122", qty: "0"}, "22"));
  assert.throws(() => calculate({gross: "122"}, "101"));
});
