import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { fileURLToPath } from 'node:url';
import path from 'path';

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
	plugins: [svelte({ hot: !process.env.VITEST })],
	test: {
		globals: true,
		environment: 'jsdom',
		include: ['src/tests/**/*.{test,spec}.{js,ts,jsx,tsx}'],
		coverage: {
			reporter: ['text', 'json', 'html']
		}
	},
	resolve: {
		alias: {
			$lib: path.resolve(rootDir, './src/lib'),
			$app: path.resolve(rootDir, './node_modules/@sveltejs/kit/src/runtime/app')
		}
	}
});
