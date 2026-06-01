<!--
  StudentMesCours.svelte
  Page "Mes Cours" pour les étudiants :
  - Affiche les cours rejoints
  - Bouton "Rejoindre un cours" → modal code
  - Possibilité de quitter/supprimer un cours
-->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { fly, fade } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import { TUTOR_FRONT_URL } from '$lib/constants';
	import { goto } from '$app/navigation';

	const i18n = getContext('i18n');

	// ── TYPES ─────────────────────────────────────────────────────
	interface EnrolledCourse {
		id: string;
		title: string;
		language: string;
		category: string | null;
		level: string;
		teacher_name: string;
		teacher_profile_image_url?: string;
		enrolled_at: string;
		status: string;
	}

	// ── STATE ──────────────────────────────────────────────────────
	let courses: EnrolledCourse[] = [];
	let isLoading = true;
	let fetchError = '';

	// Modal Join
	let showJoinModal = false;
	let courseCode = '';
	let isJoining = false;
	let joinError = '';
	let joinSuccess = false;
	let newlyJoinedId = '';

	// Modal Delete (Quitter)
	let showDeleteModal = false;
	let courseToDelete: string | null = null;
	let isDeleting = false;
	let deleteError = '';

	// ── HELPERS ────────────────────────────────────────────────────
	function levelColor(level: string): string {
		const map: Record<string, string> = {
			'primary-school': '#22c55e',
			'middle-school': '#0ea5e9',
			'high-school': '#f59e0b',
			university: '#ef4444'
		};
		return map[level] ?? '#94a3b8';
	}

	function normalizeAvatarPath(url?: string | null) {
		if (!url || url.trim() === '') return null;
		const clean = url.split('?')[0].trim();
		if (
			clean.startsWith('http://') ||
			clean.startsWith('https://') ||
			clean.startsWith('/static/') ||
			clean.startsWith('/uploads/') ||
			clean.startsWith('/api/')
		) {
			return clean;
		}
		if (clean.startsWith('/')) return clean;
		return `/uploads/avatars/${clean}`;
	}

	function levelLabel(level: string): string {
		const map: Record<string, string> = {
			'primary-school': $i18n.t('Primaire'),
			'middle-school': $i18n.t('Collège'),
			'high-school': $i18n.t('Lycée'),
			university: $i18n.t('Université')
		};
		return map[level] ?? level;
	}

	function langFlag(lang: string): string {
		const map: Record<string, string> = {
			'fr-FR': '🇫🇷',
			'en-US': '🇺🇸',
			'ar-MA': '🇲🇦'
		};
		return map[lang] ?? '🌐';
	}

	// ── JOIN COURSE ────────────────────────────────────────────────
	function openJoinModal() {
		courseCode = '';
		joinError = '';
		joinSuccess = false;
		showJoinModal = true;
	}

	function closeJoinModal() {
		if (isJoining) return;
		showJoinModal = false;
		courseCode = '';
		joinError = '';
	}

	async function joinCourse() {
		const code = courseCode.trim();
		if (!code) {
			joinError = $i18n.t('Veuillez entrer un code');
			return;
		}
		isJoining = true;
		joinError = '';

		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch('/api/v1/student/courses/enroll', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`
				},
				body: JSON.stringify({ course_id: code })
			});

			if (res.status === 409) {
				joinError = $i18n.t('Vous êtes déjà inscrit à ce cours');
				return;
			}
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? $i18n.t('Code invalide ou cours introuvable'));
			}

			const enrolled: EnrolledCourse = await res.json();
			courses = [{ ...enrolled }, ...courses];
			newlyJoinedId = enrolled.id;
			joinSuccess = true;

			setTimeout(() => {
				showJoinModal = false;
				courseCode = '';
				joinSuccess = false;
				setTimeout(() => {
					newlyJoinedId = '';
				}, 4000);
			}, 1500);
		} catch (e: any) {
			joinError = e?.message ?? $i18n.t("Erreur lors de l'inscription");
		} finally {
			isJoining = false;
		}
	}

	// ── DELETE / LEAVE COURSE ──────────────────────────────────────
	function openDeleteModal(courseId: string) {
		courseToDelete = courseId;
		deleteError = '';
		showDeleteModal = true;
	}

	function closeDeleteModal() {
		if (isDeleting) return;
		showDeleteModal = false;
		courseToDelete = null;
		deleteError = '';
	}

	async function unenrollCourse() {
		if (!courseToDelete) return;
		isDeleting = true;
		deleteError = '';

		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`/api/v1/student/courses/${courseToDelete}`, {
				method: 'DELETE',
				headers: { Authorization: `Bearer ${token}` }
			});

			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? $i18n.t('Erreur lors de la suppression du cours'));
			}

			courses = courses.filter((c) => c.id !== courseToDelete);
			closeDeleteModal();
		} catch (e: any) {
			deleteError = e?.message ?? $i18n.t('Erreur lors de la suppression');
		} finally {
			isDeleting = false;
		}
	}

	// ── FETCH ENROLLED COURSES ─────────────────────────────────────
	async function fetchCourses() {
		isLoading = true;
		fetchError = '';
		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch('/api/v1/student/courses/', {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? `Erreur ${res.status}`);
			}
			courses = await res.json();
		} catch (e: any) {
			fetchError = e?.message ?? $i18n.t('Erreur lors du chargement');
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		fetchCourses();

		const handleAvatarUpdate = () => {
			fetchCourses();
		};
		window.addEventListener('avatar-updated', handleAvatarUpdate as EventListener);

		return () => {
			window.removeEventListener('avatar-updated', handleAvatarUpdate as EventListener);
		};
	});
</script>

<!-- ===================== TEMPLATE ===================== -->
<div class="page">
	<!-- ── HEADER ──────────────────────────────────────── -->
	<div class="page-header">
		<div class="header-left">
			<div class="header-icon">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="22" height="22">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
					/>
				</svg>
			</div>
			<div>
				<h1 class="page-title">
					{$i18n.t('Mes')} <span class="title-accent">{$i18n.t('Cours')}</span>
				</h1>
				<p class="page-sub">{$i18n.t('Retrouvez et démarrez vos cours')}</p>
			</div>
		</div>

		<button class="btn-join" on:click={openJoinModal}>
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2.5"
					d="M12 4v16m8-8H4"
				/>
			</svg>
			{$i18n.t('Rejoindre un cours')}
		</button>
	</div>

	<!-- ── ERROR ─────────────────────────────────────────── -->
	{#if fetchError}
		<div class="err-banner" in:fly={{ y: -6, duration: 200 }}>
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
				/>
			</svg>
			{fetchError}
			<button class="err-retry" on:click={fetchCourses}>{$i18n.t('Réessayer')}</button>
		</div>
	{/if}

	<!-- ── LOADING ─────────────────────────────────────────── -->
	{#if isLoading}
		<div class="courses-grid">
			{#each [1, 2, 3] as _}
				<div class="skeleton-card">
					<div class="skel skel-tag"></div>
					<div class="skel skel-title"></div>
					<div class="skel skel-sub"></div>
					<div class="skel skel-btn"></div>
				</div>
			{/each}
		</div>

		<!-- ── EMPTY ───────────────────────────────────────────── -->
	{:else if courses.length === 0 && !fetchError}
		<div class="empty-state" in:fly={{ y: 12, duration: 280 }}>
			<div class="empty-illustration">
				<svg
					viewBox="0 0 80 80"
					fill="none"
					xmlns="http://www.w3.org/2000/svg"
					width="80"
					height="80"
				>
					<rect
						x="10"
						y="20"
						width="36"
						height="44"
						rx="4"
						fill="#dbe4ff"
						stroke="#4c6ef5"
						stroke-width="1.5"
					/>
					<rect
						x="18"
						y="14"
						width="36"
						height="44"
						rx="4"
						fill="#e7f5ff"
						stroke="#339af0"
						stroke-width="1.5"
					/>
					<line
						x1="26"
						y1="28"
						x2="46"
						y2="28"
						stroke="#339af0"
						stroke-width="1.5"
						stroke-linecap="round"
					/>
					<line
						x1="26"
						y1="35"
						x2="46"
						y2="35"
						stroke="#339af0"
						stroke-width="1.5"
						stroke-linecap="round"
					/>
					<line
						x1="26"
						y1="42"
						x2="38"
						y2="42"
						stroke="#339af0"
						stroke-width="1.5"
						stroke-linecap="round"
					/>
					<circle cx="60" cy="58" r="14" fill="#fff" stroke="#e2e8f0" stroke-width="1.5" />
					<line
						x1="60"
						y1="52"
						x2="60"
						y2="64"
						stroke="#94a3b8"
						stroke-width="2"
						stroke-linecap="round"
					/>
					<line
						x1="54"
						y1="58"
						x2="66"
						y2="58"
						stroke="#94a3b8"
						stroke-width="2"
						stroke-linecap="round"
					/>
				</svg>
			</div>
			<p class="empty-title">{$i18n.t("Aucun cours pour l'instant")}</p>
			<p class="empty-sub">{$i18n.t('Entrez un code pour rejoindre votre premier cours')}</p>
			<button class="btn-join" on:click={openJoinModal}>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2.5"
						d="M12 4v16m8-8H4"
					/>
				</svg>
				{$i18n.t('Rejoindre un cours')}
			</button>
		</div>

		<!-- ── COURSE CARDS ────────────────────────────────────── -->
	{:else}
		<div class="courses-grid">
			{#each courses as course (course.id)}
				<div
					class="course-card {course.id === newlyJoinedId ? 'new-highlight' : ''}"
					in:fly={{ y: 14, duration: 260, easing: cubicOut }}
				>
					<!-- NEW badge -->
					{#if course.id === newlyJoinedId}
						<div class="new-badge" in:fly={{ x: 12, duration: 280 }}>
							✨ {$i18n.t('Nouveau')}
						</div>
					{/if}

					<!-- Top row: level dot + level tag + lang + Delete Button -->
					<div class="cc-top">
						<div class="cc-top-left">
							<div
								class="cc-level-tag"
								style="color:{levelColor(course.level)}; background:{levelColor(
									course.level
								)}18; border-color:{levelColor(course.level)}33;"
							>
								<span class="level-dot" style="background:{levelColor(course.level)};"></span>
								{levelLabel(course.level)}
							</div>
							<span class="cc-lang">{langFlag(course.language)} {course.language}</span>
						</div>

						<!-- Bouton Quitter (Supprimer) -->
						<button
							class="btn-delete-course"
							on:click|stopPropagation={() => openDeleteModal(course.id)}
							title={$i18n.t('Quitter le cours')}
						>
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
								/>
							</svg>
						</button>
					</div>

					<!-- Title -->
					<h2 class="cc-title">{course.title}</h2>

					<!-- Category badge -->
					{#if course.category}
						<span class="cc-category">{course.category}</span>
					{/if}

					<!-- Teacher -->
					<div class="cc-teacher">
						<div class="teacher-avatar">
							{#if course.teacher_profile_image_url && normalizeAvatarPath(course.teacher_profile_image_url)}
								<img
									src={normalizeAvatarPath(course.teacher_profile_image_url)}
									alt={course.teacher_name}
									class="teacher-avatar-img"
								/>
							{:else}
								{course.teacher_name?.charAt(0)?.toUpperCase() ?? 'P'}
							{/if}
						</div>
						<span class="teacher-name">{course.teacher_name ?? $i18n.t('Professeur')}</span>
					</div>

					<!-- Divider -->
					<div class="cc-divider"></div>

					<!-- Start button -->
					<button class="btn-start" on:click={() => goto(`/student/classrooms/${course.id}`)}>
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2.5"
								d="M5 3l14 9-14 9V3z"
							/>
						</svg>
						{$i18n.t('Démarrer le cours')}
						<svg
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							width="14"
							height="14"
							class="arrow-right"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2.5"
								d="M13 7l5 5m0 0l-5 5m5-5H6"
							/>
						</svg>
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- ===================== JOIN MODAL ===================== -->
{#if showJoinModal}
	<div
		class="modal-overlay"
		role="button"
		tabindex="0"
		on:click={closeJoinModal}
		on:keydown={(e) => e.key === 'Escape' && closeJoinModal()}
		in:fade={{ duration: 200 }}
		out:fade={{ duration: 150 }}
	>
		<div
			class="modal-card"
			role="dialog"
			aria-modal="true"
			aria-label={$i18n.t('Rejoindre un cours')}
			on:click|stopPropagation
			on:keydown|stopPropagation
			in:fly={{ y: 20, duration: 300, easing: cubicOut }}
		>
			<!-- Close -->
			<button class="modal-close" on:click={closeJoinModal} aria-label={$i18n.t('Fermer')}>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					/>
				</svg>
			</button>

			{#if !joinSuccess}
				<!-- ── DEFAULT STATE ── -->
				<div class="modal-body">
					<div class="modal-logo-wrap">
						<img src="{TUTOR_FRONT_URL}/static/favicon.png" alt="OT AI" class="modal-logo-img" />
					</div>

					<h2 class="modal-title">{$i18n.t('Rejoindre un cours')}</h2>
					<p class="modal-subtitle">
						{$i18n.t('Entrez le code fourni par votre professeur')}
					</p>

					<!-- Code input -->
					<div class="input-group">
						<label for="courseCodeInput" class="input-label">
							{$i18n.t('Code du cours')}
						</label>
						<input
							id="courseCodeInput"
							type="text"
							bind:value={courseCode}
							placeholder={$i18n.t('ex: a1b2c3d4-...')}
							class="code-input {joinError ? 'input-error' : ''}"
							disabled={isJoining}
							on:keydown={(e) => e.key === 'Enter' && joinCourse()}
							autocomplete="off"
							spellcheck="false"
						/>
						{#if joinError}
							<p class="input-err-msg" in:fly={{ y: -4, duration: 150 }}>
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="13" height="13">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
									/>
								</svg>
								{joinError}
							</p>
						{/if}
					</div>

					<p class="modal-hint">
						{$i18n.t('Pas de code ? Demandez à votre professeur ou à votre institution')}
					</p>

					<!-- Join button -->
					<button
						class="btn-join-confirm"
						on:click={joinCourse}
						disabled={isJoining || !courseCode.trim()}
					>
						{#if isJoining}
							<svg class="spin-icon" viewBox="0 0 50 50" width="16" height="16">
								<circle
									cx="25"
									cy="25"
									r="20"
									fill="none"
									stroke="currentColor"
									stroke-width="5"
									stroke-dasharray="80 40"
								/>
							</svg>
							{$i18n.t('Inscription...')}
						{:else}
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2.5"
									d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
								/>
							</svg>
							{$i18n.t('Rejoindre le cours')}
						{/if}
					</button>
				</div>
			{:else}
				<!-- ── SUCCESS STATE ── -->
				<div class="modal-success" in:fly={{ y: 12, duration: 280, easing: cubicOut }}>
					<div class="success-icon-wrap">
						<svg viewBox="0 0 24 24" fill="none" stroke="#22c55e" width="32" height="32">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2.5"
								d="M5 13l4 4L19 7"
							/>
						</svg>
					</div>
					<h2 class="modal-title">{$i18n.t('Cours rejoint !')}</h2>
					<p class="modal-subtitle">{$i18n.t('Vous êtes maintenant inscrit au cours.')}</p>
				</div>
			{/if}
		</div>
	</div>
{/if}

<!-- ===================== DELETE CONFIRMATION MODAL ===================== -->
{#if showDeleteModal}
	<div
		class="modal-overlay"
		role="button"
		tabindex="0"
		on:click={closeDeleteModal}
		on:keydown={(e) => e.key === 'Escape' && closeDeleteModal()}
		in:fade={{ duration: 200 }}
		out:fade={{ duration: 150 }}
	>
		<div
			class="modal-card modal-delete"
			role="dialog"
			aria-modal="true"
			on:click|stopPropagation
			on:keydown|stopPropagation
			in:fly={{ y: 20, duration: 300, easing: cubicOut }}
		>
			<div class="modal-body">
				<div class="delete-icon-wrap">
					<svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" width="32" height="32">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
						/>
					</svg>
				</div>

				<h2 class="modal-title">{$i18n.t('Quitter ce cours ?')}</h2>
				<p class="modal-subtitle">
					{$i18n.t(
						"Êtes-vous sûr de vouloir vous désinscrire ? Vous perdrez l'accès à toutes les ressources de ce cours."
					)}
				</p>

				{#if deleteError}
					<p class="input-err-msg text-center" in:fly={{ y: -4, duration: 150 }}>
						{deleteError}
					</p>
				{/if}

				<div class="delete-actions">
					<button class="btn-cancel" on:click={closeDeleteModal} disabled={isDeleting}>
						{$i18n.t('Annuler')}
					</button>
					<button class="btn-confirm-delete" on:click={unenrollCourse} disabled={isDeleting}>
						{#if isDeleting}
							<svg class="spin-icon" viewBox="0 0 50 50" width="16" height="16">
								<circle
									cx="25"
									cy="25"
									r="20"
									fill="none"
									stroke="currentColor"
									stroke-width="5"
									stroke-dasharray="80 40"
								/>
							</svg>
							{$i18n.t('Suppression...')}
						{:else}
							{$i18n.t('Oui, quitter')}
						{/if}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- ===================== STYLES ===================== -->
<style>
	@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

	/* ── PAGE ── */
	.page {
		font-family: 'Plus Jakarta Sans', sans-serif;
		max-width: 1300px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: #f3f5fb;
		color: #1e293b;
	}
	:global(.dark) .page {
		background: #0f172a;
		color: #e2e8f0;
	}

	/* ── HEADER ── */
	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 1rem;
		margin-bottom: 2rem;
	}
	.header-left {
		display: flex;
		align-items: center;
		gap: 0.875rem;
	}
	.header-icon {
		width: 46px;
		height: 46px;
		border-radius: 0.875rem;
		background: linear-gradient(145deg, #3b5bdb, #2563eb);
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		box-shadow: 0 8px 16px -6px rgba(37, 99, 235, 0.4);
	}
	.page-title {
		font-size: 1.5rem;
		font-weight: 800;
		margin: 0 0 0.15rem;
		letter-spacing: -0.02em;
	}
	.title-accent {
		color: #2563eb;
	}
	:global(.dark) .title-accent {
		color: #60a5fa;
	}
	.page-sub {
		font-size: 0.8rem;
		color: #64748b;
		margin: 0;
	}
	:global(.dark) .page-sub {
		color: #94a3b8;
	}

	/* ── BTN JOIN (header) ── */
	.btn-join {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: linear-gradient(145deg, #3b5bdb, #2563eb);
		color: white;
		border: none;
		border-radius: 0.875rem;
		padding: 0.65rem 1.35rem;
		font-size: 0.9rem;
		font-weight: 700;
		cursor: pointer;
		transition: all 0.2s;
		font-family: inherit;
		box-shadow: 0 8px 16px -6px rgba(37, 99, 235, 0.4);
	}
	.btn-join:hover {
		transform: translateY(-2px);
		box-shadow: 0 12px 20px -8px rgba(37, 99, 235, 0.5);
	}

	/* ── ERROR BANNER ── */
	.err-banner {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 0.875rem;
		padding: 0.875rem 1.25rem;
		font-size: 0.875rem;
		font-weight: 600;
		color: #dc2626;
		margin-bottom: 1.5rem;
	}
	:global(.dark) .err-banner {
		background: #450a0a;
		border-color: #991b1b;
		color: #fca5a5;
	}
	.err-retry {
		margin-left: auto;
		padding: 0.3rem 0.7rem;
		border-radius: 0.5rem;
		background: white;
		border: 1px solid #fecaca;
		color: #dc2626;
		font-size: 0.8rem;
		font-weight: 600;
		cursor: pointer;
		font-family: inherit;
	}

	/* ── SKELETON ── */
	.skeleton-card {
		background: white;
		border: 1px solid #e5e8f4;
		border-radius: 1.25rem;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		min-height: 220px;
	}
	:global(.dark) .skeleton-card {
		background: #1e293b;
		border-color: #334155;
	}
	.skel {
		border-radius: 0.5rem;
		background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
	}
	:global(.dark) .skel {
		background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%);
		background-size: 200% 100%;
	}
	.skel-tag {
		height: 24px;
		width: 80px;
	}
	.skel-title {
		height: 22px;
		width: 75%;
	}
	.skel-sub {
		height: 16px;
		width: 50%;
	}
	.skel-btn {
		height: 42px;
		margin-top: auto;
	}
	@keyframes shimmer {
		to {
			background-position: -200% 0;
		}
	}

	/* ── EMPTY STATE ── */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		padding: 4rem 2rem;
		text-align: center;
	}
	.empty-illustration {
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 1.5rem;
		padding: 1.25rem;
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
	}
	:global(.dark) .empty-illustration {
		background: #1e293b;
		border-color: #334155;
	}
	.empty-title {
		font-size: 1.1rem;
		font-weight: 700;
		margin: 0;
	}
	.empty-sub {
		font-size: 0.875rem;
		color: #64748b;
		margin: 0;
	}
	:global(.dark) .empty-sub {
		color: #94a3b8;
	}

	/* ── GRID ── */
	.courses-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
		gap: 1.25rem;
	}

	/* ── COURSE CARD ── */
	.course-card {
		background: white;
		border: 1.5px solid #e5e8f4;
		border-radius: 1.25rem;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.875rem;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
		transition: all 0.25s;
		position: relative;
		overflow: hidden;
	}
	.course-card:hover {
		transform: translateY(-3px);
		box-shadow: 0 12px 28px -8px rgba(0, 0, 0, 0.1);
		border-color: #bfdbfe;
	}
	:global(.dark) .course-card {
		background: #1e293b;
		border-color: #334155;
	}
	:global(.dark) .course-card:hover {
		border-color: #3b5bdb;
	}
	.course-card.new-highlight {
		border-color: #3b5bdb;
		box-shadow:
			0 0 0 3px rgba(59, 91, 219, 0.12),
			0 12px 24px -8px rgba(59, 91, 219, 0.2);
	}

	.new-badge {
		position: absolute;
		top: 1rem;
		right: 1rem;
		background: linear-gradient(135deg, #3b5bdb, #2563eb);
		color: white;
		font-size: 0.68rem;
		font-weight: 800;
		padding: 0.25rem 0.65rem;
		border-radius: 2rem;
		letter-spacing: 0.04em;
	}

	/* top row */
	.cc-top {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.5rem;
	}
	.cc-top-left {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}
	.cc-level-tag {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.72rem;
		font-weight: 700;
		padding: 0.25rem 0.65rem;
		border-radius: 9999px;
		border: 1px solid transparent;
	}
	.level-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.cc-lang {
		font-size: 0.75rem;
		color: #64748b;
		font-weight: 500;
	}
	:global(.dark) .cc-lang {
		color: #94a3b8;
	}

	/* Button Delete Course */
	.btn-delete-course {
		background: transparent;
		border: none;
		padding: 0.4rem;
		border-radius: 0.5rem;
		color: #94a3b8;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}
	.btn-delete-course:hover {
		background: #fef2f2;
		color: #ef4444;
	}
	:global(.dark) .btn-delete-course:hover {
		background: rgba(239, 68, 68, 0.15);
	}

	/* title */
	.cc-title {
		font-size: 1.05rem;
		font-weight: 700;
		color: #0f172a;
		margin: 0;
		line-height: 1.35;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	:global(.dark) .cc-title {
		color: #f1f5f9;
	}

	/* category */
	.cc-category {
		display: inline-block;
		background: #f1f5f9;
		color: #475569;
		font-size: 0.72rem;
		font-weight: 600;
		padding: 0.2rem 0.65rem;
		border-radius: 9999px;
		align-self: flex-start;
	}
	:global(.dark) .cc-category {
		background: #334155;
		color: #94a3b8;
	}

	/* teacher */
	.cc-teacher {
		display: flex;
		align-items: center;
		gap: 0.6rem;
	}
	.teacher-avatar {
		width: 28px;
		height: 28px;
		border-radius: 50%;
		background: linear-gradient(135deg, #dbe4ff, #bac8ff);
		color: #3b5bdb;
		font-size: 0.75rem;
		font-weight: 800;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		overflow: hidden;
	}
	.teacher-avatar-img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		border-radius: 50%;
		display: block;
	}
	:global(.dark) .teacher-avatar {
		background: rgba(59, 91, 219, 0.2);
		color: #93c5fd;
	}
	.teacher-name {
		font-size: 0.82rem;
		font-weight: 500;
		color: #475569;
	}
	:global(.dark) .teacher-name {
		color: #94a3b8;
	}

	/* divider */
	.cc-divider {
		height: 1px;
		background: #f1f5f9;
	}
	:global(.dark) .cc-divider {
		background: #334155;
	}

	/* start button */
	.btn-start {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		border-radius: 0.875rem;
		border: none;
		background: linear-gradient(145deg, #3b5bdb, #2563eb);
		color: white;
		font-weight: 700;
		font-size: 0.9rem;
		cursor: pointer;
		transition: all 0.22s;
		font-family: inherit;
		box-shadow: 0 8px 16px -6px rgba(37, 99, 235, 0.35);
		width: 100%;
	}
	.btn-start:hover {
		background: linear-gradient(145deg, #2563eb, #1d4ed8);
		transform: translateY(-2px);
		box-shadow: 0 12px 20px -8px rgba(37, 99, 235, 0.5);
	}
	.btn-start:active {
		transform: scale(0.98);
	}
	.arrow-right {
		margin-left: auto;
		opacity: 0.8;
	}

	/* ── MODAL ── */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(15, 23, 42, 0.6);
		backdrop-filter: blur(8px);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 10000;
	}

	.modal-card {
		background: white;
		border-radius: 2rem;
		padding: 2.5rem 2.25rem 2.25rem;
		max-width: 420px;
		width: 92%;
		box-shadow:
			0 32px 64px -12px rgba(0, 0, 0, 0.24),
			0 0 0 1px rgba(0, 0, 0, 0.04);
		position: relative;
	}
	:global(.dark) .modal-card {
		background: #1e293b;
		border: 1px solid #334155;
	}

	.modal-delete {
		max-width: 380px;
		padding: 2.5rem 2rem 2rem;
	}

	.modal-close {
		position: absolute;
		top: 1.1rem;
		right: 1.1rem;
		background: #f1f5f9;
		border: none;
		cursor: pointer;
		color: #64748b;
		border-radius: 0.6rem;
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}
	.modal-close:hover {
		background: #e2e8f0;
		color: #1e293b;
	}
	:global(.dark) .modal-close {
		background: #334155;
		color: #94a3b8;
	}
	:global(.dark) .modal-close:hover {
		background: #475569;
		color: #f1f5f9;
	}

	.modal-body {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		text-align: center;
	}

	.modal-logo-wrap {
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 0.25rem;
	}
	.modal-logo-img {
		width: 100px;
		height: 100px;
		object-fit: contain;
	}

	.delete-icon-wrap {
		width: 64px;
		height: 64px;
		border-radius: 50%;
		background: #fef2f2;
		border: 2px solid #fecaca;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 0.5rem;
	}
	:global(.dark) .delete-icon-wrap {
		background: rgba(239, 68, 68, 0.15);
		border-color: rgba(239, 68, 68, 0.3);
	}

	.modal-title {
		font-size: 1.35rem;
		font-weight: 800;
		margin: 0;
		color: #0f172a;
		letter-spacing: -0.3px;
	}
	:global(.dark) .modal-title {
		color: #f8fafc;
	}
	.modal-subtitle {
		font-size: 0.9rem;
		color: #64748b;
		margin: 0;
		line-height: 1.55;
		max-width: 300px;
	}
	:global(.dark) .modal-subtitle {
		color: #94a3b8;
	}

	.input-group {
		width: 100%;
		text-align: left;
	}
	.input-label {
		display: block;
		font-size: 0.8rem;
		font-weight: 600;
		color: #475569;
		margin-bottom: 0.4rem;
	}
	:global(.dark) .input-label {
		color: #94a3b8;
	}
	.code-input {
		width: 100%;
		padding: 0.75rem 1rem;
		border: 1.5px solid #e2e8f0;
		border-radius: 0.875rem;
		background: #f8fafc;
		color: #1e293b;
		font-family: 'Courier New', monospace;
		font-size: 0.95rem;
		outline: none;
		box-sizing: border-box;
		transition: all 0.2s;
	}
	.code-input:focus {
		border-color: #3b5bdb;
		background: white;
		box-shadow: 0 0 0 3px rgba(59, 91, 219, 0.12);
	}
	.code-input.input-error {
		border-color: #ef4444;
		background: #fff5f5;
	}
	.code-input:disabled {
		opacity: 0.65;
		cursor: not-allowed;
	}
	:global(.dark) .code-input {
		background: #0f172a;
		border-color: #334155;
		color: #f1f5f9;
	}
	:global(.dark) .code-input:focus {
		border-color: #3b5bdb;
		background: #0f172a;
	}

	.input-err-msg {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.4rem;
		font-size: 0.78rem;
		color: #ef4444;
		margin-top: 0.4rem;
		font-weight: 500;
	}

	.modal-hint {
		font-size: 0.78rem;
		color: #94a3b8;
		margin: 0;
		line-height: 1.5;
	}

	.btn-join-confirm {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.875rem 1.5rem;
		border-radius: 1rem;
		border: none;
		background: linear-gradient(145deg, #3b5bdb, #2563eb);
		color: white;
		font-weight: 700;
		font-size: 0.95rem;
		cursor: pointer;
		transition: all 0.2s;
		font-family: inherit;
		box-shadow: 0 8px 16px -6px rgba(37, 99, 235, 0.4);
	}
	.btn-join-confirm:hover:not(:disabled) {
		background: linear-gradient(145deg, #2563eb, #1d4ed8);
		transform: translateY(-2px);
		box-shadow: 0 12px 20px -8px rgba(37, 99, 235, 0.5);
	}
	.btn-join-confirm:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		transform: none;
	}

	.delete-actions {
		display: flex;
		gap: 0.75rem;
		width: 100%;
		margin-top: 1rem;
	}

	.btn-cancel {
		flex: 1;
		padding: 0.85rem;
		border-radius: 1rem;
		border: 1.5px solid #e2e8f0;
		background: transparent;
		color: #64748b;
		font-weight: 700;
		font-size: 0.9rem;
		cursor: pointer;
		transition: all 0.2s;
		font-family: inherit;
	}
	.btn-cancel:hover:not(:disabled) {
		background: #f8fafc;
		color: #0f172a;
	}
	:global(.dark) .btn-cancel {
		border-color: #334155;
		color: #94a3b8;
	}
	:global(.dark) .btn-cancel:hover:not(:disabled) {
		background: #334155;
		color: #f8fafc;
	}

	.btn-confirm-delete {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 0.85rem;
		border-radius: 1rem;
		border: none;
		background: #ef4444;
		color: white;
		font-weight: 700;
		font-size: 0.9rem;
		cursor: pointer;
		transition: all 0.2s;
		font-family: inherit;
		box-shadow: 0 8px 16px -6px rgba(239, 68, 68, 0.4);
	}
	.btn-confirm-delete:hover:not(:disabled) {
		background: #dc2626;
		transform: translateY(-2px);
	}
	.btn-confirm-delete:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		transform: none;
	}

	.spin-icon {
		animation: spin 0.8s linear infinite;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	/* success state */
	.modal-success {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.875rem;
		text-align: center;
		padding: 0.5rem 0;
	}
	.success-icon-wrap {
		width: 72px;
		height: 72px;
		border-radius: 50%;
		background: #f0fdf4;
		border: 2px solid #bbf7d0;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	:global(.dark) .success-icon-wrap {
		background: #052e16;
		border-color: #166534;
	}

	/* ── RESPONSIVE ── */
	@media (max-width: 640px) {
		.page {
			padding: 1rem;
		}
		.page-header {
			flex-direction: column;
			align-items: flex-start;
		}
		.btn-join {
			width: 100%;
			justify-content: center;
		}
		.courses-grid {
			grid-template-columns: 1fr;
		}
		.modal-card {
			padding: 2rem 1.5rem 1.75rem;
			border-radius: 1.5rem;
		}
		.delete-actions {
			flex-direction: column;
		}
	}
</style>
