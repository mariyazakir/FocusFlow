const test = require("node:test");
const assert = require("node:assert/strict");
const { canContinue } = require("./legal-consent.js");

test("acceptance requires agreement, privacy acknowledgement, and adult attestation", () => {
  assert.equal(canContinue(true, true, true), true);
  assert.equal(canContinue(false, true, true), false);
  assert.equal(canContinue(true, false, true), false);
  assert.equal(canContinue(true, true, false), false);
});
