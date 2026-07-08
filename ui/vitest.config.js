import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { fileURLToPath } from 'node:url';
import path from 'path';

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
	plugins: [svelte({ hot: !process.env.VITEST })],
	define: {
		// $lib/constants.ts references these Vite-injected globals (set for real
		// in vite.config.ts); without them here, any test that transitively
		// imports constants.ts throws "APP_BUILD_HASH is not defined".
		APP_VERSION: JSON.stringify(process.env.npm_package_version ?? '0.0.0'),
		APP_BUILD_HASH: JSON.stringify(process.env.APP_BUILD_HASH ?? 'test-build')
	},
	test: {
		globals: true,
		environment: 'jsdom',
		include: ['src/tests/**/*.{test,spec}.{js,ts,jsx,tsx}'],
		coverage: {
			reporter: ['text', 'json', 'html']
		}
	},
	resolve: {
		// Without this, Vite resolves 'svelte' via its Node/SSR export condition under
		// Vitest, which stubs out lifecycle functions like onMount to no-ops (SSR has no
		// real mount event) — components compile fine but onMount callbacks silently never run.
		conditions: process.env.VITEST ? ['browser'] : [],
		alias: {
			$lib: path.resolve(rootDir, './src/lib'),
			$app: path.resolve(rootDir, './node_modules/@sveltejs/kit/src/runtime/app')
		}
	}
});
