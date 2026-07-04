import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';

/** @type {import('vite').Plugin} */
const viteServerConfig = {
	name: 'log-request-middleware',
	configureServer(server) {
		server.middlewares.use((req, res, next) => {
			res.setHeader('Access-Control-Allow-Origin', '*');
			res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
			res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
			res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
			res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
			next();
		});
	}
};

export default defineConfig({
	plugins: [
		sveltekit(),
		viteStaticCopy({
			targets: [
				{
					src: 'node_modules/onnxruntime-web/dist/*.jsep.*',
					dest: 'wasm'
				}
			]
		}),
		viteServerConfig
	],
	define: {
		APP_VERSION: JSON.stringify(process.env.npm_package_version),
		APP_BUILD_HASH: JSON.stringify(process.env.APP_BUILD_HASH || 'dev-build')
	},
	build: {
		sourcemap: true
	},
	worker: {
		format: 'es'
	},
	server: {
		fs: {
			allow: [
				'./static/avatar',
				'./static/classroom',
				'./static/draco',
				'./static/images/background.jpeg'
			]
		},
		host: true,
		port: 5173,
		strictPort: true,
		watch: {
			usePolling: true
		},
		proxy: {
			// Dev requests are same-origin (relative URLs in constants.ts) and are
			// proxied to the backend here — that way the HttpOnly session cookie is
			// first-party and attached automatically, mirroring production where
			// FastAPI serves the SPA itself. BACKEND_URL overrides the target for
			// Docker (e.g. http://open-tutor-backend:8080).
			'/api': {
				target: process.env.BACKEND_URL ?? 'http://localhost:8080',
				changeOrigin: true,
				secure: false
			},
			'/auths': {
				target: process.env.BACKEND_URL ?? 'http://localhost:8080',
				changeOrigin: true,
				secure: false
			},
			'/realtime': {
				target: process.env.BACKEND_URL ?? 'http://localhost:8080',
				ws: true,
				changeOrigin: true
			}
		}
	},
	optimizeDeps: {
		include: ['pyodide', 'onnxruntime-web'],
		exclude: ['@sveltejs/kit', 'svelte']
	},
	assetsInclude: ['**/*.glb']
});
