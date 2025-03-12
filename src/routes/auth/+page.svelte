<script>
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	import { getBackendConfig } from '$lib/apis';
	import { ldapUserSignIn, getSessionUser, userSignIn, userSignUp } from '$lib/apis/auths';

	import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
	import { WEBUI_NAME, config, user, socket } from '$lib/stores';

	import { generateInitialsImage, canvasPixelTest } from '$lib/utils';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import OnBoarding from '$lib/components/OnBoarding.svelte';

	const i18n = getContext('i18n');

	let loaded = false;

	let mode = $config?.features.enable_ldap ? 'ldap' : 'signup'; // Changed default to signup

	let firstName = '';
	let lastName = '';
	let email = '';
	let password = '';
	let showPassword = false;
	let role = '';
	let rememberMe = false;

	let ldapUsername = '';

	const querystringValue = (key) => {
		const querystring = window.location.search;
		const urlParams = new URLSearchParams(querystring);
		return urlParams.get(key);
	};

	const setSessionUser = async (sessionUser) => {
		if (sessionUser) {
			console.log(sessionUser);
			toast.success($i18n.t(`You're now logged in.`));
			if (sessionUser.token) {
				localStorage.token = sessionUser.token;
			}

			$socket.emit('user-join', { auth: { token: sessionUser.token } });
			await user.set(sessionUser);
			await config.set(await getBackendConfig());

			const redirectPath = querystringValue('redirect') || '/';
			goto(redirectPath);
		}
	};

	const signInHandler = async () => {
		const sessionUser = await userSignIn(email, password).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		await setSessionUser(sessionUser);
	};

	const signUpHandler = async () => {
		const name = `${firstName} ${lastName}`.trim();
		const sessionUser = await userSignUp(name, email, password, generateInitialsImage(name)).catch(
			(error) => {
				toast.error(`${error}`);
				return null;
			}
		);

		await setSessionUser(sessionUser);
	};

	const ldapSignInHandler = async () => {
		const sessionUser = await ldapUserSignIn(ldapUsername, password).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		await setSessionUser(sessionUser);
	};

	const submitHandler = async () => {
		if (mode === 'ldap') {
			await ldapSignInHandler();
		} else if (mode === 'signin') {
			await signInHandler();
		} else {
			await signUpHandler();
		}
	};

	const checkOauthCallback = async () => {
		if (!$page.url.hash) {
			return;
		}
		const hash = $page.url.hash.substring(1);
		if (!hash) {
			return;
		}
		const params = new URLSearchParams(hash);
		const token = params.get('token');
		if (!token) {
			return;
		}
		const sessionUser = await getSessionUser(token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		if (!sessionUser) {
			return;
		}
		localStorage.token = token;
		await setSessionUser(sessionUser);
	};

	// Function to toggle password visibility
	const togglePasswordVisibility = () => {
		showPassword = !showPassword;
	};

	function togglePassword(node) {
		node.type = false ? 'text' : 'password';

		return {
		update(showPassword) {
			node.type = showPassword ? 'text' : 'password';
		}
		};
	};

	let onboarding = false;

	onMount(async () => {
		if ($user !== undefined) {
			await goto('/');
		}
		await checkOauthCallback();

		loaded = true;
		if (($config?.features.auth_trusted_header ?? false) || $config?.features.auth === false) {
			await signInHandler();
		} else {
			onboarding = $config?.onboarding ?? false;
		}
	});
</script>

<svelte:head>
	<title>
	  {mode === 'signup' ? $i18n.t('Create Account') : $i18n.t('Sign in')} | OpenTutorAI
	</title>
	  <!-- Standard favicon for most browsers -->
	  <link rel="icon" href="favicon/favicon.ico" type="image/x-icon">
	  <!-- PNG version for browsers that support it -->
	  <link rel="icon" href="favicon/favicon-96x96.png" type="image/png">
	  <!-- Apple Touch Icon for iOS devices -->
	  <link rel="apple-touch-icon" href="favicon/apple-touch-icon.png">
	  <!-- Web app manifests for mobile devices -->
	  <link rel="manifest" href="favicon/site.webmanifest">
</svelte:head>

<OnBoarding
	bind:show={onboarding}
	getStartedHandler={() => {
		onboarding = false;
		mode = $config?.features.enable_ldap ? 'ldap' : 'signup';
	}}
/>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900 relative" style="height: 100vh; overflow-y: auto;">
	<div class="w-full absolute top-0 left-0 right-0 h-8 drag-region" />

	{#if loaded}
		<div class="flex flex-col md:flex-row w-full" style="min-height: calc(100vh - 8px);">
			<!-- Left panel with branding and features -->
			<div class="w-full md:w-2/5 bg-blue-50 dark:bg-gray-800 p-8 flex flex-col md:h-screen overflow-y-auto" style="max-height: 100vh;" role="complementary">
				<div class="flex items-center mb-6">
					<p class="text-2xl font-semibold text-black dark:text-white font-InstrumentSerif">
						{$i18n.t('Open')} <span style="color: #57CED8;">{$i18n.t('TutorAI')}</span>
					</p>
				</div>
				
				<p class="text-3xl font-semibold mb-1 text-black dark:text-white font-InstrumentSerif">
					{$i18n.t('Welcome to Open')} <span style="color: #57CED8;">{$i18n.t('TutorAI')}</span>
				</p>
				<p class="text-l text-gray-800 dark:text-gray-200 mb-10 font-InstrumentSerif">{$i18n.t('Your Path to Smarter Learning')}</p>
				
				{#if mode === 'signup'}
					<div class="space-y-4">
						<div class="bg-white dark:bg-gray-700 rounded-lg p-4 flex items-center shadow-sm">
							<div class="w-10 h-10 min-w-10 rounded-full bg-blue-100 dark:bg-gray-100 flex items-center justify-center mr-4">
								<svg xmlns="http://www.w3.org/2000/svg" style="color: #57CED8;" class="h-5 w-5 dark:text-blue-300" viewBox="0 0 20 20" fill="currentColor">
									<path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
									<path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd" />
								</svg>
							</div>
							<span class="text-gray-900 dark:text-gray-50">{$i18n.t('Personalized learning experience')}</span>
						</div>
						
						<div class="bg-white dark:bg-gray-700 rounded-lg p-4 flex items-center shadow-sm">
							<div class="w-10 h-10 min-w-10 rounded-full bg-blue-100 dark:bg-gray-100 flex items-center justify-center mr-4">
								<svg xmlns="http://www.w3.org/2000/svg" style="color: #57CED8;" class="h-5 w-5 dark:text-blue-300" viewBox="0 0 20 20" fill="currentColor">
									<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clip-rule="evenodd" />
								</svg>
							</div>
							<span class="text-gray-900 dark:text-gray-50">{$i18n.t('AI-powered assistance')}</span>
						</div>
						
						<div class="bg-white dark:bg-gray-700 rounded-lg p-4 flex items-center shadow-sm">
							<div class="w-10 h-10 min-w-10 rounded-full bg-blue-100 dark:bg-gray-100 flex items-center justify-center mr-4">
								<svg xmlns="http://www.w3.org/2000/svg" style="color: #57CED8;" class="h-5 w-5 dark:text-blue-300" viewBox="0 0 20 20" fill="currentColor">
									<path fill-rule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
								</svg>
							</div>
							<span class="text-gray-900 dark:text-gray-50">{$i18n.t('Track your progress')}</span>
						</div>
						
						<div class="bg-white dark:bg-gray-700 rounded-lg p-4 flex items-center shadow-sm">
							<div class="w-10 h-10 min-w-10 rounded-full bg-blue-100 dark:bg-gray-100 flex items-center justify-center mr-4">
								<svg xmlns="http://www.w3.org/2000/svg" style="color: #57CED8;" class="h-5 w-5 dark:text-blue-300" viewBox="0 0 20 20" fill="currentColor">
								<path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
								</svg>
							</div>
							<span class="text-gray-900 dark:text-gray-50">{$i18n.t('Access to premium content')}</span>
						</div>
					</div>
				{:else}
					<!-- Login illustration placeholder - kept unchanged -->
					<div class="flex justify-center items-center my-8">
						<img src="/grad-students.png" alt={$i18n.t('Learning illustration')} class="w-75 md:w-87" />
					</div>
					
					<!-- Feature list for login - kept unchanged -->
					<div class="mt-auto space-y-4">
						<div class="flex items-center">
							<div class="w-8 h-8 rounded-full bg-blue-100 dark:bg-gray-100 flex items-center justify-center mr-3">
								<svg xmlns="http://www.w3.org/2000/svg" style="color: #57CED8;" class="h-4 w-4 dark:text-blue-300" viewBox="0 0 20 20" fill="currentColor">
									<path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
									<path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd" />
								</svg>
							</div>
							<span class="text-gray-700 dark:text-gray-200">{$i18n.t('Personalized Learning')}</span>
						</div>
						<div class="flex items-center">
							<div class="w-8 h-8 rounded-full bg-blue-100 dark:bg-gray-100 flex items-center justify-center mr-3">
								<svg xmlns="http://www.w3.org/2000/svg" style="color: #57CED8;" class="h-4 w-4 dark:text-blue-300" viewBox="0 0 20 20" fill="currentColor">
									<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clip-rule="evenodd" />
								</svg>
							</div>
							<span class="text-gray-700 dark:text-gray-200">{$i18n.t('AI Assistant')}</span>
						</div>
						<div class="flex items-center">
							<div class="w-8 h-8 rounded-full bg-blue-100 dark:bg-gray-100 flex items-center justify-center mr-3">
								<svg xmlns="http://www.w3.org/2000/svg" style="color: #57CED8;" class="h-4 w-4 dark:text-blue-300" viewBox="0 0 20 20" fill="currentColor">
									<path fill-rule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
								</svg>
							</div>
							<span class="text-gray-700 dark:text-gray-200">{$i18n.t('Progress Tracking')}</span>
						</div>
					</div>
				{/if}
			</div>

			<!-- Right panel with authentication form -->
			<div class="w-full md:w-3/5 flex justify-center p-8 bg-white dark:bg-gray-900 md:h-screen overflow-y-auto" 
				style="max-height: 100vh;" role="main">
				<div class="w-full max-w-md py-4 md:py-8 pb-12">
					{#if ($config?.features.auth_trusted_header ?? false) || $config?.features.auth === false}
						<div class="text-center mb-6">
							<div class="flex items-center justify-center gap-3 text-xl sm:text-2xl font-semibold dark:text-gray-200">
								<div>
									{$i18n.t('Signing in to {{WEBUI_NAME}}', { WEBUI_NAME: $WEBUI_NAME })}
								</div>
								<div>
									<Spinner />
								</div>
							</div>
						</div>
					{:else}
						<div class="mb-8">
							<h2 class="text-2xl font-semibold mb-2 text-black dark:text-white">
								{#if mode === 'signup'}
									{$i18n.t('Create Account')}
								{:else}
									{$i18n.t('Sign in')}
								{/if}
							</h2>
							{#if mode === 'signup'}
								<p class="text-gray-600 dark:text-gray-400 text-sm">
									{$i18n.t('Fill in your information to get started')}
								</p>
							{:else}
								<p class="text-gray-600 dark:text-gray-400 text-sm">
									{$i18n.t('Sign in to access your account')}
								</p>
							{/if}
						</div>

						<form class="space-y-5" on:submit|preventDefault={submitHandler}>
							{#if mode === 'signup'}
								<div class="grid grid-cols-2 gap-4">
									<div>
										<label for="firstName" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
											{$i18n.t('First Name')}
										</label>
										<input
											id="firstName"
											bind:value={firstName}
											type="text"
											class="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-black dark:text-white"
											required
										/>
									</div>
									<div>
										<label for="lastName" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
											{$i18n.t('Last Name')}
										</label>
										<input
											id="lastName"
											bind:value={lastName}
											type="text"
											class="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-black dark:text-white"
											required
										/>
									</div>
								</div>
							{/if}

							{#if mode === 'ldap'}
								<div>
									<label for="username" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
										{$i18n.t('Username')}
									</label>
									<input
										id="username"
										bind:value={ldapUsername}
										type="text"
										autocomplete="username"
										name="username"
										class="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-black dark:text-white"
										placeholder={$i18n.t('Enter Your Email')}
										required
									/>
								</div>
							{:else}
								<div>
									<label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
										{$i18n.t('Email')}
									</label>
									<input
										id="email"
										bind:value={email}
										type="email"
										autocomplete="email"
										name="email"
										class="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-black dark:text-white"
										placeholder={$i18n.t('Enter Your Email')}
										required
									/>
								</div>
							{/if}

							<div>
								<div class="flex justify-between items-center mb-1">
									<label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
										{$i18n.t('Password')}
									</label>
									{#if mode === 'signin'}
										<a href="#" class="text-sm text-blue-500 hover:text-blue-600 dark:text-blue-400">
											{$i18n.t('Forgot password?')}
										</a>
									{/if}
								</div>
								<div class="relative">
									<input
										id="password"
										bind:value={password}
										use:togglePassword={showPassword}
										class="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-black dark:text-white pr-16"
										placeholder={$i18n.t('Enter Your Password')}
										autocomplete="current-password"
										name="current-password"
										required
									/>
									<button
										type="button"
										class="absolute inset-y-0 right-0 pr-3 flex items-center text-sm text-blue-600 hover:text-blue-700 dark:text-blue-300 dark:hover:text-blue-200"
										on:click={togglePasswordVisibility}
									>
										{$i18n.t(showPassword ? 'Hide' : 'Show')}
									</button>
								</div>
							</div>

							{#if mode === 'signup'}
								<div>
									<label for="role" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
										{$i18n.t('Account Type')}
									</label>
									<div class="relative">
										<select
											id="role"
											bind:value={role}
											class="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-black dark:text-white appearance-none"
											style="-webkit-appearance: none; -moz-appearance: none;"
										>
											<option value="" disabled selected>{$i18n.t('Select your role')}</option>
											<option value="teacher">{$i18n.t('Teacher')}</option>
											<option value="student">{$i18n.t('Student')}</option>
											<option value="admin">{$i18n.t('Admin')}</option>
										</select>
									</div>
								</div>

								<div class="flex items-center">
									<input
										id="terms"
										type="checkbox"
										class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-600"
										required
									/>
									<label for="terms" class="ml-2 block text-sm text-gray-800 dark:text-gray-200">
										{$i18n.t('I agree to the')}
										<a href="#" class="text-blue-600 hover:text-blue-700 dark:text-blue-300 dark:hover:text-blue-200"> {$i18n.t('Terms of Service')} </a>
										{$i18n.t('and')}
										<a href="#" class="text-blue-600 hover:text-blue-700 dark:text-blue-300 dark:hover:text-blue-200"> {$i18n.t('Privacy Policy')} </a>
									</label>
								</div>
							{/if}

							{#if mode === 'signin'}
								<div class="flex items-center justify-between">
									<div class="flex items-center">
										<input
											id="remember-me"
											bind:checked={rememberMe}
											type="checkbox"
											class="h-4 w-4 text-blue-500 border-gray-300 rounded focus:ring-blue-500"
										/>
										<label for="remember-me" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
											{$i18n.t('Remember me')}
										</label>
									</div>
								</div>
							{/if}

							<button
								type="submit"
								class="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2.5 px-4 rounded-md transition duration-150 ease-in-out"
							>
								{#if mode === 'signup'}
									{$i18n.t('Create Account')}
								{:else}
									{$i18n.t('Sign in')}
								{/if}
							</button>
						</form>

						{#if Object.keys($config?.oauth?.providers ?? {}).length > 0 || true}
							<div class="my-6 flex items-center">
								<div class="flex-grow border-t border-gray-300 dark:border-gray-700"></div>
								<span class="flex-shrink mx-4 text-gray-700 dark:text-gray-300">{$i18n.t('OR')}</span>
								<div class="flex-grow border-t border-gray-300 dark:border-gray-700"></div>
							</div>

							<div class="space-y-3 overflow-y-auto">
								{#if $config?.oauth?.providers?.google || true}
									<button
										class="w-full flex items-center justify-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md py-2.5 px-4 text-gray-700 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-700"
										on:click={() => {
											window.location.href = `${WEBUI_BASE_URL}/oauth/google/login`;
										}}
									>
										<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" class="h-5 w-5 mr-3">
											<path
												fill="#EA4335"
												d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
											/><path
												fill="#4285F4"
												d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
											/><path
												fill="#FBBC05"
												d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
											/><path
												fill="#34A853"
												d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
											/>
										</svg>
										<span>{$i18n.t('Continue with Google')}</span>
									</button>
								{/if}
							</div>
						{/if}

						<div class="mt-6 text-center">
							{#if mode === 'signin'}
								<p class="text-gray-800 dark:text-gray-200 text-sm">
									{$i18n.t("Don't have an account?")}
									<button
										class="text-blue-600 hover:text-blue-700 dark:text-blue-300 dark:hover:text-blue-200 font-medium ml-1"
										on:click={() => (mode = 'signup')}
									>
										{$i18n.t('Sign Up')}
									</button>
								</p>
							{:else}
								<p class="text-gray-800 dark:text-gray-200 text-sm">
									{$i18n.t('Already have an account?')}
									<button
										class="text-blue-600 hover:text-blue-700 dark:text-blue-300 dark:hover:text-blue-200 font-medium ml-1"
										on:click={() => (mode = 'signin')}
									>
										{$i18n.t('Sign in')}
									</button>
								</p>
								<div class="h-16"></div> 
							{/if}
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>