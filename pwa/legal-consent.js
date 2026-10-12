((root, factory) => {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.FocusFlowLegal = api;
})(globalThis, () => Object.freeze({
  canContinue: (terms, privacy, adultConfirmed) => Boolean(terms && privacy && adultConfirmed),
}));
