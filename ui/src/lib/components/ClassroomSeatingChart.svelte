
<!-- src/lib/components/ClassroomSeatingChart.svelte -->
<script lang="ts">
	import { getContext, onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';
	import type { StudentOut } from '$lib/types/classroom';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let students: StudentOut[] = [];

	type Layout = 'rows' | 'u' | 'islands';
	const LAYOUTS: { id: Layout; label: string }[] = [
		{ id: 'rows', label: 'Disposition en rangées' },
		{ id: 'u', label: 'Disposition en U' },
		{ id: 'islands', label: 'Disposition en îlots (groupes)' }
	];
	let layout: Layout = 'rows';

	let container: HTMLDivElement;
	let webglUnavailable = false;
	let cleanup: (() => void) | null = null;
	let rebuildDesks: ((layout: Layout) => void) | null = null;

	let hoveredStudent: StudentOut | null = null;
	let tooltipX = 0;
	let tooltipY = 0;

	// Same palette as StudentAvatar.svelte, expressed as Three.js hex colors.
	const AVATAR_COLORS = [
		0x3b82f6, // blue-500
		0x10b981, // emerald-500
		0xf59e0b, // amber-500
		0xa855f7, // purple-500
		0xec4899, // pink-500
		0x14b8a6, // teal-500
		0x6366f1, // indigo-500
		0xf43f5e // rose-500
	];

	const colorFor = (value: string) => {
		let hash = 0;
		for (let i = 0; i < value.length; i++) hash = (hash << 5) - hash + value.charCodeAt(i);
		return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
	};

	const initialsOf = (value: string) =>
		value
			.trim()
			.split(/\s+/)
			.slice(0, 2)
			.map((part) => part[0]?.toUpperCase() ?? '')
			.join('');

	// Desk position + facing angle (radians, 0 = facing the board at -z) for each layout.
	type Placement = { x: number; z: number; rotationY: number };

	const layoutRows = (n: number): Placement[] => {
		const cols = Math.max(1, Math.ceil(Math.sqrt(n)));
		const spacingX = 1.8;
		const spacingZ = 1.5;
		const placements: Placement[] = [];
		for (let i = 0; i < n; i++) {
			const row = Math.floor(i / cols);
			const col = i % cols;
			const rowCount = Math.min(cols, n - row * cols);
			const x = (col - (rowCount - 1) / 2) * spacingX;
			const z = row * spacingZ - 0.5;
			placements.push({ x, z, rotationY: 0 });
		}
		return placements;
	};

	const layoutU = (n: number): Placement[] => {
		const backCount = Math.max(1, Math.round(n * 0.34));
		const remaining = Math.max(0, n - backCount);
		const leftCount = Math.ceil(remaining / 2);
		const rightCount = remaining - leftCount;

		const halfWidth = 2.6;
		const frontZ = -0.6;
		const backZ = 2.2;
		const placements: Placement[] = [];

		for (let i = 0; i < leftCount; i++) {
			const t = leftCount > 1 ? i / (leftCount - 1) : 0.5;
			placements.push({ x: -halfWidth, z: frontZ + t * (backZ - frontZ), rotationY: -Math.PI / 2 });
		}
		for (let i = 0; i < backCount; i++) {
			const t = backCount > 1 ? i / (backCount - 1) : 0.5;
			placements.push({ x: -halfWidth + t * (2 * halfWidth), z: backZ, rotationY: 0 });
		}
		for (let i = 0; i < rightCount; i++) {
			const t = rightCount > 1 ? i / (rightCount - 1) : 0.5;
			placements.push({ x: halfWidth, z: backZ - t * (backZ - frontZ), rotationY: Math.PI / 2 });
		}
		return placements.slice(0, n);
	};

	const ISLAND_OFFSETS: [number, number][] = [
		[-0.85, -0.7],
		[0.85, -0.7],
		[-0.85, 0.7],
		[0.85, 0.7]
	];

	const layoutIslands = (n: number): Placement[] => {
		const groupSize = 4;
		const groupCount = Math.max(1, Math.ceil(n / groupSize));
		const cols = Math.max(1, Math.ceil(Math.sqrt(groupCount)));
		const islandSpacingX = 3.6;
		const islandSpacingZ = 3.2;
		const placements: Placement[] = [];

		for (let i = 0; i < n; i++) {
			const group = Math.floor(i / groupSize);
			const seatInGroup = i % groupSize;
			const groupRow = Math.floor(group / cols);
			const groupCol = group % cols;
			const groupsInRow = Math.min(cols, groupCount - groupRow * cols);

			const centerX = (groupCol - (groupsInRow - 1) / 2) * islandSpacingX;
			const centerZ = groupRow * islandSpacingZ - 0.5;

			const [dx, dz] = ISLAND_OFFSETS[seatInGroup % ISLAND_OFFSETS.length];
			placements.push({
				x: centerX + dx,
				z: centerZ + dz,
				rotationY: Math.atan2(dx, dz)
			});
		}
		return placements;
	};

	const computeLayout = (type: Layout, n: number): Placement[] => {
		if (type === 'u') return layoutU(n);
		if (type === 'islands') return layoutIslands(n);
		return layoutRows(n);
	};

	async function setupScene() {
		const THREE = await import('three');
		const { OrbitControls } = await import('three/examples/jsm/controls/OrbitControls.js');

		const width = container.clientWidth;
		const height = container.clientHeight;

		const scene = new THREE.Scene();
		scene.background = new THREE.Color(0xf4f7fe);

		const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
		camera.position.set(0, 5.5, 7.5);

		const renderer = new THREE.WebGLRenderer({ antialias: true });
		renderer.setSize(width, height);
		renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
		container.appendChild(renderer.domElement);

		const controls = new OrbitControls(camera, renderer.domElement);
		controls.target.set(0, 0.6, 0.5);
		controls.maxPolarAngle = Math.PI / 2.1;
		controls.minDistance = 3;
		controls.maxDistance = 16;
		controls.update();

		scene.add(new THREE.AmbientLight(0xffffff, 0.8));
		const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
		dirLight.position.set(3, 6, 4);
		scene.add(dirLight);

		const floor = new THREE.Mesh(
			new THREE.PlaneGeometry(24, 24),
			new THREE.MeshStandardMaterial({ color: 0xe2e8f0 })
		);
		floor.rotation.x = -Math.PI / 2;
		scene.add(floor);

		const board = new THREE.Mesh(
			new THREE.BoxGeometry(3.2, 1.1, 0.08),
			new THREE.MeshStandardMaterial({ color: 0x334155 })
		);
		board.position.set(0, 1.3, -2.8);
		scene.add(board);

		const deskGroup = new THREE.Group();
		scene.add(deskGroup);

		const buildDesk = (x: number, z: number, rotationY: number) => {
			const group = new THREE.Group();

			const tableMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
			const table = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.08, 0.8), tableMat);
			table.position.set(0, 0.5, 0);
			group.add(table);

			const legMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8 });
			const legGeo = new THREE.BoxGeometry(0.06, 0.5, 0.06);
			for (const [lx, lz] of [
				[0.6, 0.32],
				[-0.6, 0.32],
				[0.6, -0.32],
				[-0.6, -0.32]
			]) {
				const leg = new THREE.Mesh(legGeo, legMat);
				leg.position.set(lx, 0.25, lz);
				group.add(leg);
			}

			const baseMat = new THREE.MeshStandardMaterial({ color: 0x475569 });
			const base = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.05, 0.12), baseMat);
			base.position.set(0, 0.565, -0.2);
			group.add(base);

			const screen = new THREE.Mesh(
				new THREE.BoxGeometry(0.42, 0.28, 0.03),
				new THREE.MeshStandardMaterial({ color: 0x1e293b })
			);
			screen.position.set(0, 0.78, -0.25);
			group.add(screen);

			const glow = new THREE.Mesh(
				new THREE.PlaneGeometry(0.36, 0.22),
				new THREE.MeshStandardMaterial({
					color: 0x3b82f6,
					emissive: 0x3b82f6,
					emissiveIntensity: 0.4
				})
			);
			glow.position.set(0, 0.78, -0.235);
			group.add(glow);

			const chairMat = new THREE.MeshStandardMaterial({ color: 0x64748b });
			const seat = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.06, 0.4), chairMat);
			seat.position.set(0, 0.3, 0.55);
			group.add(seat);
			const back = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.4, 0.06), chairMat);
			back.position.set(0, 0.5, 0.74);
			group.add(back);

			group.position.set(x, 0, z);
			group.rotation.y = rotationY;
			return group;
		};

		const makeInitialsTexture = (name: string) => {
			const canvas = document.createElement('canvas');
			canvas.width = 128;
			canvas.height = 128;
			const ctx = canvas.getContext('2d');
			if (ctx) {
				const hex = '#' + colorFor(name).toString(16).padStart(6, '0');
				ctx.fillStyle = hex;
				ctx.beginPath();
				ctx.arc(64, 64, 60, 0, Math.PI * 2);
				ctx.fill();
				ctx.fillStyle = '#ffffff';
				ctx.font = 'bold 48px sans-serif';
				ctx.textAlign = 'center';
				ctx.textBaseline = 'middle';
				ctx.fillText(initialsOf(name), 64, 68);
			}
			const texture = new THREE.CanvasTexture(canvas);
			texture.needsUpdate = true;
			return texture;
		};

		const loadImage = (url: string): Promise<HTMLImageElement> =>
			new Promise((resolve, reject) => {
				const img = new Image();
				img.crossOrigin = 'anonymous';
				img.onload = () => resolve(img);
				img.onerror = reject;
				img.src = url;
			});

		const makePhotoTexture = async (url: string) => {
			const img = await loadImage(url);
			const canvas = document.createElement('canvas');
			canvas.width = 128;
			canvas.height = 128;
			const ctx = canvas.getContext('2d');
			if (!ctx) return null;
			ctx.save();
			ctx.beginPath();
			ctx.arc(64, 64, 60, 0, Math.PI * 2);
			ctx.closePath();
			ctx.clip();
			ctx.drawImage(img, 4, 4, 120, 120);
			ctx.restore();
			ctx.beginPath();
			ctx.arc(64, 64, 60, 0, Math.PI * 2);
			ctx.lineWidth = 4;
			ctx.strokeStyle = '#ffffff';
			ctx.stroke();
			const texture = new THREE.CanvasTexture(canvas);
			texture.needsUpdate = true;
			return texture;
		};

		const applyAvatarTexture = (sprite: any, student: StudentOut) => {
			sprite.material.map = makeInitialsTexture(student.name);
			sprite.material.needsUpdate = true;

			const hasPhoto = student.profile_image_url && student.profile_image_url !== '/user.png';
			if (hasPhoto) {
				makePhotoTexture(student.profile_image_url as string)
					.then((texture) => {
						if (!texture || sprite.userData.student?.id !== student.id) return;
						const oldMap = sprite.material.map;
						sprite.material.map = texture;
						sprite.material.needsUpdate = true;
						oldMap?.dispose?.();
					})
					.catch(() => {
						// keep the initials texture already applied
					});
			}
		};

		let avatarSprites: any[] = [];

		const clearDesks = () => {
			for (const child of [...deskGroup.children]) {
				deskGroup.remove(child);
				child.traverse((obj: any) => {
					obj.geometry?.dispose?.();
					if (obj.material) {
						const materials = Array.isArray(obj.material) ? obj.material : [obj.material];
						for (const mat of materials) {
							mat.map?.dispose?.();
							mat.dispose?.();
						}
					}
				});
			}
			for (const sprite of avatarSprites) {
				scene.remove(sprite);
				sprite.material.map?.dispose?.();
				sprite.material.dispose?.();
			}
			avatarSprites = [];
		};

		const buildLayout = (type: Layout) => {
			clearDesks();
			const placements = computeLayout(type, students.length);
			students.forEach((student, i) => {
				const { x, z, rotationY } = placements[i];
				deskGroup.add(buildDesk(x, z, rotationY));

				const sprite = new THREE.Sprite(new THREE.SpriteMaterial());
				sprite.scale.set(0.5, 0.5, 1);
				sprite.position.set(x + 0.5 * Math.sin(rotationY), 1.15, z + 0.5 * Math.cos(rotationY));
				sprite.userData.student = student;
				applyAvatarTexture(sprite, student);
				scene.add(sprite);
				avatarSprites.push(sprite);
			});
		};

		buildLayout(layout);
		rebuildDesks = buildLayout;

		const raycaster = new THREE.Raycaster();
		const pointer = new THREE.Vector2();

		const onPointerDown = (event: PointerEvent) => {
			const rect = renderer.domElement.getBoundingClientRect();
			pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
			pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
			raycaster.setFromCamera(pointer, camera);
			const hits = raycaster.intersectObjects(avatarSprites);
			if (hits.length > 0) {
				dispatch('selectStudent', hits[0].object.userData.student as StudentOut);
			}
		};
		renderer.domElement.addEventListener('pointerdown', onPointerDown);

		const onPointerMove = (event: PointerEvent) => {
			const rect = renderer.domElement.getBoundingClientRect();
			pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
			pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
			raycaster.setFromCamera(pointer, camera);
			const hits = raycaster.intersectObjects(avatarSprites);
			if (hits.length > 0) {
				hoveredStudent = hits[0].object.userData.student as StudentOut;
				tooltipX = event.clientX - rect.left;
				tooltipY = event.clientY - rect.top;
				renderer.domElement.style.cursor = 'pointer';
			} else {
				hoveredStudent = null;
				renderer.domElement.style.cursor = 'grab';
			}
		};
		const onPointerLeave = () => {
			hoveredStudent = null;
		};
		renderer.domElement.addEventListener('pointermove', onPointerMove);
		renderer.domElement.addEventListener('pointerleave', onPointerLeave);

		let animationId: number;
		const animate = () => {
			animationId = requestAnimationFrame(animate);
			controls.update();
			renderer.render(scene, camera);
		};
		animate();

		const handleResize = () => {
			const w = container.clientWidth;
			const h = container.clientHeight;
			camera.aspect = w / h;
			camera.updateProjectionMatrix();
			renderer.setSize(w, h);
		};
		const resizeObserver = new ResizeObserver(handleResize);
		resizeObserver.observe(container);

		return () => {
			rebuildDesks = null;
			cancelAnimationFrame(animationId);
			resizeObserver.disconnect();
			renderer.domElement.removeEventListener('pointerdown', onPointerDown);
			renderer.domElement.removeEventListener('pointermove', onPointerMove);
			renderer.domElement.removeEventListener('pointerleave', onPointerLeave);
			hoveredStudent = null;
			clearDesks();
			scene.traverse((obj: any) => {
				obj.geometry?.dispose?.();
				if (obj.material) {
					const materials = Array.isArray(obj.material) ? obj.material : [obj.material];
					for (const mat of materials) {
						mat.map?.dispose?.();
						mat.dispose?.();
					}
				}
			});
			renderer.dispose();
			if (renderer.domElement.parentElement === container) {
				container.removeChild(renderer.domElement);
			}
		};
	}

	const selectLayout = (next: Layout) => {
		layout = next;
		rebuildDesks?.(next);
	};

	onMount(() => {
		if (!browser || students.length === 0) return;
		setupScene()
			.then((dispose) => {
				cleanup = dispose;
			})
			.catch(() => {
				webglUnavailable = true;
			});
	});

	onDestroy(() => {
		cleanup?.();
	});
</script>

<div data-testid="seating-chart" class="space-y-2">
	{#if students.length === 0}
		<p class="text-center text-sm text-gray-500 dark:text-gray-400 py-8">
			{$i18n.t('No students enrolled yet')}
		</p>
	{:else if webglUnavailable}
		<p class="text-center text-sm text-gray-500 dark:text-gray-400 py-8">
			{$i18n.t('3D view is not available in this browser')}
		</p>
	{:else}
		<div class="flex flex-wrap items-center justify-center gap-2">
			{#each LAYOUTS as opt}
				<button
					type="button"
					data-testid={`layout-${opt.id}`}
					on:click={() => selectLayout(opt.id)}
					class="px-3 py-1.5 text-xs font-medium rounded-full border transition-colors {layout ===
					opt.id
						? 'bg-blue-600 text-white border-blue-600'
						: 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'}"
				>
					{$i18n.t(opt.label)}
				</button>
			{/each}
		</div>

		<p class="text-xs text-gray-400 dark:text-gray-500 text-center">
			{$i18n.t('Drag to rotate · Scroll to zoom · Click a student to view their info')}
		</p>
		<div class="relative">
			<div
				bind:this={container}
				data-testid="seating-chart-3d"
				class="w-full h-[420px] rounded-lg overflow-hidden cursor-grab active:cursor-grabbing"
			></div>
			{#if hoveredStudent}
				<div
					data-testid="seating-chart-tooltip"
					class="absolute pointer-events-none px-2 py-1 rounded-md bg-gray-900/90 text-white text-xs font-medium shadow-lg -translate-x-1/2 -translate-y-full"
					style="left: {tooltipX}px; top: {tooltipY - 12}px;"
				>
					{hoveredStudent.name}
				</div>
			{/if}
		</div>
	{/if}
</div>
