<script lang="ts">
	import { onMount, getContext, createEventDispatcher } from 'svelte';
	import { settings } from '$lib/stores';
	import { fade } from 'svelte/transition';
	import { toast } from 'svelte-sonner';

	const dispatch = createEventDispatcher();

	// Get i18n from context with proper typing to fix the linter errors
	interface I18nContext {
		t?: (key: string) => string;
	}
	const i18n: I18nContext = getContext('i18n') || {};

	// Safe translation function to handle cases where i18n.t might not be available
	function t(key: string): string {
		if (i18n && typeof i18n.t === 'function') {
			return i18n.t(key);
		}
		// Fallback to the key itself if translation is not available
		return key;
	}

	// Avatar data - each avatar has unique traits that influence their personality
	// These avatars represent different teaching styles for our tutoring platform
	const avatars = [
		{
			id: 'The Scholar',
			name: $i18n.t(`The Scholar`),
			image: '/images/The Scholar.png',
			accentColor: '#2196F3',
			gradientEnd: '#3D5E94',
			description: $i18n.t(
				`Analytical, detail-oriented, methodical, patient. Emphasizes deep understanding with comprehensive explanations.`
			)
		},
		{
			id: 'The Mentor',
			name: $i18n.t(`The Mentor`),
			image: '/images/The Mentor.png',
			accentColor: '#F59E0B',
			gradientEnd: '#3D5E94',
			description: $i18n.t(
				`Encouraging, warm, supportive, insightful. Focuses on building confidence through guided discovery.`
			)
		},
		{
			id: 'The Coach',
			name: $i18n.t(`The Coach`),
			image: '/images/The Coach.png',
			accentColor: '#10B981',
			gradientEnd: '#3D5E94',
			description: $i18n.t(
				`Energetic, motivational, direct, goal-oriented. Emphasizes practical application and quick results.`
			)
		},
		{
			id: 'The Innovator',
			name: $i18n.t(`The Innovator`),
			image: '/images/The Innovator.png',
			accentColor: '#EF4444',
			gradientEnd: '#3D5E94',
			description: $i18n.t(
				`Creative, adaptable, curious, thought-provoking. Explores alternative perspectives and connections.`
			)
		}
	];

	// Default to first avatar on load
	let selectedAvatar = avatars[0].id;

	// Carousel display controls - shows different number of avatars based on screen size
	let visibleIndex = 0;
	let visibleCount = 3; // Default for desktop
	let verticalLayout = false; // Flag for vertical layout

	// Adjust visibleCount based on screen width
	function updateVisibleCount() {
		if (typeof window !== 'undefined') {
			if (window.innerWidth < 640) {
				visibleCount = 4; // Show all avatars in vertical mode
				verticalLayout = true;
			} else if (window.innerWidth < 1024) {
				visibleCount = 2; // Tablet
				verticalLayout = false;
			} else {
				visibleCount = 3; // Desktop
				verticalLayout = false;
			}
		}
	}

	onMount(() => {
		updateVisibleCount();

		// Add resize listener
		window.addEventListener('resize', updateVisibleCount);

		return () => {
			window.removeEventListener('resize', updateVisibleCount);
		};
	});

	// Updates the selected avatar when user makes a selection
	// Does not immediately start chat, just highlights the selection
	const selectAvatar = (avatarId: string) => {
		selectedAvatar = avatarId;
	};

	// Initializes chat with the selected avatar personality
	// This function handles:
	// 1. Updating global settings to enable avatar mode
	// 2. Storing the selected avatar in user preferences
	// 3. Notifying the user of selection
	// 4. Triggering the parent component to start the chat session
	const startChatWithAvatar = (avatarId: string) => {
		selectedAvatar = avatarId;

		const modelSelectorEl = document.querySelector('div.model-selector-value');
		const visibleModelName = modelSelectorEl?.textContent?.trim() || '';
		
		if (visibleModelName && visibleModelName !== 'Select a model') {
			console.log('Ensuring model is set in sessionStorage:', visibleModelName);
			
			const existingModelsStr = window.sessionStorage?.getItem('selectedModels');
			const existingModels = existingModelsStr ? JSON.parse(existingModelsStr) : [];
			
			if (!existingModels || existingModels.length === 0 || existingModels[0] === '') {
				console.log('Setting model in sessionStorage');
				window.sessionStorage.setItem('selectedModels', JSON.stringify([visibleModelName]));
			}
		}
		
		if (typeof window !== 'undefined' && window.sessionStorage) {
			const selectedModelsStr = window.sessionStorage.getItem('selectedModels');
			const selectedModels = selectedModelsStr ? JSON.parse(selectedModelsStr) : [];
			
			if (!selectedModels || selectedModels.length === 0 || selectedModels.every((model: string) => !model || model === '')) {
				if (visibleModelName && visibleModelName !== 'Select a model') {
					console.log('Force setting model as last resort:', visibleModelName);
					window.sessionStorage.setItem('selectedModels', JSON.stringify([visibleModelName]));
				} else {
					toast.error(t('Please select a model before starting a chat'));
					
					if (window.localStorage.getItem('pendingSupportData')) {
						window.localStorage.removeItem('pendingSupportData');
					}
					
					return;
				}
			}
		}

		// Update app settings with avatar preferences
		settings.update((s) => {
			const updatedSettings = { ...s };
			(updatedSettings as any).avatarEnabled = true;
			(updatedSettings as any).selectedAvatarId = avatarId;
			return updatedSettings;
		});

		// Persist settings between sessions
		localStorage.setItem('settings', JSON.stringify($settings));

		// Tell parent component to initialize chat
		dispatch('select', { avatarId });
	};

	// Return to chat type selection screen
	const goBack = () => {
		dispatch('back');
	};

	// Carousel navigation controls
	// These handle the horizontal scrolling when there are more avatars
	// than can fit in the visible area
	const prevSlide = () => {
		if (visibleIndex > 0) {
			visibleIndex--;
		}
	};

	const nextSlide = () => {
		if (visibleIndex < avatars.length - visibleCount) {
			visibleIndex++;
		}
	};
</script>

<div class="avatar-selection-container">
	<div class="selection-wrapper" in:fade={{ duration: 300 }}>
		<!-- Header with back button -->
		<div class="header">
			<button class="back-button" on:click={goBack} aria-label="Go back">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M15 19l-7-7 7-7"
					/>
				</svg>
			</button>
			<h1 class="title">{$i18n.t('Choose your avatar')}</h1>
		</div>

		<!-- Avatar display: vertical on small screens, carousel on larger screens -->
		<div class="avatar-container">
			{#if verticalLayout}
				<!-- Vertical stack layout for small screens -->
				<div class="vertical-layout">
					{#each avatars as avatar}
						<div
							class="vertical-avatar-item {selectedAvatar === avatar.id ? 'selected' : ''}"
							on:click={() => selectAvatar(avatar.id)}
						>
							<div
								class="vertical-avatar-card"
								style="--accent-color: {avatar.accentColor}; {selectedAvatar === avatar.id
									? `border: 2px solid ${avatar.accentColor}`
									: ''}"
							>
								<!-- Card background with subtle pattern -->
								<div
									class="card-bg"
									style="background-image: url('/images/background.jpeg')"
								></div>

								<!-- Avatar image with glow effect -->
								<div class="vertical-avatar-image-container">
									<div class="avatar-glow" style="--glow-color: {avatar.accentColor}"></div>
									<img
										src={avatar.image}
										alt={avatar.name}
										class="avatar-image"
										draggable="false"
									/>
								</div>

								<!-- Avatar info -->
								<div class="vertical-avatar-info">
									<div
										class="name-badge"
										style="background: linear-gradient(135deg, {avatar.accentColor}, {avatar.gradientEnd})"
									>
										<h3 class="vertical-avatar-name">{avatar.name}</h3>
									</div>
									<div class="vertical-avatar-details">
										<p class="vertical-avatar-description">{avatar.description}</p>
										<button
											class="start-chat-button"
											style="background: linear-gradient(135deg, {avatar.accentColor}, {avatar.gradientEnd})"
											on:click|stopPropagation={() => startChatWithAvatar(avatar.id)}
										>
											<span>{$i18n.t('Start Chat')}</span>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												class="h-4 w-4 ml-1"
												viewBox="0 0 20 20"
												fill="currentColor"
											>
												<path
													fill-rule="evenodd"
													d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z"
													clip-rule="evenodd"
												/>
											</svg>
										</button>
									</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<!-- Horizontal carousel for larger screens with enhanced design -->
				<div class="carousel-container">
					<div class="carousel-overflow">
						<div
							class="carousel-track"
							style="transform: translateX(-{visibleIndex * (100 / visibleCount)}%)"
						>
							{#each avatars as avatar, i}
								<div class="avatar-item {selectedAvatar === avatar.id ? 'selected' : ''}">
									<!-- Avatar card -->
									<div
										class="avatar-card"
										style="--accent-color: {avatar.accentColor}"
										on:click={() => selectAvatar(avatar.id)}
									>
										<!-- Card background with library image -->
										<div
											class="card-bg"
											style="background-image: url('/images/background.jpeg')"
										></div>

										<!-- Glow effect for selected avatar -->
										{#if selectedAvatar === avatar.id}
											<div class="avatar-glow" style="--glow-color: {avatar.accentColor}"></div>
										{/if}

										<!-- Title at top of card -->
										<div
											class="card-title"
											style="background: linear-gradient(135deg, {avatar.accentColor}, {avatar.gradientEnd})"
										>
											<h3 class="avatar-name">{avatar.name}</h3>
										</div>

										<!-- Avatar image with spotlight effect -->
										<div class="avatar-spotlight"></div>
										<div class="avatar-image-wrapper">
											<img
												src={avatar.image}
												alt={avatar.name}
												class="avatar-image"
												draggable="false"
											/>
										</div>

										<!-- Card content -->
										<div class="card-content">
											<!-- Info overlay that appears on hover -->
											<div class="info-overlay">
												<p class="avatar-description">{avatar.description}</p>
												<button
													class="start-chat-button"
													style="background: linear-gradient(135deg, {avatar.accentColor}, {avatar.gradientEnd})"
													on:click|stopPropagation={() => startChatWithAvatar(avatar.id)}
												>
													<span>{$i18n.t('Start Chat')}</span>
													<svg
														xmlns="http://www.w3.org/2000/svg"
														class="h-4 w-4 ml-1"
														viewBox="0 0 20 20"
														fill="currentColor"
													>
														<path
															fill-rule="evenodd"
															d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z"
															clip-rule="evenodd"
														/>
													</svg>
												</button>
											</div>
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>

				<!-- Navigation arrows with improved design -->
				<div class="navigation-controls">
					<button
						class="nav-button"
						on:click={prevSlide}
						disabled={visibleIndex === 0}
						class:disabled={visibleIndex === 0}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-6 w-6"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 19l-7-7 7-7"
							/>
						</svg>
					</button>

					<div class="pagination-dots">
						{#each Array(Math.ceil(avatars.length / visibleCount)) as _, i}
							<div
								class="pagination-dot"
								class:active={Math.floor(visibleIndex / visibleCount) === i}
							></div>
						{/each}
					</div>

					<button
						class="nav-button"
						on:click={nextSlide}
						disabled={visibleIndex >= avatars.length - visibleCount}
						class:disabled={visibleIndex >= avatars.length - visibleCount}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-6 w-6"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 5l7 7-7 7"
							/>
						</svg>
					</button>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	/* Container and background styles */
	.avatar-selection-container {
		height: 100vh;
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow-y: auto;
		padding: 0;
		position: relative;
	}

	.selection-wrapper {
		width: 100%;
		max-width: 1200px;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		max-height: 100vh;
		position: relative;
		z-index: 1;
	}

	/* Header styles */
	.header {
		display: flex;
		align-items: center;
		margin-bottom: 2rem;
	}

	.back-button {
		margin-right: 1rem;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2.5rem;
		height: 2.5rem;
		border-radius: 50%;
		color: var(--gray-700, #374151);
		background-color: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(5px);
		transition: all 0.3s ease;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.back-button:hover {
		background-color: rgba(255, 255, 255, 0.2);
		transform: scale(1.05);
	}

	.title {
		font-size: 2rem;
		font-weight: 700;
		color: var(--gray-900, #111827);
		text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		letter-spacing: 0.5px;
	}

	:global(.dark) .back-button {
		color: var(--gray-300, #d1d5db);
	}

	:global(.dark) .title {
		color: white;
	}

	/* Avatar container */
	.avatar-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		width: 100%;
	}

	/* Vertical layout styles */
	.vertical-layout {
		display: flex;
		flex-direction: column;
		width: 100%;
		gap: 1.25rem;
		max-height: 70vh;
		overflow-y: auto;
		padding: 0.5rem;
		scrollbar-width: thin;
		scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
	}

	.vertical-layout::-webkit-scrollbar {
		width: 5px;
	}

	.vertical-layout::-webkit-scrollbar-track {
		background: transparent;
	}

	.vertical-layout::-webkit-scrollbar-thumb {
		background-color: rgba(255, 255, 255, 0.3);
		border-radius: 10px;
	}

	/* Vertical avatar items */
	.vertical-avatar-item {
		width: 100%;
		transition: all 0.3s ease;
	}

	.vertical-avatar-item.selected {
		transform: translateX(5px) scale(1.02);
	}

	.vertical-avatar-card {
		position: relative;
		display: flex;
		border-radius: 1rem;
		overflow: hidden;
		height: 180px;
		box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
		transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
		background-color: rgba(30, 30, 40, 0.6);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	:global(:not(.dark)) .vertical-avatar-card {
		background-color: rgba(40, 40, 50, 0.9);
		box-shadow:
			0 8px 15px rgba(0, 0, 0, 0.12),
			0 3px 8px rgba(0, 0, 0, 0.08);
		filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.12));
		border: 1px solid rgba(0, 0, 0, 0.2);
		backdrop-filter: blur(8px);
	}

	.vertical-avatar-card:hover {
		transform: translateY(-5px);
		box-shadow:
			0 15px 30px -5px rgba(0, 0, 0, 0.5),
			0 0 15px rgba(var(--accent-color-rgb, 33, 150, 243), 0.3);
	}

	:global(:not(.dark)) .vertical-avatar-card:hover {
		transform: translateY(-5px) scale(1.01);
		filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.15));
		box-shadow:
			0 10px 18px rgba(0, 0, 0, 0.1),
			0 4px 10px rgba(0, 0, 0, 0.06);
	}

	.vertical-avatar-item.selected .vertical-avatar-card {
		box-shadow:
			0 0 0 2px var(--accent-color),
			0 15px 30px -5px rgba(0, 0, 0, 0.3),
			0 0 15px rgba(var(--accent-color-rgb, 33, 150, 243), 0.5);
	}

	:global(:not(.dark)) .vertical-avatar-item.selected .vertical-avatar-card {
		filter: drop-shadow(0 8px 15px rgba(0, 0, 0, 0.12))
			drop-shadow(0 0 12px rgba(var(--accent-color-rgb, 33, 150, 243), 0.2));
		box-shadow:
			0 0 0 2px var(--accent-color),
			0 10px 18px rgba(0, 0, 0, 0.1),
			0 4px 8px rgba(0, 0, 0, 0.06);
		background-color: rgba(30, 30, 40, 0.95);
	}

	/* Card background */
	.card-bg {
		position: absolute;
		inset: 0;
		z-index: 1;
		background-size: cover;
		background-position: center;
		opacity: 0.15;
		filter: blur(1px);
	}

	:global(:not(.dark)) .card-bg {
		opacity: 0.25;
		filter: blur(1px) brightness(0.6) contrast(1.2);
	}

	/* Avatar image container */
	.vertical-avatar-image-container {
		width: 40%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
		z-index: 2;
		overflow: hidden;
	}

	.avatar-glow {
		position: absolute;
		width: 120%;
		height: 120%;
		background: radial-gradient(circle, var(--glow-color) 0%, transparent 70%);
		opacity: 0.15;
		filter: blur(15px);
		z-index: 1;
	}

	.avatar-image {
		position: relative;
		z-index: 3;
		width: 100%;
		height: 100%;
		object-fit: contain;
		filter: drop-shadow(0 5px 10px rgba(0, 0, 0, 0.4));
		transition: transform 0.3s ease;
	}

	:global(:not(.dark)) .avatar-image {
		filter: drop-shadow(0 5px 10px rgba(0, 0, 0, 0.6));
	}

	.vertical-avatar-card:hover .avatar-image {
		transform: scale(1.05);
	}

	/* Avatar info */
	.vertical-avatar-info {
		position: absolute;
		right: 0;
		top: 0;
		width: 60%;
		height: 100%;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		justify-content: center;
		z-index: 3;
	}

	.name-badge {
		display: inline-flex;
		padding: 0.2rem 0.6rem;
		border-radius: 9999px;
		margin-bottom: 0.6rem;
		box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
		transform: translateX(-5px);
		transition: transform 0.3s ease;
	}

	.vertical-avatar-card:hover .name-badge {
		transform: translateX(0);
	}

	.vertical-avatar-name {
		color: white;
		font-weight: 600;
		font-size: 0.875rem;
		text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
	}

	/* Details that appear on hover */
	.vertical-avatar-details {
		opacity: 0;
		transform: translateY(10px);
		transition: all 0.3s ease;
	}

	.vertical-avatar-card:hover .vertical-avatar-details,
	.vertical-avatar-item.selected .vertical-avatar-details {
		opacity: 1;
		transform: translateY(0);
	}

	.vertical-avatar-description {
		color: rgba(255, 255, 255, 0.9);
		font-size: 0.7rem;
		line-height: 1.4;
		margin-bottom: 0.75rem;
		text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
	}

	/* Start chat button */
	.start-chat-button {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		padding: 0.5rem 0.75rem;
		border-radius: 0.5rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: white;
		transition: all 0.2s ease;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
		border: none;
		cursor: pointer;
	}

	:global(:not(.dark)) .start-chat-button {
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
		font-weight: 600;
	}

	.start-chat-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 7px 10px rgba(0, 0, 0, 0.2);
	}

	:global(:not(.dark)) .start-chat-button:hover {
		transform: translateY(-2px) scale(1.02);
		box-shadow: 0 7px 12px rgba(0, 0, 0, 0.4);
	}

	.start-chat-button:active {
		transform: translateY(0);
	}

	/* Start chat button - smaller on vertical layout */
	.vertical-avatar-card .start-chat-button {
		padding: 0.4rem 0.6rem;
		font-size: 0.75rem;
	}

	/* Horizontal layout styles */
	.carousel-container {
		position: relative;
		margin-bottom: 2rem;
		width: 100%;
	}

	.carousel-overflow {
		width: 100%;
		overflow: hidden;
		padding: 1rem 0;
	}

	.carousel-track {
		display: flex;
		transition: transform 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
	}

	.avatar-item {
		width: calc(100% / var(--visible-count, 3));
		flex-shrink: 0;
		padding: 0.75rem;
		transition: all 0.3s ease;
		opacity: 0.7;
		transform: scale(0.95);
	}

	.avatar-item.selected {
		opacity: 1;
		transform: scale(1);
	}

	/* Avatar card for horizontal layout */
	.avatar-card {
		position: relative;
		height: 340px;
		width: 100%;
		border-radius: 1rem;
		overflow: hidden;
		box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
		cursor: pointer;
		transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
		background-color: rgba(30, 30, 40, 0.6);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.1);
		display: flex;
		flex-direction: column;
	}

	:global(:not(.dark)) .avatar-card {
		background-color: rgba(40, 40, 50, 0.9);
		box-shadow:
			0 10px 20px rgba(0, 0, 0, 0.15),
			0 5px 10px rgba(0, 0, 0, 0.1);
		filter: drop-shadow(0 5px 15px rgba(0, 0, 0, 0.15));
		border: 1px solid rgba(0, 0, 0, 0.2);
		backdrop-filter: blur(8px);
	}

	.avatar-card:hover {
		transform: translateY(-10px);
		box-shadow:
			0 20px 40px rgba(0, 0, 0, 0.4),
			0 0 20px rgba(var(--accent-color-rgb, 33, 150, 243), 0.3);
	}

	:global(:not(.dark)) .avatar-card:hover {
		filter: drop-shadow(0 8px 20px rgba(0, 0, 0, 0.2));
		box-shadow:
			0 15px 25px rgba(0, 0, 0, 0.12),
			0 5px 12px rgba(0, 0, 0, 0.08);
		transform: translateY(-10px) scale(1.02);
	}

	.avatar-item.selected .avatar-card {
		box-shadow:
			0 0 0 2px var(--accent-color),
			0 20px 40px rgba(0, 0, 0, 0.4),
			0 0 30px rgba(var(--accent-color-rgb, 33, 150, 243), 0.4);
		border-color: var(--accent-color);
	}

	:global(:not(.dark)) .avatar-item.selected .avatar-card {
		filter: drop-shadow(0 10px 20px rgba(0, 0, 0, 0.15))
			drop-shadow(0 0 15px rgba(var(--accent-color-rgb, 33, 150, 243), 0.25));
		box-shadow:
			0 0 0 3px var(--accent-color),
			0 12px 20px rgba(0, 0, 0, 0.12),
			0 5px 12px rgba(0, 0, 0, 0.08);
		border-color: var(--accent-color);
		background-color: rgba(30, 30, 40, 0.95);
	}

	/* Spotlight effect */
	.avatar-spotlight {
		position: absolute;
		top: -50%;
		left: -50%;
		width: 200%;
		height: 200%;
		background: radial-gradient(ellipse at center, rgba(255, 255, 255, 0.1) 0%, transparent 60%);
		transform: scale(0.8);
		opacity: 0;
		transition: all 1s ease;
		z-index: 2;
		pointer-events: none;
	}

	.avatar-card:hover .avatar-spotlight {
		opacity: 1;
		transform: scale(1) rotate(-10deg);
	}

	/* Add wrapper for avatar image in horizontal layout */
	.avatar-image-wrapper {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		height: 75%;
		z-index: 2;
		display: flex;
		align-items: flex-end;
		justify-content: center;
		margin-top: 2.5rem; /* Add margin to avoid overlap with the title */
	}

	/* Adjust avatar image for horizontal layout */
	.avatar-card .avatar-image {
		max-height: 90%;
		width: auto;
		object-fit: contain;
		object-position: bottom;
		margin-bottom: 0;
	}

	/* Card content positioning update */
	.card-content {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		padding: 1.5rem;
		z-index: 3;
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		background: linear-gradient(
			to top,
			rgba(0, 0, 0, 0.7) 0%,
			rgba(0, 0, 0, 0.4) 50%,
			transparent 100%
		);
	}

	:global(:not(.dark)) .card-content {
		background: linear-gradient(
			to top,
			rgba(0, 0, 0, 0.8) 0%,
			rgba(0, 0, 0, 0.5) 50%,
			transparent 100%
		);
	}

	/* Info overlay for horizontal layout */
	.info-overlay {
		margin-top: 1rem;
		opacity: 0;
		transform: translateY(10px);
		transition: all 0.3s ease;
		width: 100%;
	}

	.avatar-card:hover .info-overlay,
	.avatar-item.selected .avatar-card .info-overlay {
		opacity: 1;
		transform: translateY(0);
	}

	.avatar-name {
		color: white;
		font-weight: 600;
		font-size: 1rem;
		text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
	}

	.avatar-description {
		color: rgba(255, 255, 255, 0.9);
		font-size: 0.8rem;
		line-height: 1.5;
		margin-bottom: 1rem;
		text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
	}

	/* Navigation controls */
	.navigation-controls {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1.5rem;
		margin-bottom: 1.5rem;
	}

	.nav-button {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 3rem;
		height: 3rem;
		background-color: rgba(255, 255, 255, 0.1);
		border-radius: 50%;
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
		color: white;
		transition: all 0.2s ease;
		backdrop-filter: blur(5px);
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	:global(:not(.dark)) .nav-button {
		background-color: rgba(40, 40, 50, 0.8);
		border: 1px solid rgba(0, 0, 0, 0.1);
		box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
		color: white;
		filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.1));
	}

	.nav-button:hover:not(.disabled) {
		background-color: rgba(255, 255, 255, 0.2);
		transform: scale(1.05);
	}

	:global(:not(.dark)) .nav-button:hover:not(.disabled) {
		background-color: rgba(50, 50, 60, 0.9);
		box-shadow: 0 6px 12px rgba(0, 0, 0, 0.25);
		transform: scale(1.05);
	}

	.nav-button.disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.pagination-dots {
		display: flex;
		gap: 0.5rem;
	}

	.pagination-dot {
		width: 0.5rem;
		height: 0.5rem;
		border-radius: 50%;
		background-color: rgba(255, 255, 255, 0.3);
		transition: all 0.2s ease;
	}

	:global(:not(.dark)) .pagination-dot {
		background-color: rgba(50, 50, 60, 0.5);
	}

	.pagination-dot.active {
		background-color: white;
		box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
		transform: scale(1.2);
	}

	:global(:not(.dark)) .pagination-dot.active {
		background-color: rgba(60, 60, 70, 0.9);
		box-shadow: 0 0 8px rgba(0, 0, 0, 0.3);
	}

	/* Responsive adjustments */
	@media (min-width: 640px) {
		.avatar-card {
			height: 380px;
		}

		.avatar-item {
			--visible-count: 2;
		}

		.title {
			font-size: 2.25rem;
		}

		/* Make avatar images slightly bigger on medium screens */
		.avatar-image-wrapper {
			height: 75%;
		}

		.avatar-card .avatar-image {
			max-height: 95%;
		}
	}

	@media (min-width: 1024px) {
		.avatar-card {
			height: 420px;
		}

		.avatar-item {
			--visible-count: 3;
			padding: 1rem;
		}

		.title {
			font-size: 2.5rem;
		}

		/* Make avatar images even bigger on large screens */
		.avatar-image-wrapper {
			height: 80%;
		}

		.avatar-card .avatar-image {
			max-height: 100%;
			transform: scale(1.05);
		}

		.avatar-card:hover .avatar-image {
			transform: scale(1.1);
		}
	}

	/* Height-based adjustments */
	@media (max-height: 700px) {
		.title {
			font-size: 1.75rem;
		}

		.avatar-card {
			height: 300px;
		}

		.vertical-avatar-card {
			height: 160px;
		}

		.header {
			margin-bottom: 1rem;
		}
	}

	@media (max-height: 500px) {
		.title {
			font-size: 1.5rem;
		}

		.avatar-card {
			height: 240px;
		}

		.vertical-avatar-card {
			height: 140px;
		}

		.vertical-layout {
			gap: 0.75rem;
		}

		.header {
			margin-bottom: 0.75rem;
		}
	}

	/* Position card title consistently in both layouts */
	.card-title {
		position: absolute;
		top: 0.75rem;
		left: 0.75rem;
		z-index: 10;
		padding: 0.25rem 0.75rem;
		border-radius: 9999px;
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
		transform: translateY(0);
		transition: transform 0.3s ease;
	}

	:global(:not(.dark)) .card-title {
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
	}

	/* Vertical layout card title styles */
	.vertical-avatar-card .card-title {
		position: absolute;
		top: 0.75rem;
		left: 0.75rem;
		z-index: 10;
	}

	.vertical-avatar-card:hover .card-title {
		transform: translateY(-2px);
	}
</style>
