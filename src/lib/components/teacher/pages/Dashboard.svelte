<script lang="ts">
    import { getContext, onMount, onDestroy } from 'svelte';
    import { derived } from 'svelte/store';
    import { goto } from '$app/navigation';
    import { fly, fade } from 'svelte/transition';
    import { user } from '$lib/stores';

    const i18n: any = getContext('i18n');
    const _ = derived(i18n, ($i18n: any) => (key: string, options?: any) => $i18n.t(key, options));

    // ── TYPES ─────────────────────────────────────────────────────
    interface Course {
        id: string;
        title: string;
        language: string;
        category: string | null;
        level: string;
        objectives: string | null;
        status: string;
        model_used: string | null;
        created_at: string;
        updated_at: string | null;
        student_count?: number;
    }

    // ── STATE ──────────────────────────────────────────────────────
    let courses: Course[] = [];
    let isLoading = true;
    let fetchError = '';
    let newCourseId = '';
    let copiedId = '';
    let quizzesCount = 0;

    // Quiz state
    let teacherQuizzes: any[] = [];
    let isLoadingQuizzes = true;

    // Delete state
    let deletingCourseId = '';
    let isDeleting = false;
    let deleteError = '';

    // Reactive clock
    let now = Date.now();
    let clockInterval: ReturnType<typeof setInterval>;

    // ── STATS ──────────────────────────────────────────────────────
    $: totalCourses = courses.length;
    $: totalStudents = courses.reduce((acc, c) => acc + (c.student_count ?? 0), 0);

    // ── HELPERS ────────────────────────────────────────────────────
    function timeAgo(dateStr: string, _now = Date.now()): string {
        const normalized = dateStr.endsWith('Z') || dateStr.includes('+')
            ? dateStr
            : dateStr + 'Z';
        const then = new Date(normalized).getTime();
        const diffSec = Math.floor((_now - then) / 1000);

        if (diffSec < 10)    return $i18n.t('à l\'instant');
        if (diffSec < 60)    return $i18n.t('il y a') + ' ' + diffSec + ' ' + $i18n.t('secondes');
        if (diffSec < 3600) {
            const m = Math.floor(diffSec / 60);
            return $i18n.t('il y a') + ' ' + m + ' ' + (m === 1 ? $i18n.t('minute') : $i18n.t('minutes'));
        }
        if (diffSec < 86400) {
            const h = Math.floor(diffSec / 3600);
            return $i18n.t('il y a') + ' ' + h + ' ' + (h === 1 ? $i18n.t('heure') : $i18n.t('heures'));
        }
        if (diffSec < 604800) {
            const d = Math.floor(diffSec / 86400);
            return $i18n.t('il y a') + ' ' + d + ' ' + (d === 1 ? $i18n.t('jour') : $i18n.t('jours'));
        }
        const w = Math.floor(diffSec / 604800);
        return $i18n.t('il y a') + ' ' + w + ' ' + (w === 1 ? $i18n.t('semaine') : $i18n.t('semaines'));
    }

    function levelColor(level: string): string {
        const map: Record<string, string> = {
            'primary-school': '#22c55e',
            'middle-school':  '#0ea5e9',
            'high-school':    '#f59e0b',
            'university':     '#ef4444',
        };
        return map[level] ?? '#94a3b8';
    }

    function levelLabel(level: string): string {
        const map: Record<string, string> = {
            'primary-school': $i18n.t('Primaire'),
            'middle-school':  $i18n.t('Collège'),
            'high-school':    $i18n.t('Lycée'),
            'university':     $i18n.t('Université'),
        };
        return map[level] ?? level;
    }

    function shortCode(id: string): string {
        return id;
    }

    async function copyCode(id: string) {
        await navigator.clipboard.writeText(shortCode(id));
        copiedId = id;
        setTimeout(() => copiedId = '', 2000);
    }

    // ── DELETE COURSE ──────────────────────────────────────────────
    function openDeleteModal(courseId: string) {
        deletingCourseId = courseId;
        deleteError = '';
    }

    function closeDeleteModal() {
        if (isDeleting) return;
        deletingCourseId = '';
        deleteError = '';
    }

    async function deleteCourse(courseId: string) {
        isDeleting = true;
        deleteError = '';
        try {
            const token = localStorage.getItem('token') ?? '';
            const res = await fetch(`/api/v1/teacher/courses/${courseId}`, {
                method: 'DELETE',
                headers: { Authorization: `Bearer ${token}` }
            });
            if (!res.ok && res.status !== 204) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail ?? `Erreur ${res.status}`);
            }
            courses = courses.filter(c => c.id !== courseId);
            deletingCourseId = '';
            deleteError = '';
        } catch (e: any) {
            deleteError = e?.message ?? $i18n.t('Erreur lors de la suppression');
        } finally {
            isDeleting = false;
        }
    }

    // ── STUDENT COUNTS ─────────────────────────────────────────────
    async function fetchStudentCounts() {
        const token = localStorage.getItem('token') ?? '';
        const results = await Promise.all(
            courses.map(async (c) => {
                try {
                    const res = await fetch(`/api/v1/teacher/courses/${c.id}/students/count`, {
                        headers: { Authorization: `Bearer ${token}` }
                    });
                    if (!res.ok) return { id: c.id, count: 0 };
                    const data = await res.json();
                    return { id: c.id, count: data.count ?? 0 };
                } catch { return { id: c.id, count: 0 }; }
            })
        );
        courses = courses.map(c => ({
            ...c,
            student_count: results.find(x => x.id === c.id)?.count ?? 0
        }));
    }

    async function fetchQuizzesCount() {
        const token = localStorage.getItem('token') ?? '';
        isLoadingQuizzes = true;
        try {
            const res = await fetch('/api/v1/quizzes/teacher', {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                teacherQuizzes = data;
                quizzesCount = data.filter((q: any) => q.status === 'published').length;
            } else {
                teacherQuizzes = [];
            }
        } catch {
            teacherQuizzes = [];
        } finally {
            isLoadingQuizzes = false;
        }
    }

    // ── FETCH COURSES ──────────────────────────────────────────────
    async function fetchCourses() {
        isLoading = true;
        fetchError = '';
        try {
            const token = localStorage.getItem('token') ?? '';
            const res = await fetch('/api/v1/teacher/courses/', {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail ?? `Erreur ${res.status}`);
            }
            const data: Course[] = await res.json();
            courses = data.sort((a, b) => {
                if (a.id === newCourseId) return -1;
                if (b.id === newCourseId) return 1;
                return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            });

            await fetchStudentCounts();

        } catch (e: any) {
            fetchError = e?.message ?? $i18n.t('Erreur lors du chargement');
        } finally {
            isLoading = false;
        }
    }

    // ── ON MOUNT ──────────────────────────────────────────────────
    onMount(() => {
        const params = new URLSearchParams(window.location.search);
        newCourseId = params.get('newCourse') ?? '';
        fetchCourses();
        fetchQuizzesCount();
        if (newCourseId) {
            setTimeout(() => { newCourseId = ''; }, 5000);
        }
        clockInterval = setInterval(() => { now = Date.now(); }, 30_000);
    });

    // ── ON DESTROY ────────────────────────────────────────────────
    onDestroy(() => {
        clearInterval(clockInterval);
    });
</script>

<div class="dashboard">

    <!-- ── TOP BAR ──────────────────────────────────────────── -->
    <div class="topbar">
        <div class="topbar-title">
            <div class="topbar-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="20" height="20">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
                </svg>
            </div>
            <div>
                <h1 class="topbar-heading">{$i18n.t('Tableau de bord')}</h1>
                <p class="topbar-sub">{$i18n.t('Gérez vos cours et suivez vos étudiants')}</p>
            </div>
        </div>
        <button class="btn-create" on:click={() => goto('/teacher/courses')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
            </svg>
            {$i18n.t('Créer un cours')}
        </button>
    </div>

    <!-- ── NEW COURSE BANNER ────────────────────────────────── -->
    {#if newCourseId}
        <div class="new-banner" in:fly={{ y: -10, duration: 300 }} out:fade={{ duration: 200 }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
            </svg>
            <span>{$i18n.t('Votre cours a été créé avec succès ! Il apparaît en premier ci-dessous.')}</span>
        </div>
    {/if}

    <!-- ── STATS ────────────────────────────────────────────── -->
    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-icon stat-blue">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
            </div>
            <div class="stat-body">
                <span class="stat-label">{$i18n.t('Total des cours')}</span>
                <span class="stat-value">{isLoading ? '—' : totalCourses}</span>
            </div>
        </div>

        <div class="stat-card">
            <div class="stat-icon stat-green">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
            </div>
            <div class="stat-body">
                <span class="stat-label">{$i18n.t('Étudiants inscrits')}</span>
                <span class="stat-value">{isLoading ? '—' : totalStudents}</span>
            </div>
        </div>

        <div class="stat-card cursor-pointer hover:scale-[1.01] active:scale-95 transition-all" on:click={() => goto('/teacher/assignments')}>
            <div class="stat-icon stat-purple">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
                </svg>
            </div>
            <div class="stat-body">
                <span class="stat-label">{$i18n.t('Évaluations active(s)')}</span>
                <span class="stat-value">{isLoading ? '—' : quizzesCount}</span>
            </div>
        </div>
    </div>

    <!-- ── SECTION HEADER ───────────────────────────────────── -->
    <div class="section-head">
        <h2 class="section-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            {$i18n.t('Cours récents')}
        </h2>
        <button class="btn-refresh" on:click={fetchCourses} title={$i18n.t('Actualiser')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="15" height="15">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
        </button>
    </div>

    <!-- ── ERROR ─────────────────────────────────────────────── -->
    {#if fetchError}
        <div class="err-banner" in:fly={{ y: -6, duration: 200 }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
            </svg>
            {fetchError}
            <button class="err-retry" on:click={fetchCourses}>{$i18n.t('Réessayer')}</button>
        </div>
    {/if}

    <!-- ── LOADING ────────────────────────────────────────────── -->
    {#if isLoading}
        <div class="loading-grid">
            {#each [1,2,3,4] as _}
                <div class="skeleton-card">
                    <div class="skel skel-title"></div>
                    <div class="skel skel-sub"></div>
                    <div class="skel skel-code"></div>
                    <div class="skel skel-footer"></div>
                </div>
            {/each}
        </div>

    <!-- ── EMPTY ──────────────────────────────────────────────── -->
    {:else if courses.length === 0 && !fetchError}
        <div class="empty-state" in:fly={{ y: 10, duration: 250 }}>
            <div class="empty-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="32" height="32">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                        d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
            </div>
            <p class="empty-title">{$i18n.t('Aucun cours pour l\'instant')}</p>
            <p class="empty-sub">{$i18n.t('Créez votre premier cours pour commencer')}</p>
            <button class="btn-create" on:click={() => goto('/teacher/courses')}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="15" height="15">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
                </svg>
                {$i18n.t('Créer un cours')}
            </button>
        </div>

    <!-- ── COURSES GRID ───────────────────────────────────────── -->
    {:else}
        <div class="courses-grid">
            {#each courses as course (course.id)}
                <div
                    class="course-card {course.id === newCourseId ? 'new-highlight' : ''}"
                    in:fly={{ y: 12, duration: 250 }}
                >
                    <!-- NEW badge -->
                    {#if course.id === newCourseId}
                        <div class="new-badge" in:fly={{ x: 10, duration: 300 }}>
                            ✨ {$i18n.t('Nouveau')}
                        </div>
                    {/if}

                    <!-- Card header -->
                    <div class="cc-header">
                        <div class="cc-title-wrap">
                            <h3 class="cc-title">{course.title}</h3>
                            <p class="cc-meta">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                                {timeAgo(course.created_at, now)}
                            </p>
                        </div>
                        <div class="cc-level-dot" style="background:{levelColor(course.level)}" title={levelLabel(course.level)}></div>
                    </div>

                    <!-- Tags -->
                    <div class="cc-tags">
                        {#if course.language}
                            <span class="ctag ctag-blue">{course.language}</span>
                        {/if}
                        {#if course.category}
                            <span class="ctag ctag-gray">{course.category}</span>
                        {/if}
                        <span class="ctag" style="background:{levelColor(course.level)}18; color:{levelColor(course.level)};">
                            {levelLabel(course.level)}
                        </span>
                    </div>

                    <!-- Participation code -->
                    <div class="cc-code-block">
                        <div class="cc-code-inner">
                            <div>
                                <p class="cc-code-label">{$i18n.t('Code de participation')}</p>
                                <p class="cc-code-value">{shortCode(course.id)}</p>
                            </div>
                            <button
                                class="cc-copy-btn {copiedId === course.id ? 'copied' : ''}"
                                on:click={() => copyCode(course.id)}
                                title={$i18n.t('Copier le code')}
                            >
                                {#if copiedId === course.id}
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="15" height="15">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                                    </svg>
                                {:else}
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="15" height="15">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                                    </svg>
                                {/if}
                                {copiedId === course.id ? $i18n.t('Copié !') : $i18n.t('Copier')}
                            </button>
                        </div>
                    </div>

                    <!-- Students row -->
                    <div class="cc-students-row">
                        <div class="cc-students-info">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
                            </svg>
                            <span class="cc-students-count">{course.student_count ?? 0}</span>
                            <span class="cc-students-label">
                                {(course.student_count ?? 0) <= 1
                                    ? $i18n.t('étudiant inscrit')
                                    : $i18n.t('étudiants inscrits')}
                            </span>
                        </div>
                    </div>

                    <!-- Footer — delete  -->
                    <div class="cc-footer">
                        <div></div>
                        <button
                            class="cc-delete-btn"
                            on:click={() => openDeleteModal(course.id)}
                            title={$i18n.t('Supprimer le cours')}
                        >
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                            </svg>
                        </button>
                    </div>
                </div>
            {/each}
        </div>
    {/if}

    <!-- ── QUIZZES SECTION HEADER ───────────────────────────────────── -->
    <div class="section-head" style="margin-top: 2.5rem;">
        <h2 class="section-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
            </svg>
            {$_('dashboard.my_quizzes')}
        </h2>
        <button class="btn-refresh" on:click={fetchQuizzesCount} title={$i18n.t('Actualiser')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="15" height="15">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
        </button>
    </div>

    <!-- ── LOADING ────────────────────────────────────────────── -->
    {#if isLoadingQuizzes}
        <div class="loading-grid">
            {#each [1,2] as _}
                <div class="skeleton-card">
                    <div class="skel skel-title"></div>
                    <div class="skel skel-sub"></div>
                    <div class="skel skel-code"></div>
                    <div class="skel skel-footer"></div>
                </div>
            {/each}
        </div>

    <!-- ── EMPTY ──────────────────────────────────────────────── -->
    {:else if teacherQuizzes.length === 0}
        <div class="empty-state" in:fly={{ y: 10, duration: 250 }}>
            <div class="empty-icon" style="background: rgba(126,34,206,.15); color: #7e22ce;">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="32" height="32">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
                </svg>
            </div>
            <p class="empty-title">{$i18n.t('Aucun quiz pour l\'instant')}</p>
            <p class="empty-sub">{$i18n.t('Générez votre premier quiz avec l\'IA pour commencer')}</p>
            <button class="btn-create" on:click={() => goto('/teacher/assignments')}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="15" height="15">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
                </svg>
                {$i18n.t('Créer un quiz')}
            </button>
        </div>

    <!-- ── QUIZZES GRID ───────────────────────────────────────── -->
    {:else}
        <div class="courses-grid">
            {#each teacherQuizzes as quiz (quiz.id)}
                <div class="course-card" in:fly={{ y: 12, duration: 250 }}>
                    <!-- Status tag -->
                    <div class="cc-header">
                        <div class="cc-title-wrap">
                            <h3 class="cc-title">{quiz.title}</h3>
                            <p class="cc-meta">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                                {timeAgo(quiz.created_at, now)}
                            </p>
                        </div>
                        <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-purple-50 dark:bg-purple-950/30 text-purple-600 dark:text-purple-400 self-start">
                            {quiz.status === 'published' ? $i18n.t('Publié') : $i18n.t('Brouillon')}
                        </span>
                    </div>

                    <!-- Details tags -->
                    <div class="cc-tags">
                        <span class="ctag ctag-gray">
                            {quiz.total_questions} {quiz.total_questions > 1 ? $i18n.t('questions') : $i18n.t('question')}
                        </span>
                        {#if quiz.time_limit}
                            <span class="ctag ctag-blue">
                                ⏱️ {quiz.time_limit} {$i18n.t('minutes')}
                            </span>
                        {/if}
                    </div>

                    <!-- Sharing code block (if published) -->
                    {#if quiz.status === 'published' && quiz.quiz_code}
                        <div class="cc-code-block" style="border-left-color: #7e22ce;">
                            <div class="cc-code-inner">
                                <div>
                                    <p class="cc-code-label">{$i18n.t('Code de partage')}</p>
                                    <p class="cc-code-value" style="color: #7e22ce;">{quiz.quiz_code}</p>
                                </div>
                                <button
                                    class="cc-copy-btn {copiedId === quiz.quiz_code ? 'copied' : ''}"
                                    on:click={() => copyCode(quiz.quiz_code)}
                                    title={$i18n.t('Copier le code')}
                                >
                                    {#if copiedId === quiz.quiz_code}
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="15" height="15">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                                        </svg>
                                    {:else}
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="15" height="15">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                                        </svg>
                                    {/if}
                                    {copiedId === quiz.quiz_code ? $i18n.t('Copié !') : $i18n.t('Copier')}
                                </button>
                            </div>
                        </div>
                    {/if}

                    <!-- Student participation row -->
                    <div class="cc-students-row" style="margin-top: auto;">
                        <div class="cc-students-info">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
                            </svg>
                            <span class="cc-students-count">{quiz.participants_count ?? 0}</span>
                            <span class="cc-students-label">
                                {(quiz.participants_count ?? 0) <= 1
                                    ? $i18n.t('étudiant a participé')
                                    : $i18n.t('étudiants ont participé')}
                            </span>
                        </div>
                    </div>
                </div>
            {/each}
        </div>
    {/if}

    <!-- ── DELETE CONFIRMATION MODAL ────────────────────────── -->
    {#if deletingCourseId}
        <div
            class="modal-overlay"
            role="button"
            tabindex="0"
            on:click={closeDeleteModal}
            on:keydown={(e) => e.key === 'Escape' && closeDeleteModal()}
            in:fade={{ duration: 200 }}
        >
            <div
                class="del-modal"
                role="dialog"
                aria-modal="true"
                on:click|stopPropagation
                on:keydown|stopPropagation
            >
                <div class="del-icon-wrap">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="28" height="28">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8"
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                </div>

                <h3 class="del-title">{$i18n.t('Supprimer ce cours ?')}</h3>
                <p class="del-sub">
                    {$i18n.t('Cette action est irréversible. Le cours, son plan et tous ses fichiers seront supprimés définitivement.')}
                </p>

                {#if deleteError}
                    <div class="del-error">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                        </svg>
                        {deleteError}
                    </div>
                {/if}

                <div class="del-actions">
                    <button class="btn-cancel" on:click={closeDeleteModal} disabled={isDeleting}>
                        {$i18n.t('Annuler')}
                    </button>
                    <button
                        class="btn-confirm-delete"
                        on:click={() => deleteCourse(deletingCourseId)}
                        disabled={isDeleting}
                    >
                        {#if isDeleting}
                            <svg class="spin-icon" viewBox="0 0 50 50" width="16" height="16">
                                <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="5"
                                    stroke-dasharray="80 40"/>
                            </svg>
                            {$i18n.t('Suppression...')}
                        {:else}
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="15" height="15">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                            </svg>
                            {$i18n.t('Supprimer définitivement')}
                        {/if}
                    </button>
                </div>
            </div>
        </div>
    {/if}

</div>

<style>
.dashboard {
    padding: 2rem;
    min-height: 100vh;
    background: #f3f5fb;
    font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif;
    color: #1e293b;
    max-width: 1300px;
    margin: 0 auto;
}
:global(.dark) .dashboard { background: #0f172a; color: #e2e8f0; }

.topbar {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 1rem; margin-bottom: 1.75rem;
}
.topbar-title { display: flex; align-items: center; gap: .875rem; }
.topbar-icon {
    width: 46px; height: 46px; border-radius: .875rem;
    background: linear-gradient(145deg, #3b5bdb, #2563eb);
    display: flex; align-items: center; justify-content: center;
    color: white; box-shadow: 0 8px 16px -6px rgba(37,99,235,.4);
}
.topbar-heading { font-size: 1.5rem; font-weight: 800; margin: 0; letter-spacing: -.02em; }
.topbar-sub { font-size: .8rem; color: #64748b; margin: .15rem 0 0; }
:global(.dark) .topbar-sub { color: #94a3b8; }

.btn-create {
    display: flex; align-items: center; gap: .5rem;
    background: linear-gradient(145deg, #3b5bdb, #2563eb);
    color: white; border: none; border-radius: .875rem;
    padding: .65rem 1.35rem; font-size: .9rem; font-weight: 700;
    cursor: pointer; transition: all .2s; font-family: inherit;
    box-shadow: 0 8px 16px -6px rgba(37,99,235,.4);
}
.btn-create:hover { transform: translateY(-2px); box-shadow: 0 12px 20px -8px rgba(37,99,235,.5); }

.new-banner {
    display: flex; align-items: center; gap: .75rem;
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: .875rem; padding: .875rem 1.25rem;
    font-size: .875rem; font-weight: 600; color: #16a34a;
    margin-bottom: 1.5rem;
}
:global(.dark) .new-banner { background: #052e16; border-color: #166534; color: #86efac; }

.stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-bottom: 1.75rem; }
.stat-card {
    background: white; border: 1px solid #e5e8f4; border-radius: 1rem;
    padding: 1.25rem 1.5rem; display: flex; align-items: center; gap: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
}
:global(.dark) .stat-card { background: #1e293b; border-color: #334155; }
.stat-icon { width: 44px; height: 44px; border-radius: .75rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stat-blue  { background: #eff6ff; color: #2563eb; }
.stat-green { background: #f0fdf4; color: #16a34a; }
.stat-purple { background: #f3e8ff; color: #7e22ce; }
:global(.dark) .stat-blue  { background: rgba(37,99,235,.15); }
:global(.dark) .stat-green { background: rgba(22,163,74,.15); }
:global(.dark) .stat-purple { background: rgba(126,34,206,.15); }
.stat-body { display: flex; flex-direction: column; gap: .2rem; }
.stat-label { font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .07em; color: #94a3b8; }
.stat-value { font-size: 1.75rem; font-weight: 800; color: #0f172a; line-height: 1; }
:global(.dark) .stat-value { color: #f1f5f9; }

.section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.section-title { display: flex; align-items: center; gap: .5rem; font-size: 1rem; font-weight: 700; margin: 0; color: #1e293b; }
:global(.dark) .section-title { color: #f1f5f9; }
.btn-refresh {
    background: white; border: 1px solid #e2e8f0; border-radius: .6rem;
    width: 34px; height: 34px; display: flex; align-items: center;
    justify-content: center; color: #64748b; cursor: pointer; transition: all .2s;
}
.btn-refresh:hover { background: #eff6ff; color: #2563eb; border-color: #bfdbfe; transform: rotate(90deg); }
:global(.dark) .btn-refresh { background: #1e293b; border-color: #334155; }

.err-banner {
    display: flex; align-items: center; gap: .75rem;
    background: #fef2f2; border: 1px solid #fecaca;
    border-radius: .875rem; padding: .875rem 1.25rem;
    font-size: .875rem; font-weight: 600; color: #dc2626; margin-bottom: 1.25rem;
}
:global(.dark) .err-banner { background: #450a0a; border-color: #991b1b; color: #fca5a5; }
.err-retry {
    margin-left: auto; padding: .35rem .75rem; border-radius: .5rem;
    background: white; border: 1px solid #fecaca; color: #dc2626;
    font-size: .8rem; font-weight: 600; cursor: pointer; font-family: inherit;
}

.loading-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.25rem; }
.skeleton-card {
    background: white; border: 1px solid #e5e8f4; border-radius: 1rem;
    padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem;
}
:global(.dark) .skeleton-card { background: #1e293b; border-color: #334155; }
.skel {
    border-radius: .5rem;
    background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
    background-size: 200% 100%; animation: shimmer 1.5s infinite;
}
:global(.dark) .skel { background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%); background-size: 200% 100%; }
.skel-title  { height: 20px; width: 70%; }
.skel-sub    { height: 14px; width: 45%; }
.skel-code   { height: 60px; }
.skel-footer { height: 36px; }
@keyframes shimmer { to { background-position: -200% 0; } }

.empty-state { display: flex; flex-direction: column; align-items: center; gap: 1rem; padding: 4rem 2rem; text-align: center; }
.empty-icon { width: 72px; height: 72px; background: #eff6ff; border-radius: 1.5rem; display: flex; align-items: center; justify-content: center; color: #2563eb; }
:global(.dark) .empty-icon { background: rgba(37,99,235,.1); }
.empty-title { font-size: 1.1rem; font-weight: 700; margin: 0; color: #1e293b; }
:global(.dark) .empty-title { color: #f1f5f9; }
.empty-sub { font-size: .875rem; color: #64748b; margin: 0; }

.courses-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 1.25rem; }

.course-card {
    background: white; border: 1.5px solid #e5e8f4;
    border-radius: 1.25rem; padding: 1.5rem;
    display: flex; flex-direction: column; gap: .875rem;
    box-shadow: 0 2px 8px rgba(0,0,0,.04);
    transition: all .25s; position: relative; overflow: hidden;
}
.course-card:hover { transform: translateY(-3px); box-shadow: 0 12px 24px -8px rgba(0,0,0,.1); border-color: #bfdbfe; }
:global(.dark) .course-card { background: #1e293b; border-color: #334155; }
:global(.dark) .course-card:hover { border-color: #3b5bdb; }
.course-card.new-highlight { border-color: #3b5bdb; box-shadow: 0 0 0 3px rgba(59,91,219,.12), 0 12px 24px -8px rgba(59,91,219,.2); }
:global(.dark) .course-card.new-highlight { box-shadow: 0 0 0 3px rgba(96,165,250,.2), 0 12px 24px -8px rgba(59,91,219,.3); }

.new-badge {
    position: absolute; top: 1rem; right: 1rem;
    background: linear-gradient(135deg, #3b5bdb, #2563eb);
    color: white; font-size: .68rem; font-weight: 800;
    padding: .25rem .65rem; border-radius: 2rem; letter-spacing: .04em;
}

.cc-header { display: flex; align-items: flex-start; justify-content: space-between; gap: .75rem; }
.cc-title-wrap { flex: 1; min-width: 0; }
.cc-title { font-size: 1rem; font-weight: 700; color: #0f172a; margin: 0 0 .3rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-right: 2.5rem; }
:global(.dark) .cc-title { color: #f1f5f9; }
.cc-meta { display: flex; align-items: center; gap: .35rem; font-size: .75rem; color: #94a3b8; margin: 0; }
.cc-level-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; box-shadow: 0 0 0 3px rgba(0,0,0,.08); }

.cc-tags { display: flex; flex-wrap: wrap; gap: .35rem; }
.ctag { font-size: .7rem; font-weight: 600; padding: .2rem .6rem; border-radius: 9999px; }
.ctag-blue { background: #dbe4ff; color: #3b5bdb; }
.ctag-gray { background: #f1f5f9; color: #64748b; }
:global(.dark) .ctag-blue { background: rgba(59,91,219,.2); color: #93c5fd; }
:global(.dark) .ctag-gray { background: #334155; color: #94a3b8; }

.cc-code-block { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: .875rem; padding: .875rem 1rem; }
:global(.dark) .cc-code-block { background: #0f172a; border-color: #1e293b; }
.cc-code-inner { display: flex; align-items: center; justify-content: space-between; gap: .75rem; }
.cc-code-label { font-size: .65rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #94a3b8; margin: 0 0 .3rem; }
.cc-code-value { font-size: .8rem; font-weight: 700; color: #2563eb; font-family: 'Courier New', monospace; margin: 0; letter-spacing: .03em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px; }
:global(.dark) .cc-code-value { color: #60a5fa; }
.cc-copy-btn {
    display: flex; align-items: center; gap: .35rem;
    background: white; border: 1.5px solid #e2e8f0; border-radius: .625rem;
    padding: .45rem .75rem; font-size: .78rem; font-weight: 600; color: #2563eb;
    cursor: pointer; transition: all .2s; white-space: nowrap; font-family: inherit; flex-shrink: 0;
}
.cc-copy-btn:hover { background: #eff6ff; border-color: #bfdbfe; }
.cc-copy-btn.copied { background: #f0fdf4; border-color: #bbf7d0; color: #16a34a; }
:global(.dark) .cc-copy-btn { background: #1e293b; border-color: #334155; }
:global(.dark) .cc-copy-btn.copied { background: #052e16; border-color: #166534; color: #86efac; }

.cc-students-row {
    background: #f0fdf4; border: 1px solid #d1fae5;
    border-radius: .75rem; padding: .6rem .875rem;
}
:global(.dark) .cc-students-row { background: rgba(22,163,74,.08); border-color: rgba(22,163,74,.2); }
.cc-students-info { display: flex; align-items: center; gap: .4rem; color: #16a34a; }
:global(.dark) .cc-students-info { color: #4ade80; }
.cc-students-count { font-size: 1rem; font-weight: 800; color: #15803d; line-height: 1; }
:global(.dark) .cc-students-count { color: #4ade80; }
.cc-students-label { font-size: .78rem; font-weight: 500; color: #16a34a; }
:global(.dark) .cc-students-label { color: #4ade80; }

.cc-footer { display: flex; align-items: center; justify-content: flex-end; padding-top: .125rem; }

.cc-delete-btn {
    display: flex; align-items: center; justify-content: center;
    width: 32px; height: 32px;
    background: #fff5f5; border: 1px solid #fecaca;
    border-radius: .6rem; color: #ef4444;
    cursor: pointer; transition: all .2s; flex-shrink: 0;
}
.cc-delete-btn:hover { background: #ef4444; color: white; border-color: #ef4444; transform: scale(1.05); }
:global(.dark) .cc-delete-btn { background: rgba(239,68,68,.1); border-color: rgba(239,68,68,.3); color: #f87171; }
:global(.dark) .cc-delete-btn:hover { background: #ef4444; border-color: #ef4444; color: white; }

.cc-manage-btn {
    display: flex; align-items: center; gap: .3rem;
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: .6rem;
    padding: .45rem .875rem; font-size: .8rem; font-weight: 600; color: #1e293b;
    cursor: pointer; transition: all .2s; font-family: inherit;
}
.cc-manage-btn:hover { background: #2563eb; color: white; border-color: #2563eb; }
:global(.dark) .cc-manage-btn { background: #334155; border-color: #475569; color: #e2e8f0; }
:global(.dark) .cc-manage-btn:hover { background: #3b5bdb; border-color: #3b5bdb; }

.modal-overlay {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(15,23,42,0.6); backdrop-filter: blur(6px);
    display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.del-modal {
    background: white; border-radius: 1.5rem; padding: 2.25rem 2rem 2rem;
    max-width: 400px; width: 92%;
    box-shadow: 0 32px 64px -12px rgba(0,0,0,.25), 0 0 0 1px rgba(0,0,0,.04);
    text-align: center;
    animation: slideUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
:global(.dark) .del-modal { background: #1e293b; border: 1px solid #334155; }

.del-icon-wrap {
    width: 68px; height: 68px; border-radius: 50%;
    background: #fff5f5; border: 2px solid #fecaca;
    display: flex; align-items: center; justify-content: center;
    color: #ef4444; margin: 0 auto 1.25rem;
}
:global(.dark) .del-icon-wrap { background: rgba(239,68,68,.1); border-color: rgba(239,68,68,.3); color: #f87171; }

.del-title { font-size: 1.25rem; font-weight: 800; color: #0f172a; margin: 0 0 .625rem; letter-spacing: -.02em; }
:global(.dark) .del-title { color: #f1f5f9; }
.del-sub { font-size: .875rem; color: #64748b; margin: 0 0 1.5rem; line-height: 1.6; }
:global(.dark) .del-sub { color: #94a3b8; }

.del-error {
    display: flex; align-items: center; gap: .5rem; font-size: .8rem; color: #dc2626;
    background: #fef2f2; border: 1px solid #fecaca; border-radius: .6rem;
    padding: .6rem .875rem; margin-bottom: 1.25rem; text-align: left;
}
:global(.dark) .del-error { background: #450a0a; border-color: #991b1b; color: #fca5a5; }

.del-actions { display: flex; gap: .75rem; }
.btn-cancel {
    flex: 1; padding: .75rem 1rem; border-radius: .875rem;
    border: 1.5px solid #e2e8f0; background: white;
    color: #475569; font-weight: 600; font-size: .9rem;
    cursor: pointer; transition: all .15s; font-family: inherit;
}
.btn-cancel:hover:not(:disabled) { background: #f8fafc; border-color: #cbd5e1; }
.btn-cancel:disabled { opacity: .5; cursor: not-allowed; }
:global(.dark) .btn-cancel { background: #334155; border-color: #475569; color: #cbd5e1; }
:global(.dark) .btn-cancel:hover:not(:disabled) { background: #475569; }

.btn-confirm-delete {
    flex: 1; padding: .75rem 1rem; border-radius: .875rem; border: none;
    background: linear-gradient(145deg, #f43f5e, #ef4444);
    color: white; font-weight: 700; font-size: .9rem;
    cursor: pointer; transition: all .2s; font-family: inherit;
    display: flex; align-items: center; justify-content: center; gap: .5rem;
    box-shadow: 0 8px 16px -6px rgba(239,68,68,.4);
}
.btn-confirm-delete:hover:not(:disabled) {
    background: linear-gradient(145deg, #e11d48, #dc2626);
    transform: translateY(-1px); box-shadow: 0 12px 20px -8px rgba(239,68,68,.5);
}
.btn-confirm-delete:disabled { opacity: .6; cursor: not-allowed; transform: none; }

.spin-icon { animation: spin 0.8s linear infinite; }

@keyframes spin    { to { transform: rotate(360deg); } }
@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

@media (max-width: 640px) {
    .dashboard { padding: 1rem; }
    .stats-row { grid-template-columns: 1fr; }
    .courses-grid { grid-template-columns: 1fr; }
    .topbar { flex-direction: column; align-items: flex-start; }
    .del-actions { flex-direction: column; }
}
</style>