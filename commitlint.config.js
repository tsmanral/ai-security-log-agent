// Conventional Commits enforcement for LSADRA.
// Used by the commitlint pre-commit hook (commit-msg stage) and CI.
module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    // Allow the scopes the project uses; empty scope is also permitted.
    "body-max-line-length": [1, "always", 100],
  },
};
