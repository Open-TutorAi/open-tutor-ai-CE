<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';

	import { user } from '$lib/stores';
	import { updateUserProfile, getSessionUser } from '$lib/apis/auths';

	import UpdatePassword from '$lib/components/chat/Settings/Account/UpdatePassword.svelte';
	import { getGravatarUrl } from '$lib/apis/utils';
	import { generateInitialsImage, canvasPixelTest } from '$lib/utils';
	import { settings, theme } from '$lib/stores';
	import { getLanguages } from '$lib/i18n';


	const i18n = getContext('i18n');

	export let saveHandler: Function = () => {};

	let profileImageUrl = '';
	let name = '';

	let profileImageInputElement: HTMLInputElement;

	let themes = ['system', 'dark', 'light'];
	let selectedTheme = 'light';
	let languages: Awaited<ReturnType<typeof getLanguages>> = [];
	let lang = $i18n.language;

	const applyTheme = (_theme: string) => {
		let themeToApply = _theme === 'oled-dark' ? 'dark' : _theme;

		if (_theme === 'system') {
			themeToApply = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
		}

		themes
			.filter((e) => e !== themeToApply)
			.forEach((e) => {
				e.split(' ').forEach((cls) => document.documentElement.classList.remove(cls));
			});

		themeToApply.split(' ').forEach((cls) => document.documentElement.classList.add(cls));
	};

	const themeChangeHandler = (_theme: string) => {
		theme.set(_theme);
		localStorage.setItem('theme', _theme);
		applyTheme(_theme);
		selectedTheme = _theme;
	};


	const submitHandler = async () => {
		if (name !== $user.name) {
			if (profileImageUrl === generateInitialsImage($user.name) || profileImageUrl === '') {
				profileImageUrl = generateInitialsImage(name);
			}
		}

		const updatedUser = await updateUserProfile(localStorage.token, name, profileImageUrl).catch(
			(error) => {
				toast.error(`${error}`);
			}
		);

		if (updatedUser) {
			// Get Session User Info
			const sessionUser = await getSessionUser(localStorage.token).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			await user.set(sessionUser);
			return true;
		}
		return false;
	};

	onMount(async () => {
		name = $user.name;
		profileImageUrl = $user.profile_image_url;

		selectedTheme = localStorage.theme ?? 'system';
		applyTheme(selectedTheme);

		languages = await getLanguages();
		lang = $i18n.language;
	});
</script>

<div class="flex flex-col h-full justify-between text-sm text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-900 rounded-2xl shadow-lg p-5">
	<div class="space-y-4 overflow-y-scroll max-h-[28rem] lg:max-h-full custom-scrollbar">
		<input
			id="profile-image-input"
			bind:this={profileImageInputElement}
			type="file"
			hidden
			accept="image/*"
			on:change={(e) => {
				const files = profileImageInputElement.files ?? [];
				let reader = new FileReader();
				reader.onload = (event) => {
					let originalImageUrl = `${event.target.result}`;

					const img = new Image();
					img.src = originalImageUrl;

					img.onload = function () {
						const canvas = document.createElement('canvas');
						const ctx = canvas.getContext('2d');

						// Calculate the aspect ratio of the image
						const aspectRatio = img.width / img.height;

						// Calculate the new width and height to fit within 250x250
						let newWidth, newHeight;
						if (aspectRatio > 1) {
							newWidth = 250 * aspectRatio;
							newHeight = 250;
						} else {
							newWidth = 250;
							newHeight = 250 / aspectRatio;
						}

						// Set the canvas size
						canvas.width = 250;
						canvas.height = 250;

						// Calculate the position to center the image
						const offsetX = (250 - newWidth) / 2;
						const offsetY = (250 - newHeight) / 2;

						// Draw the image on the canvas
						ctx.drawImage(img, offsetX, offsetY, newWidth, newHeight);

						// Get the base64 representation of the compressed image
						const compressedSrc = canvas.toDataURL('image/jpeg');

						// Display the compressed image
						profileImageUrl = compressedSrc;

						profileImageInputElement.files = null;
					};
				};

				if (
					files.length > 0 &&
					['image/gif', 'image/webp', 'image/jpeg', 'image/png'].includes(files[0]['type'])
				) {
					reader.readAsDataURL(files[0]);
				}
			}}
		/>

		<div class="space-y-2">
			<!-- <div class=" text-sm font-medium">{$i18n.t('Account')}</div> -->

			<div class="flex space-x-5 items-center">
				<div class="flex flex-col">
					<div class="self-center mt-2">
						<button
							class="relative rounded-full border-4 border-white shadow-md dark:border-gray-800 transition hover:scale-105"
							type="button"
							on:click={() => {
								profileImageInputElement.click();
							}}
						>
							<img
								src={profileImageUrl !== '' ? profileImageUrl : generateInitialsImage(name)}
								alt="profile"
								crossorigin="anonymous"
								class="rounded-full size-20 object-cover"
							/>

							<div
								class="absolute flex justify-center rounded-full bottom-0 left-0 right-0 top-0 h-full w-full overflow-hidden bg-gray-700 bg-fixed opacity-0 transition duration-300 ease-in-out hover:opacity-50"
							>
								<div class="absolute flex justify-center items-center inset-0 rounded-full bg-black/50 opacity-0 hover:opacity-100 transition duration-300">
									<svg
										xmlns="http://www.w3.org/2000/svg"
										viewBox="0 0 20 20"
										fill="currentColor"
										class="w-6 h-6 text-white"
									>
										<path
											d="m2.695 14.762-1.262 3.155a.5.5 0 0 0 .65.65l3.155-1.262a4 4 0 0 0 1.343-.886L17.5 5.501a2.121 2.121 0 0 0-3-3L3.58 13.419a4 4 0 0 0-.885 1.343Z"
										/>
									</svg>
								</div>
							</div>
						</button>
					</div>
				</div>

				<div class="flex-1 flex flex-col self-center gap-1">
					<div class="text-sm font-semibold text-gray-700 dark:text-gray-300">{$i18n.t('Profile Image')}</div>

					<div class="flex gap-2 flex-wrap">
						<button
							class="text-xs text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 px-4 py-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition"
							on:click={async () => {
								if (canvasPixelTest()) {
									profileImageUrl = generateInitialsImage(name);
								} else {
									toast.info(
										$i18n.t(
											'Fingerprint spoofing detected: Unable to use initials as avatar. Defaulting to default profile image.'
										),
										{
											duration: 1000 * 10
										}
									);
								}
							}}>{$i18n.t('Use Initials')}</button
						>

						<button
							class="text-xs text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 px-4 py-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition"
							on:click={async () => {
								const url = await getGravatarUrl(localStorage.token, $user.email);
								console.log('Gravatar URL:', url);
								if (url) {
									profileImageUrl = url;
								} else {
									profileImageUrl = '/user.png'; // fallback
									toast.error('Failed to load Gravatar image');
								}
								profileImageInputElement.value = '';
								}}
							>
							{$i18n.t('Use Gravatar')}
						</button>



						<button
							class="text-xs text-red-600 bg-gray-100 dark:bg-gray-800 px-3 py-1 rounded-lg hover:bg-red-100 dark:hover:bg-red-900 transition"
							on:click={async () => {
								profileImageUrl = '/user.png';
							}}>{$i18n.t('Remove')}</button
						>
					</div>
				</div>
			</div>

			<div class="pt-2">
				<div class="flex flex-col w-full">
					<div class="mb-1 text-xs font-semibold text-gray-600 dark:text-gray-400">{$i18n.t('Name')}</div>

					<div class="flex-1">
						<input
							class="w-full rounded-xl py-2 px-4 text-sm dark:text-white bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 transition focus:ring-inset"
							type="text"
							bind:value={name}
							required
						/>
					</div>
				</div>
			</div>
		</div>

		<div class="pt-2">
			<UpdatePassword />
		</div>

		<!-- UI Preferences -->
		<div class="space-y-3 pt-2">
			<div class="flex w-full justify-between">
				<div class="self-center text-xs font-medium">{$i18n.t('Theme')}</div>
				<div class="flex items-center relative">
					<select
						class="dark:bg-gray-900 w-fit pr-8 rounded-sm py-2 px-2 text-xs bg-transparent outline-hidden text-right"
						bind:value={selectedTheme}
						on:change={() => themeChangeHandler(selectedTheme)}
					>
						<option value="system">💻 {$i18n.t('System')}</option>
						<option value="dark">🌑 {$i18n.t('Dark')}</option>
						<option value="light">☀️ {$i18n.t('Light')}</option>
					</select>
				</div>
			</div>

			<div class="flex w-full justify-between">
				<div class="self-center text-xs font-medium">{$i18n.t('Language')}</div>
				<div class="flex items-center relative">
					<select
						class="dark:bg-gray-900 w-fit pr-8 rounded-sm py-2 px-2 text-xs bg-transparent outline-hidden text-right"
						bind:value={lang}
						on:change={async () => {
							$i18n.changeLanguage(lang);
							localStorage.setItem('lang', lang);
						}}
					>
						{#each languages as l}
							<option value={l.code}>{l.title}</option>
						{/each}
					</select>
				</div>
			</div>
		</div>

		<hr class="border-t border-gray-200 dark:border-gray-700 my-4" />

	</div>

	<div class="flex justify-end pt-4">
		<button
			class="px-4 py-2 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white dark:bg-gradient-to-r dark:from-blue-600 dark:to-indigo-600 dark:hover:from-blue-700 dark:hover:to-indigo-700 rounded-full transition"
			on:click={async () => {
				const res = await submitHandler();

				if (res) {
					toast.success($i18n.t('Changes updated successfully'));
					saveHandler();
				}
			}}
		>
			{$i18n.t('Save')}
		</button>
	</div>
</div>
