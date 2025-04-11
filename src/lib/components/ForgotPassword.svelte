<script>
	import { getContext, onMount, createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');
	let email = '';
	let isSubmitting = false;
	let errorMessage = '';
	let successMessage = '';

	function validateEmail(email) {
		const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
		return emailRegex.test(email);
	}

	async function handleSubmit() {
		errorMessage = '';
		successMessage = '';

		if (!validateEmail(email)) {
			errorMessage = $i18n.t('Please enter a valid email address.');
			return;
		}

		isSubmitting = true;
		try {
			await new Promise((resolve) => setTimeout(resolve, 1500));
			successMessage = $i18n.t('Password reset instructions sent to ') + email;
		} catch (error) {
			errorMessage = $i18n.t('Something went wrong. Please try again later.');
		} finally {
			isSubmitting = false;
		}
	}

	function returnToSignIn() {
		dispatch('close');
	}
</script>

<div class="fixed inset-0 z-50 bg-gray-100 dark:bg-gray-900 overflow-y-auto">
	<div class="min-h-screen w-full flex flex-col md:flex-row font-sans">
		<!-- Left Panel -->
		<div class="w-full md:w-5/12 bg-[#E6F0FA] p-6 md:p-12 flex flex-col justify-center">
			<div class="mx-auto max-w-md w-full">
				<h2 class="text-2xl md:text-3xl font-bold text-gray-800 mb-3">
					{$i18n.t('Password Recovery')}
				</h2>
				<p class="text-sm md:text-base text-gray-600 mb-8">
					{$i18n.t('Well help you get back to your account.')}
				</p>

				<!-- Steps -->
				<div class="space-y-5">
					<div class="flex items-center">
						<div
							class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold mr-4"
						>
							1
						</div>
						<span class="text-sm md:text-base text-gray-700"
							>{$i18n.t('Enter your email address')}</span
						>
					</div>
					<div class="flex items-center">
						<div
							class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold mr-4"
						>
							2
						</div>
						<span class="text-sm md:text-base text-gray-700"
							>{$i18n.t('Check your inbox for reset link')}</span
						>
					</div>
					<div class="flex items-center">
						<div
							class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold mr-4"
						>
							3
						</div>
						<span class="text-sm md:text-base text-gray-700">{$i18n.t('Create new password')}</span>
					</div>
				</div>

				<!-- Divider -->
				<div class="border-t border-gray-200 my-8"></div>

				<!-- Help Section -->
				<div>
					<p class="font-semibold text-gray-800 text-sm md:text-base mb-3">
						{$i18n.t('Need help?')}
					</p>
					<div class="bg-white p-4 rounded-lg shadow-sm border border-gray-100 w-full max-w-xs">
						<p class="text-gray-500 text-sm mb-1">{$i18n.t('Contact Support:')}</p>
						<a
							href="mailto:support@opentutorai.com"
							class="text-blue-600 text-sm hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
							>support@opentutorai.com</a
						>
					</div>
				</div>
			</div>
		</div>

		<!-- Right Panel -->
		<div class="w-full md:w-7/12 bg-white p-6 md:p-12 flex flex-col justify-center relative">
			<!-- Help Button -->
			<a
				href="#"
				class="absolute top-4 right-4 md:top-6 md:right-6 bg-[#E6F0FA] text-gray-700 text-sm font-medium px-4 py-1 border border-gray-300 rounded-full hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
			>
				{$i18n.t('Help')}
			</a>

			<div class="mx-auto max-w-md w-full">
				<h2 class="text-2xl md:text-3xl font-bold text-gray-800 mb-3">
					{$i18n.t('Forgot Password?')}
				</h2>
				<p class="text-sm md:text-base text-gray-600 mb-8">
					{$i18n.t('Enter your email to receive password reset instructions')}
				</p>

				<!-- Success/Error Messages -->
				{#if errorMessage}
					<div class="mb-6 p-4 bg-red-50 text-red-700 text-sm rounded-lg flex items-center">
						<svg
							class="w-5 h-5 mr-2"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
							></path>
						</svg>
						{errorMessage}
					</div>
				{/if}
				{#if successMessage}
					<div class="mb-6 p-4 bg-green-50 text-green-700 text-sm rounded-lg flex items-center">
						<svg
							class="w-5 h-5 mr-2"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M5 13l4 4L19 7"
							></path>
						</svg>
						{successMessage}
					</div>
				{/if}

				<form on:submit|preventDefault={handleSubmit}>
					<!-- Email Input -->
					<div class="mb-6">
						<label for="email" class="block text-gray-700 text-sm md:text-base font-medium mb-2"
							>Email Address</label
						>
						<input
							type="email"
							id="email"
							bind:value={email}
							placeholder={$i18n.t('Enter your registered email')}
							class="w-full px-4 py-3 bg-white text-gray-600 text-sm md:text-base border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
							required
							aria-describedby="email-error"
						/>
					</div>

					<!-- CAPTCHA -->
					<div class="mb-9">
						<label for="captcha" class="block text-gray-700 text-sm md:text-base font-medium mb-2"
							>{$i18n.t('Security Check')}</label
						>
						<div
							class="w-full h-20 bg-gray-50 border border-gray-200 rounded flex items-center justify-center text-gray-500"
						>
							{$i18n.t('CAPTCHA / Security verification')}
						</div>
					</div>

					<!-- Submit Button -->
					<button
						type="submit"
						class="w-full py-3 bg-[#1E88E5] hover:bg-[#1565C0] text-white text-sm md:text-base font-semibold rounded transition-all disabled:bg-blue-400 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
						disabled={isSubmitting}
					>
						{#if isSubmitting}
							<svg
								class="animate-spin h-5 w-5 mr-2 inline-block"
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
							>
								<circle
									class="opacity-25"
									cx="12"
									cy="12"
									r="10"
									stroke="currentColor"
									stroke-width="4"
								></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
								></path>
							</svg>
							{$i18n.t('Sending...')}
						{:else}
							{$i18n.t('Send Reset Instructions')}
						{/if}
					</button>
				</form>

				<!-- Bottom Links -->
				<div class="mt-6 flex justify-center items-center space-x-4 text-sm">
					<span class="text-gray-500">{$i18n.t('Remember your password?')}</span>
					<button
						on:click={returnToSignIn}
						class="text-blue-600 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
						>{$i18n.t('Back to Sign In')}</button
					>
				</div>

				<!-- Spam Notice -->
				<div class="mt-8 text-center text-gray-600 text-sm bg-gray-100 px-4 py-3 rounded w-full">
					{$i18n.t('Check your spam folder if you dont see the reset email in your inbox')}
				</div>
			</div>
		</div>
	</div>
</div>