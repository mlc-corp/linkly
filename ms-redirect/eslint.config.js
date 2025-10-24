import js from "@eslint/js";
import pluginImport from "eslint-plugin-import";
import configPrettier from "eslint-config-prettier";
import globals from "globals";

export default [
  {
    ignores: [
      "node_modules/**",
      "coverage/**",
      "playwright-report/**",
      "test-results/**",
      "dist/**",
      "tests/**",
    ],
  },

  js.configs.recommended,

  {
    files: ["**/*.js", "**/*.mjs"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...globals.node,
      },
    },
    plugins: {
      import: pluginImport,
    },
    rules: {
      "import/order": ["warn", { "newlines-between": "always" }],
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
    },
  },

  configPrettier,
];
