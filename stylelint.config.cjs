module.exports = {
  extends: ["stylelint-config-standard"],

  ignoreFiles: [
    "venv/**",
    ".venv/**",
    "node_modules/**",
    "dist/**",
    "build/**",
    "coverage/**",
    "htmlcov/**",
    "**/*.min.css"
  ],

  rules: {
    "no-duplicate-selectors": true,
    "color-no-invalid-hex": true,
    "comment-empty-line-before": null
  }
};