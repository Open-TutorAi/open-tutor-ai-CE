<script lang="ts">
	import { onMount } from 'svelte';

	let code = `print("Hello OpenTutorAI")`;
	let output = "";
	let stdout = "";
	let stderr = "";
	let pyodideLoader: typeof import('pyodide')['loadPyodide'] | null = null;
	let pyodideInstance: any = null;
	let pyodideInitializing = false;

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
				output = stderr.trim();
			} else if (stdout.trim().length > 0) {
				output = stdout.trim();
			} else if (result !== undefined && result !== null) {
				output = String(result);
			} else {
				output = 'Code executed successfully';
			}
		} catch (e) {
			output = e?.message ?? String(e);
		}
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
	class="mt-3 px-4 py-2 bg-blue-500 text-white rounded"
	disabled={pyodideInitializing}>
	{pyodideInitializing ? 'Loading...' : 'Run ▶'}
</button>

<pre class="mt-4 bg-gray-100 p-3 rounded">{output}</pre>