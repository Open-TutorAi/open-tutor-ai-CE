import { defineConfig } from 'cypress';

export default defineConfig({
	e2e: {
		baseUrl: 'http://localhost:5173',
		viewportWidth: 1280,
		viewportHeight: 720,
		defaultCommandTimeout: 15000,
		requestTimeout: 15000,
		responseTimeout: 30000,
		video: true,
		screenshotOnRunFailure: true,
		chromeWebSecurity: false,
		experimentalStudio: true,
		supportFile: 'cypress/support/index.ts',
		setupNodeEvents(on, config) {
			// implement node event listeners here
		}
	},
	retries: {
		runMode: 2,
		openMode: 0
	},
	env: {
		apiUrl: 'http://localhost:5173',
	},
	video: true,
	screenshotOnRunFailure: true
});
