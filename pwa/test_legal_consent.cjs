const test = require("node:test");
const assert = require("node:assert/strict");
const { canContinue } = require("./legal-consent.js");

test("acceptance requires agreement and privacy acknowledgement, without an age gate", () => {
  assert.equal(canContinue(true, true), true);
  assert.equal(canContinue(false, true), false);
  assert.equal(canContinue(true, false), false);
});
