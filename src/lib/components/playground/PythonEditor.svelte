<script lang="ts">
	import { onMount } from 'svelte';

	let code = `print("Hello OpenTutorAI")`;
	let output = "";
	let stdout = "";
	let stderr = "";
	let pyodideLoader: typeof import('pyodide')['loadPyodide'] | null = null;
	let pyodideInstance: any = null;
	let pyodideInitializing = false;
	let pyodideRunning = false;
	let isError = false;
	let errorStack = '';

	async function preparePyodide() {
		if (pyodideInstance) {
			return pyodideInstance;
		}

		if (!pyodideLoader) {
			const pyodideModule = await import('pyodide');
			pyodideLoader = pyodideModule.loadPyodide;
		}

		if (typeof pyodideLoader !== 'function') {
			throw new Error('Pyodide loader not available');
		}

		pyodideInitializing = true;
		pyodideInstance = await pyodideLoader({
			indexURL: '/pyodide/'
		});
		pyodideInitializing = false;

		return pyodideInstance;
	}

	async function runPython() {
		stdout = '';
		stderr = '';
		output = '';
		isError = false;
		errorStack = '';

		pyodideRunning = true;
		try {
			const pyodide = await preparePyodide();

			pyodide.setStdout({
				batched: (msg: string) => {
					stdout += msg;
				}
			});

			pyodide.setStderr({
				batched: (msg: string) => {
					stderr += msg;
				}
			});

			const result = await pyodide.runPythonAsync(code);

			if (stderr) {
				isError = true;
				output = stderr.trim();
			} else if (stdout.trim().length > 0) {
				isError = false;
				output = stdout.trim();
			} else if (result !== undefined && result !== null) {
				isError = false;
				output = String(result);
			} else {
				isError = false;
				output = 'Code executed successfully';
			}
		} catch (e: any) {
			isError = true;
			const name = e?.name ? `${e.name}: ` : '';
			output = name + (e?.message ?? String(e));
			if (e?.stack) errorStack = String(e.stack);
		} finally {
			pyodideRunning = false;
		}
	}

	function clearPlayground() {
		code = '';
		output = '';
		stdout = '';
		stderr = '';
		isError = false;
		errorStack = '';
	}

	onMount(async () => {
		try {
			await preparePyodide();
		} catch (error) {
			console.error('Failed to initialize Pyodide:', error);
			output = 'Failed to load Pyodide. Check the browser console for details.';
		}
	});
</script>

<textarea bind:value={code}
	class="w-full h-64 border rounded p-3 font-mono"></textarea>

<button
	on:click={runPython}
	class="mt-3 px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
	disabled={pyodideInitializing || pyodideRunning}>
	{pyodideInitializing ? 'Loading...' : pyodideRunning ? 'Running...' : 'Run ▶'}
</button>

<div class="mt-4">
	<pre
		role="status"
		aria-live="polite"
		aria-atomic="true"
		class={"p-3 rounded " + (isError ? 'text-red-700 bg-red-100' : 'text-gray-800 bg-gray-100')}
		><code>{output}</code></pre>

	{#if isError && errorStack}
		<details class="mt-2 p-2 bg-red-50 rounded text-sm text-red-800">
			<summary class="cursor-pointer">Afficher la stack complète</summary>
			<pre class="mt-2 whitespace-pre-wrap">{errorStack}</pre>
		</details>
	{/if}
</div>