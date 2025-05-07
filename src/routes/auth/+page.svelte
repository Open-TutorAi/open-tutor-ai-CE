<script>
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import ForgotPassword from '$lib/components/ForgotPassword.svelte';

	import { getBackendConfig } from '$lib/apis';
	import { ldapUserSignIn, getSessionUser, userSignIn, userSignUp, getUserCount } from '$lib/apis/auths';

	import { TUTOR_API_BASE_URL, TUTOR_BASE_URL } from '$lib/constants';
	import { TUTOR_NAME, config, user, socket } from '$lib/stores';

	import { generateInitialsImage, canvasPixelTest } from '$lib/utils';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import OnBoarding from '$lib/components/OnBoarding.svelte';
	import RoleSelection from '$lib/components/RoleSelectionPage.svelte';

	const i18n = getContext('i18n');

	let loaded = false;
	let showForgotPassword = false;
	let mode = $config?.features.enable_ldap ? 'ldap' : 'signin'; // Default is signin
	let firstName = '';
	let lastName = '';
	let email = '';
	let password = '';
	let showPassword = false;
	let role = ''; // No default role now as it will be chosen in the role selection page
	let rememberMe = false;
	let ldapUsername = '';
	let onboarding = false;
	let isFirstUser = false;

	// State to track signup steps
	let signupStep = 1; // 1: Role selection, 2: Account information

	const querystringValue = (key) => {
		const querystring = window.location.search;
		const urlParams = new URLSearchParams(querystring);
		return urlParams.get(key);
	};

	const setSessionUser = async (sessionUser) => {
		if (sessionUser) {
			console.log('Session user received:', sessionUser);
			toast.success($i18n.t(`You're now logged in.`));
			if (sessionUser.token) {
				localStorage.token = sessionUser.token;
			}

			if ($socket) {
				$socket.emit('user-join', { auth: { token: sessionUser.token } });
			}
			await user.set(sessionUser);
			await config.set(await getBackendConfig());

			// Redirect based on user role with explicit logging
			console.log('Redirecting based on role:', sessionUser.role);

			try {
				if (sessionUser.role) {
					console.log(`Redirecting to ${sessionUser.role} page`);
					// window.location.href = `/${sessionUser.role}`;
					if (sessionUser.role == 'user') {
						window.location.href = '/student/dashboard';
					}else if (sessionUser.role == 'teacher') {
						window.location.href = '/teacher';
					}else if (sessionUser.role == 'parent') {
						window.location.href = '/parent';
					}
				} else {
					console.log('Unknown role, redirecting to default page');
					const redirectPath = querystringValue('redirect') || '/';
					window.location.href = redirectPath;
				}
			} catch (error) {
				console.error('Error during redirection:', error);
				// Fallback to home page if redirection fails
				window.location.href = '/';
			}
		} else {
			console.error('No session user received');
			toast.error($i18n.t('Login failed. Please try again.'));
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
		console.log(`Creating account with role: ${role}`);

		const sessionUser = await userSignUp(
			name,
			email,
			password,
			generateInitialsImage(name),
			role
		).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

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
	}

	// Check if this is the first user to register
	const checkIfFirstUser = async () => {
		try {
			const userCountResult = await getUserCount();
			isFirstUser = userCountResult && userCountResult.count === 0;
			console.log('Is first user:', isFirstUser);
			// If first user, set role to admin and skip to step 2
			if (isFirstUser && mode === 'signup') {
				role = 'admin';
				signupStep = 2;
			}
		} catch (error) {
			console.error('Error checking user count:', error);
		}
	};

	// Handle role selection from the RoleSelection component
	const handleRoleSelected = (event) => {
		role = event.detail.role;
		console.log(`Role selected: ${role}`);
		// Proceed to the next step of signup
		signupStep = 2;
	};

	// Handle going back from role selection
	const handleGoBack = () => {
		// If at role selection step, switch to signin mode
		if (signupStep === 1) {
			mode = 'signin';
		}
	};

	// Function to go back to role selection from account info
	const goBackToRoleSelection = () => {
		// Don't allow going back to role selection if first user (admin)
		if (isFirstUser) return;
		signupStep = 1;
	};

	onMount(async () => {
		if ($user !== undefined) {
			// Redirect based on user role if already logged in
			if ($user.role == 'user') {
				await goto('/student/dashboard');
			}
			await goto(`/${$user.role}`);
		}
		await checkOauthCallback();

		loaded = true;
		if (($config?.features.auth_trusted_header ?? false) || $config?.features.auth === false) {
			await signInHandler();
		} else {
			onboarding = $config?.onboarding ?? false;

			// Check user count when entering signup mode
			if (mode === 'signup') {
				await checkIfFirstUser();
			}
		}
	});
</script>

<svelte:head>
	<title>
		{mode === 'signup'
			? signupStep === 1
				? $i18n.t('Choose Your Role')
				: $i18n.t('Create Account')
			: $i18n.t('Sign in')} | OpenTutorAI
	</title>
	<!-- Standard favicon for most browsers -->
	<link rel="icon" href="favicon/favicon.ico" type="image/x-icon" />
	<!-- PNG version for browsers that support it -->
	<link rel="icon" href="favicon/favicon-96x96.png" type="image/png" />
	<!-- Apple Touch Icon for iOS devices -->
	<link rel="apple-touch-icon" href="favicon/apple-touch-icon.png" />
	<!-- Web app manifests for mobile devices -->
	<link rel="manifest" href="favicon/site.webmanifest" />
</svelte:head>
{#if showForgotPassword}
	<ForgotPassword on:close={() => (showForgotPassword = false)} />
{/if}
<OnBoarding
	bind:show={onboarding}
	getStartedHandler={async () => {
		onboarding = false;
		mode = $config?.features.enable_ldap ? 'ldap' : 'signup';
		if (mode === 'signup') {
			await checkIfFirstUser();
			if (!isFirstUser) {
				signupStep = 1; // Show role selection first if not first user
			}
		}
	}}
/>

<div
	class="min-h-screen bg-gray-50 dark:bg-gray-900 relative"
	style="height: 100vh; overflow-y: auto;"
>
	<div class="w-full absolute top-0 left-0 right-0 h-8 drag-region" />

	{#if loaded}
		<!-- Show Role Selection Page if in signup mode and on step 1 and not first user -->
		{#if mode === 'signup' && signupStep === 1 && !isFirstUser}
			<RoleSelection on:roleSelected={handleRoleSelected} on:goBack={handleGoBack} />
		{:else}
			<div class="flex flex-col md:flex-row w-full" style="min-height: calc(100vh - 8px);">
				<!-- Left panel with branding and features -->
				<div
					class="w-full md:w-2/5 p-6 flex flex-col justify-center items-center min-h-screen"
					style="background: linear-gradient(135deg, #1e3a8a, #6d28d9); color: white; border-radius: 0px; overflow: hidden;"
					role="complementary"
				>
					<!-- Logo -->
					<div class="flex items-center justify-center mb-3">
						<img
							crossorigin="anonymous"
							src="{TUTOR_BASE_URL}/static/splash.png"
							class="w-28 h-28 rounded-full bg-white p-3 shadow-lg"
							alt="logo"
						/>
					</div>

					<!-- Title Section -->
					<p class="text-3xl font-extrabold font-InstrumentSerif text-center leading-snug">
						{$i18n.t('Welcome to')}
						<span class="text-cyan-300">OpenTutorAI</span>
					</p>
					<p class="text-md opacity-95 font-InstrumentSerif text-center italic mt-2">
						{$i18n.t('Ton chemin vers un apprentissage plus intelligent')}
					</p>

					<!-- Illustration -->
					<div class="flex justify-center items-center mt-5">
						<img
							src="/grad-students.png"
							alt={$i18n.t('Graduation illustration')}
							class="w-60 md:w-72 rounded-xl"
						/>
					</div>
				</div>

				<!-- Right panel with authentication form -->
				<div
					class="w-full md:w-3/5 flex justify-center p-8 bg-white dark:bg-gray-900 md:h-screen overflow-y-auto"
					style="max-height: 100vh;"
					role="main"
				>
					<div class="w-full max-w-md py-4 md:py-8 pb-12">
						{#if ($config?.features.auth_trusted_header ?? false) || $config?.features.auth === false}
							<div class="text-center mb-6">
								<div
									class="flex items-center justify-center gap-3 text-xl sm:text-2xl font-semibold dark:text-gray-200"
								>
									<div>
										{$i18n.t('Signing in to {{TUTOR_NAME}}', { TUTOR_NAME: $TUTOR_NAME })}
									</div>
									<div>
										<Spinner />
									</div>
								</div>
							</div>
						{:else}
							<div class="mb-8">
								<!-- Show back button if in signup mode step 2 and not the first user -->
								{#if mode === 'signup' && signupStep === 2 && !isFirstUser}
									<button
										on:click={goBackToRoleSelection}
										class="flex items-center text-blue-600 hover:text-blue-700 mb-4"
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="h-5 w-5 mr-1"
											viewBox="0 0 20 20"
											fill="currentColor"
										>
											<path
												fill-rule="evenodd"
												d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z"
												clip-rule="evenodd"
											/>
										</svg>
										{$i18n.t('Back to Role Selection')}
									</button>
								{/if}

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
									<!-- Show chosen role badge or admin notification -->
									{#if role}
										<div class="mb-2">
											{#if isFirstUser}
												<div class="mb-4 p-3 bg-blue-50 text-blue-800 rounded-md">
													<p class="font-medium">{$i18n.t('First User Setup')}</p>
													<p class="text-sm">{$i18n.t('You are the first user to register. You will be created as an administrator.')}</p>
												</div>
											{/if}
											<span
												class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
												{role === 'user'
													? 'bg-blue-100 text-blue-800'
													: role === 'teacher'
														? 'bg-emerald-100 text-emerald-800'
														: role === 'admin'
															? 'bg-purple-100 text-purple-800'
															: 'bg-purple-100 text-purple-800'}"
											>
												{role === 'user' 
													? '👨‍🎓' 
													: role === 'teacher' 
														? '👨‍🏫' 
														: role === 'admin'
															? '👨‍💼'
															: '👨‍👧'}
												{role === 'user'
													? $i18n.t('Student')
													: role === 'teacher'
														? $i18n.t('Teacher')
														: role === 'admin'
															? $i18n.t('Administrator')
															: $i18n.t('Parent')}
											</span>
										</div>
									{/if}

									<div class="grid grid-cols-2 gap-4">
										<div>
											<label
												for="firstName"
												class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
											>
												{$i18n.t('First Name')}
											</label>
											<input
												id="firstName"
												bind:value={firstName}
												type="text"
												class="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-black dark:text-white"
												placeholder={$i18n.t('Enter Your First Name')}
												required
											/>
										</div>
										<div>
											<label
												for="lastName"
												class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
											>
												{$i18n.t('Last Name')}
											</label>
											<input
												id="lastName"
												bind:value={lastName}
												type="text"
												class="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-black dark:text-white"
												placeholder={$i18n.t('Enter Your Last Name')}
												required
											/>
										</div>
									</div>
								{/if}

								{#if mode === 'ldap'}
									<div>
										<label
											for="username"
											class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
										>
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
										<label
											for="email"
											class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
										>
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
										<label
											for="password"
											class="block text-sm font-medium text-gray-700 dark:text-gray-300"
										>
											{$i18n.t('Password')}
										</label>
										{#if mode === 'signin'}
											<a
												href="#"
												class="text-sm text-blue-500 hover:text-blue-600 dark:text-blue-400"
												on:click|preventDefault={() => (showForgotPassword = true)}
											>
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
									<div class="flex items-center">
										<input
											id="terms"
											type="checkbox"
											class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-600"
											required
										/>
										<label for="terms" class="ml-2 block text-sm text-gray-800 dark:text-gray-200">
											{$i18n.t('I agree to the')}
											<a
												href="#"
												class="text-blue-600 hover:text-blue-700 dark:text-blue-300 dark:hover:text-blue-200"
											>
												{$i18n.t('Terms of Service')}
											</a>
											{$i18n.t('and')}
											<a
												href="#"
												class="text-blue-600 hover:text-blue-700 dark:text-blue-300 dark:hover:text-blue-200"
											>
												{$i18n.t('Privacy Policy')}
											</a>
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
											<label
												for="remember-me"
												class="ml-2 block text-sm text-gray-700 dark:text-gray-300"
											>
												{$i18n.t('Remember me')}
											</label>
										</div>
									</div>
								{/if}

								<button
									type="submit"
									class="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2.5 px-4 rounded-md transition duration-150 ease-in-out"
									disabled={mode === 'signup' && !role}
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
									<span class="flex-shrink mx-4 text-gray-700 dark:text-gray-300"
										>{$i18n.t('OR')}</span
									>
									<div class="flex-grow border-t border-gray-300 dark:border-gray-700"></div>
								</div>

								<div class="space-y-3 overflow-y-auto">
									{#if $config?.oauth?.providers?.google || true}
										<button
											class="w-full flex items-center justify-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md py-2.5 px-4 text-gray-700 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-700"
											on:click={() => {
												window.location.href = `${TUTOR_BASE_URL}/oauth/google/login`;
											}}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 48 48"
												class="h-5 w-5 mr-3"
											>
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
								{#if mode === 'signup'}
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
								{:else}
									<p class="text-gray-800 dark:text-gray-200 text-sm">
										{$i18n.t("Don't have an account?")}
										<button
											class="text-blue-600 hover:text-blue-700 dark:text-blue-300 dark:hover:text-blue-200 font-medium ml-1"
											on:click={async () => {
												mode = 'signup';
												await checkIfFirstUser(); // Check if first user when clicking signup
												if (!isFirstUser) {
													signupStep = 1; // Start with role selection if not first user
												}
											}}
										>
											{$i18n.t('Sign up')}
										</button>
									</p>
								{/if}
							</div>
						{/if}
					</div>
				</div>
			</div>
		{/if}
	{/if}
</div>