<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import * as THREE from 'three';
	import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
	import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { settings } from '$lib/stores';

	// Props
	export let active = false; // Whether the avatar should be shown
	export let message = ''; // Current message to speak
	export let speaking = false; // Whether the avatar is speaking

	// State variables
	let avatarContainer: HTMLDivElement;
	let scene: THREE.Scene;
	let camera: THREE.PerspectiveCamera;
	let renderer: THREE.WebGLRenderer;
	let controls: OrbitControls;
	let avatar: THREE.Object3D;
	let headMesh: any; // For accessing morph targets
	let animationFrameId: number;
	let loading = true;
	let speechSynthesis = window.speechSynthesis;
	let voices: SpeechSynthesisVoice[] = [];
	let isSpeaking = false;
	let currentViseme = 0;
	let visemeSequence: { viseme: string; duration: number }[] = [];
	let visemeTimer: number | null = null;

	const dispatch = createEventDispatcher();

	onMount(async () => {
		// Initialize 3D renderer
		await initThreeJs();

		// Set up voice options once the browser has loaded them
		speechSynthesis.onvoiceschanged = () => {
			voices = speechSynthesis.getVoices();
			console.log('Available voices:', voices);
		};

		// Request voices immediately in case they're already loaded
		voices = speechSynthesis.getVoices();
	});

	onDestroy(() => {
		// Clean up resources
		if (animationFrameId) {
			cancelAnimationFrame(animationFrameId);
		}

		if (renderer) {
			renderer.dispose();
		}

		// Stop any ongoing speech
		if (speechSynthesis) {
			speechSynthesis.cancel();
		}

		// Clear viseme animation
		if (visemeTimer) {
			clearTimeout(visemeTimer);
		}
	});

	async function initThreeJs() {
		if (!avatarContainer) return;

		// Create scene
		scene = new THREE.Scene();
		scene.background = new THREE.Color(0x2d3250); // Dark blue background that's semi-transparent

		// Get container dimensions
		const width = avatarContainer.clientWidth;
		const height = avatarContainer.clientHeight;

		// Create camera
		camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
		camera.position.set(0, 1.6, 2.2); // Position to show head and shoulders

		// Create renderer
		renderer = new THREE.WebGLRenderer({
			antialias: true,
			alpha: true // Enable transparency
		});
		renderer.setSize(width, height);
		renderer.setPixelRatio(window.devicePixelRatio);
		renderer.outputColorSpace = THREE.SRGBColorSpace;
		avatarContainer.appendChild(renderer.domElement);

		// Add lighting
		const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
		scene.add(ambientLight);

		const directionalLight = new THREE.DirectionalLight(0xffffff, 1.7);
		directionalLight.position.set(0.5, 2, 1);
		scene.add(directionalLight);

		// Add orbit controls
		controls = new OrbitControls(camera, renderer.domElement);
		controls.enableDamping = true;
		controls.dampingFactor = 0.05;
		controls.minDistance = 1;
		controls.maxDistance = 5;
		controls.target.set(0, 1.5, 0); // Look at head height
		controls.update();

		// Load avatar model
		await loadAvatar('backend/avatar/glb/Masculine_TPose.glb');

		// Start animation loop
		animate();

		// Handle window resize
		window.addEventListener('resize', handleResize);
	}

	async function loadAvatar(modelPath: string) {
		loading = true;
		const loader = new GLTFLoader();

		try {
			const gltf = await new Promise((resolve, reject) => {
				loader.load(
					modelPath,
					(gltf) => resolve(gltf),
					(xhr) => {
						console.log(`${(xhr.loaded / (xhr.total || 1)) * 100}% loaded`);
					},
					(error) => {
						console.error('Error loading GLTF model:', error);
						reject(error);
					}
				);
			});

			avatar = gltf.scene;
			scene.add(avatar);

			// Find head mesh with morph targets (for viseme animation)
			avatar.traverse((node) => {
				const mesh = node as THREE.Mesh;
				if (
					mesh.morphTargetDictionary &&
					mesh.morphTargetInfluences &&
					mesh.morphTargetDictionary['viseme_sil'] !== undefined
				) {
					headMesh = mesh;
					console.log('Found head mesh with visemes:', mesh.morphTargetDictionary);
				}
			});

			// Center avatar in frame
			const box = new THREE.Box3().setFromObject(avatar);
			const size = box.getSize(new THREE.Vector3());
			const center = box.getCenter(new THREE.Vector3());

			avatar.position.set(-center.x, -center.y + size.y / 2, -center.z);
			loading = false;
		} catch (error) {
			console.error('Error loading avatar:', error);
			loading = false;
		}
	}

	function animate() {
		animationFrameId = requestAnimationFrame(animate);

		if (controls) {
			controls.update();
		}

		if (renderer && scene && camera) {
			renderer.render(scene, camera);
		}
	}

	function handleResize() {
		if (!avatarContainer || !camera || !renderer) return;

		const width = avatarContainer.clientWidth;
		const height = avatarContainer.clientHeight;

		// Update camera
		camera.aspect = width / height;
		camera.updateProjectionMatrix();

		// Update renderer
		renderer.setSize(width, height);
	}

	// Watch for changes in message prop to speak new messages
	$: if (message && active && speaking) {
		speakText(message);
	}

	function speakText(text: string) {
		// Stop any ongoing speech
		speechSynthesis.cancel();

		// Reset animation
		resetVisemes();

		// Create a new utterance
		const utterance = new SpeechSynthesisUtterance(text);

		// Choose a voice (preferably a natural sounding one)
		const preferredVoice = voices.find(
			(voice) =>
				voice.name.includes('Google') ||
				voice.name.includes('Natural') ||
				voice.name.includes('Premium')
		);

		if (preferredVoice) {
			utterance.voice = preferredVoice;
		}

		// Set properties
		utterance.rate = 1.0;
		utterance.pitch = 1.0;
		utterance.volume = 1.0;

		// Create basic viseme sequence (simplistic approach)
		createVisemeSequence(text);

		// Set up events
		utterance.onstart = () => {
			isSpeaking = true;
			animateMouth();
		};

		utterance.onend = () => {
			isSpeaking = false;
			resetVisemes();
			dispatch('speechend');
		};

		utterance.onerror = () => {
			isSpeaking = false;
			resetVisemes();
			dispatch('speechend');
		};

		// Speak the text
		speechSynthesis.speak(utterance);
	}

	function createVisemeSequence(text: string) {
		// This is a simplified approach - in a real implementation you'd use proper phoneme-to-viseme mapping
		// For now, we'll create a sequence based on word length and punctuation

		visemeSequence = [];

		// Split text into words and punctuation
		const words = text.match(/[\w']+|[.,!?;]/g) || [];

		words.forEach((word) => {
			// Punctuation gets a pause
			if (/[.,!?;]/.test(word)) {
				visemeSequence.push({ viseme: 'viseme_sil', duration: 200 });
				return;
			}

			// For each syllable (roughly approximated as vowels)
			const syllables = word.match(/[aeiouy]/gi) || [];
			const syllableCount = Math.max(syllables.length, 1);

			// Estimate word duration (ms)
			const wordDuration = syllableCount * 200;

			// Each word starts with closed mouth, transitions to open shapes, then closes
			visemeSequence.push({ viseme: 'viseme_sil', duration: 50 });

			// Add random mouth shapes for the duration of the word
			const visemes = [
				'viseme_PP',
				'viseme_FF',
				'viseme_TH',
				'viseme_DD',
				'viseme_kk',
				'viseme_CH',
				'viseme_SS',
				'viseme_nn',
				'viseme_RR',
				'viseme_aa',
				'viseme_E',
				'viseme_I',
				'viseme_O',
				'viseme_U'
			];

			// Add some mouth movement visemes
			for (let i = 0; i < syllableCount; i++) {
				// Open mouth for vowel
				const randomViseme = visemes[Math.floor(Math.random() * visemes.length)];
				visemeSequence.push({ viseme: randomViseme, duration: wordDuration / syllableCount });
			}

			// End with closed mouth
			visemeSequence.push({ viseme: 'viseme_sil', duration: 50 });
		});
	}

	function animateMouth() {
		if (!isSpeaking || !headMesh || visemeSequence.length === 0) {
			resetVisemes();
			return;
		}

		// Get current viseme
		const currentVisemeObj = visemeSequence[0];

		// Apply viseme
		if (headMesh.morphTargetDictionary && headMesh.morphTargetInfluences) {
			// Reset all visemes
			Object.keys(headMesh.morphTargetDictionary).forEach((viseme) => {
				if (viseme.startsWith('viseme_')) {
					const index = headMesh.morphTargetDictionary[viseme];
					headMesh.morphTargetInfluences[index] = 0;
				}
			});

			// Set current viseme
			if (headMesh.morphTargetDictionary[currentVisemeObj.viseme] !== undefined) {
				const index = headMesh.morphTargetDictionary[currentVisemeObj.viseme];
				headMesh.morphTargetInfluences[index] = 1.0;
			}
		}

		// Schedule next viseme
		visemeTimer = setTimeout(() => {
			// Remove the first viseme
			visemeSequence.shift();

			// Continue animation if there are more visemes
			if (visemeSequence.length > 0) {
				animateMouth();
			} else {
				resetVisemes();
			}
		}, currentVisemeObj.duration);
	}

	function resetVisemes() {
		// Clear any pending animation
		if (visemeTimer) {
			clearTimeout(visemeTimer);
			visemeTimer = null;
		}

		// Reset all visemes if we have the head mesh
		if (headMesh && headMesh.morphTargetDictionary && headMesh.morphTargetInfluences) {
			Object.keys(headMesh.morphTargetDictionary).forEach((viseme) => {
				if (viseme.startsWith('viseme_')) {
					const index = headMesh.morphTargetDictionary[viseme];
					headMesh.morphTargetInfluences[index] = 0;
				}
			});

			// Set back to neutral/silent
			if (headMesh.morphTargetDictionary['viseme_sil'] !== undefined) {
				const index = headMesh.morphTargetDictionary['viseme_sil'];
				headMesh.morphTargetInfluences[index] = 1.0;
			}
		}
	}

	function toggleAvatar() {
		active = !active;
	}
</script>

<div class="avatar-overlay" class:active>
	<div class="avatar-container" bind:this={avatarContainer}>
		{#if loading}
			<div class="loading-overlay">
				<Spinner size={32} />
				<p>Loading Avatar...</p>
			</div>
		{/if}
	</div>

	<button class="toggle-button" on:click={toggleAvatar}>
		{active ? 'Hide Avatar' : 'Show Avatar'}
	</button>
</div>

<style>
	.avatar-overlay {
		position: fixed;
		bottom: 80px;
		right: 20px;
		width: 300px;
		height: 350px;
		border-radius: 12px;
		overflow: hidden;
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
		z-index: 100;
		transform: translateY(calc(100% + 20px));
		transition: transform 0.3s ease-in-out;
		background-color: rgba(45, 50, 80, 0.8);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.avatar-overlay.active {
		transform: translateY(0);
	}

	.avatar-container {
		width: 100%;
		height: 100%;
		position: relative;
	}

	.loading-overlay {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		background-color: rgba(0, 0, 0, 0.5);
		z-index: 10;
		color: white;
	}

	.toggle-button {
		position: absolute;
		bottom: 100%;
		right: 0;
		background-color: rgba(45, 50, 80, 0.8);
		color: white;
		border: none;
		border-top-left-radius: 8px;
		border-top-right-radius: 8px;
		padding: 8px 16px;
		font-size: 14px;
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.toggle-button:hover {
		background-color: rgba(74, 99, 238, 0.8);
	}

	/* Responsive adjustments */
	@media (max-width: 768px) {
		.avatar-overlay {
			width: 250px;
			height: 300px;
			bottom: 70px;
			right: 10px;
		}
	}
</style>
