// eslint.config.mjs
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';
import nextPlugin from '@next/eslint-plugin-next';
import prettier from 'eslint-config-prettier';

/** @type {import('eslint').Linter.FlatConfig[]} */
export default [
  // Ignore stuff we don't want to lint
  {
    ignores: [
      'node_modules/**',
      '.next/**',
      'dist/**',
      'out/**',
      'public/**',
      'coverage/**',
      'pnpm-lock.yaml',
      'eslint.config.mjs',
    ],
  },

  // JS recommended
  js.configs.recommended,

  // TS recommended (type-aware)
  ...tseslint.configs.recommendedTypeChecked.map((cfg) => ({
    ...cfg,
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      ...cfg.languageOptions,
      parserOptions: {
        ...cfg.languageOptions?.parserOptions,
        project: ['./tsconfig.json'],
        tsconfigRootDir: process.cwd(),
      },
    },
  })),

  // App rules (React Hooks, Next, etc.)
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    plugins: {
      'react-hooks': reactHooks,
      next: nextPlugin,
      '@typescript-eslint': tseslint.plugin,
    },
    rules: {
      // React Hooks best practices
      ...reactHooks.configs.recommended.rules,

      // A few sensible TS tweaks
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-misused-promises': ['error', { checksVoidReturn: false }],

      // Relax strict type-check rules to reduce noise and allow gradual typing
      '@typescript-eslint/no-unsafe-assignment': 'off',
      '@typescript-eslint/no-unsafe-member-access': 'off',
      '@typescript-eslint/no-unsafe-argument': 'off',
      '@typescript-eslint/no-unsafe-return': 'off',
      '@typescript-eslint/no-unsafe-call': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/require-await': 'off',
      '@typescript-eslint/restrict-template-expressions': 'off',

      // '@next/next/no-img-element': 'warn',
    },
  },

  // Turn off stylistic rules that Prettier handles
  prettier,
];
