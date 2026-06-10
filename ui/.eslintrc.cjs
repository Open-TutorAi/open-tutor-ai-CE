module.exports = {
	root: true,
	extends: [
		'eslint:recommended',
		'plugin:@typescript-eslint/recommended',
		'plugin:svelte/recommended',
		'plugin:cypress/recommended',
		'prettier'
	],
	parser: '@typescript-eslint/parser',
	plugins: ['@typescript-eslint'],
	parserOptions: {
		sourceType: 'module',
		ecmaVersion: 2020,
		extraFileExtensions: ['.svelte']
	},
	env: {
		browser: true,
		es2017: true,
		node: true
	},
	rules: {
		// Legacy debt — downgraded to warn, fix progressively
		'@typescript-eslint/no-unused-vars': 'warn',
		'@typescript-eslint/no-explicit-any': 'warn',
		'svelte/valid-compile': 'warn',
		'svelte/no-unused-svelte-ignore': 'warn',
		'svelte/no-at-html-tags': 'warn',
		'no-undef': 'warn',
		'no-constant-condition': 'warn',
		'no-useless-escape': 'warn',
		'no-empty': 'warn',
		'@typescript-eslint/ban-types': 'warn',
		'svelte/no-inner-declarations': 'warn',
		'no-ex-assign': 'warn',
		'no-control-regex': 'warn',
		'@typescript-eslint/no-namespace': 'warn',
		'no-unsafe-optional-chaining': 'warn',
		'no-async-promise-executor': 'warn'
	},
	overrides: [
		{
			files: ['*.svelte'],
			parser: 'svelte-eslint-parser',
			parserOptions: {
				parser: '@typescript-eslint/parser'
			}
		}
	]
};
