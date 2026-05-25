<!--
  CoursePlanEditor.svelte — UPDATED
  - Reads real plan from courseData.plan (passed via goto state)
  - Saves to DB via PUT /teacher/courses/{course_id}/plan
  - No more hardcoded mock chapters
  - On "Continuer" in code modal → redirect to dashboard with highlight
-->
<script lang="ts">
    import { getContext } from 'svelte';
    import { goto } from '$app/navigation';
    import { fly } from 'svelte/transition';
    import { cubicOut } from 'svelte/easing';
    import { courseCreationData } from '$lib/stores';
    import { TUTOR_FRONT_URL } from '$lib/constants';

    const i18n = getContext('i18n');

    // ── PROPS ─────────────────────────────────────────────────────
    export let courseData: {
        course_id: string;
        title: string;
        language: string;
        category: string;
        level: string;
        objectives: string;         
        aiObjectives?: string;       
        files: File[];
        plan?: { chapters: Chapter[] };
    };

    // ── TYPES ─────────────────────────────────────────────────────
    interface Section {
        id: string;
        title: string;
    }
    interface Chapter {
        id: string;
        title: string;
        sections: Section[];
    }

    // ── STATE ──────────────────────────────────────────────────────
    let chapters: Chapter[] = (courseData.plan?.chapters ?? []).map(ch => ({
        id:       ch.id       ?? crypto.randomUUID(),
        title:    ch.title    ?? '',
        sections: (ch.sections ?? []).map(s => ({
            id:    s.id    ?? crypto.randomUUID(),
            title: s.title ?? '',
        })),
    }));

    let editableObjectives = courseData.aiObjectives ?? courseData.objectives ?? '';

    let newChapterTitle = '';
    let editingChapterId: string | null = null;
    let editingChapterTitle = '';

    let newSectionTitle = '';
    let addingSectionForChapterId: string | null = null;
    let editingSection: { chapterId: string; sectionId: string } | null = null;
    let editingSectionTitle = '';

    let expandedChapters = new Set(chapters.map(c => c.id));

    let isSaving = false;
    let saveError = '';
    let saveSuccess = false;

    let showCodeModal = false;
    let courseCode = courseData.course_id;

    // ── UTILS ─────────────────────────────────────────────────────
    function generateId(): string { return crypto.randomUUID(); }

    function toggleChapter(id: string) {
        expandedChapters.has(id) ? expandedChapters.delete(id) : expandedChapters.add(id);
        expandedChapters = new Set(expandedChapters);
    }

    // ── CHAPTER OPS ────────────────────────────────────────────────
    function addChapter() {
        if (!newChapterTitle.trim()) return;
        const id = generateId();
        chapters = [...chapters, { id, title: newChapterTitle.trim(), sections: [] }];
        expandedChapters.add(id);
        expandedChapters = new Set(expandedChapters);
        newChapterTitle = '';
    }
    function startEditChapter(ch: Chapter) {
        editingChapterId = ch.id;
        editingChapterTitle = ch.title;
    }
    function saveEditChapter() {
        if (editingChapterId && editingChapterTitle.trim()) {
            chapters = chapters.map(c =>
                c.id === editingChapterId ? { ...c, title: editingChapterTitle.trim() } : c
            );
        }
        editingChapterId = null; editingChapterTitle = '';
    }
    function cancelEditChapter() { editingChapterId = null; editingChapterTitle = ''; }
    function deleteChapter(id: string) {
        chapters = chapters.filter(c => c.id !== id);
        expandedChapters.delete(id);
        expandedChapters = new Set(expandedChapters);
    }

    // ── SECTION OPS ────────────────────────────────────────────────
    function startAddSection(chapterId: string) {
        addingSectionForChapterId = chapterId;
        newSectionTitle = '';
        if (!expandedChapters.has(chapterId)) {
            expandedChapters.add(chapterId);
            expandedChapters = new Set(expandedChapters);
        }
    }
    function addSection(chapterId: string) {
        if (!newSectionTitle.trim()) return;
        chapters = chapters.map(ch =>
            ch.id === chapterId
                ? { ...ch, sections: [...ch.sections, { id: generateId(), title: newSectionTitle.trim() }] }
                : ch
        );
        addingSectionForChapterId = null; newSectionTitle = '';
    }
    function cancelAddSection() { addingSectionForChapterId = null; newSectionTitle = ''; }

    function startEditSection(chapterId: string, sec: Section) {
        editingSection = { chapterId, sectionId: sec.id };
        editingSectionTitle = sec.title;
    }
    function saveEditSection() {
        if (editingSection && editingSectionTitle.trim()) {
            const { chapterId, sectionId } = editingSection;
            chapters = chapters.map(ch =>
                ch.id === chapterId
                    ? { ...ch, sections: ch.sections.map(s => s.id === sectionId ? { ...s, title: editingSectionTitle.trim() } : s) }
                    : ch
            );
        }
        editingSection = null; editingSectionTitle = '';
    }
    function cancelEditSection() { editingSection = null; editingSectionTitle = ''; }
    function deleteSection(chapterId: string, sectionId: string) {
        chapters = chapters.map(ch =>
            ch.id === chapterId
                ? { ...ch, sections: ch.sections.filter(s => s.id !== sectionId) }
                : ch
        );
    }

    // ── SAVE PLAN TO DB ────────────────────────────────────────────
    async function savePlan() {
        isSaving = true; saveError = ''; saveSuccess = false;
        try {
            const token = localStorage.getItem('token') ?? '';
            const res = await fetch(`/api/v1/teacher/courses/${courseData.course_id}/plan`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    chapters,
                    objectives: editableObjectives,
                }),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                saveError = err.detail ?? $i18n.t('Erreur lors de la sauvegarde');
                return;
            }
            saveSuccess = true;
            setTimeout(() => saveSuccess = false, 3000);
        } catch {
            saveError = $i18n.t('Erreur réseau');
        } finally {
            isSaving = false;
        }
    }

    // ── VALIDATE (save + show modal with code) ──────────────────────────────────
    async function validateCourse() {
        await savePlan();
        if (!saveError) {
            showCodeModal = true;
        }
    }

    // ── CLOSE MODAL → redirect to dashboard with highlight ──────────
    function closeCodeModal() {
        showCodeModal = false;
        // Clear saved form data
        courseCreationData.set({
            courseTitle: '',
            courseLanguage: 'fr-FR',
            courseCategory: '',
            customCategory: '',
            courseLevel: '',
            pedagogicalObjectives: '',
            uploadedFiles: [],
            selectedModel: ''
        });
        // Redirect to dashboard, passing the new course id so it shows highlighted
        goto(`/teacher/dashboard?newCourse=${courseData.course_id}`);
    }

    function copyCodeToClipboard() {
        navigator.clipboard.writeText(courseCode);
    }

    // ── BACK TO EDIT COURSE ──────────────────────────────────────
    function goBackToEditCourse() {
        courseCreationData.set({
            courseTitle: courseData.title,
            courseLanguage: courseData.language,
            courseCategory: courseData.category,
            customCategory: (courseData as any).custom_category || '',
            courseLevel: courseData.level,
            pedagogicalObjectives: courseData.objectives || '',
            uploadedFiles: courseData.files || [],
            selectedModel: ''
        });
        goto('/teacher/courses?view=create');
    }

    // ── REACTIVE ──────────────────────────────────────────────────
    $: totalSections = chapters.reduce((acc, ch) => acc + ch.sections.length, 0);
</script>

<!-- ==================== TEMPLATE ==================== -->
<div class="plan-editor">

    <!-- Hero -->
    <div class="hero">
        <div class="hero-content">
            <div class="hero-eyebrow">{$i18n.t('Plan du cours')}</div>
            <h1 class="hero-title">{courseData.title}</h1>
            <div class="hero-tags">
                <span class="htag htag-blue">{courseData.language}</span>
                <span class="htag htag-green">{courseData.category}</span>
                <span class="htag htag-amber">{courseData.level}</span>
            </div>
        </div>
        <div class="hero-stats">
            <div class="hstat">
                <span class="hstat-n">{chapters.length}</span>
                <span class="hstat-l">{$i18n.t('Chapitres')}</span>
            </div>
            <div class="hstat-sep"></div>
            <div class="hstat">
                <span class="hstat-n">{totalSections}</span>
                <span class="hstat-l">{$i18n.t('Sections')}</span>
            </div>
            <div class="hstat-sep"></div>
            <div class="hstat">
                <span class="hstat-n">{courseData.files?.length ?? 0}</span>
                <span class="hstat-l">{$i18n.t('Fichiers')}</span>
            </div>
        </div>
    </div>

    <!-- Save feedback banner -->
    {#if saveError}
        <div class="banner banner-error" in:fly={{ y: -8, duration: 200 }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
            </svg>
            {saveError}
            <button class="banner-close" on:click={() => saveError = ''}>✕</button>
        </div>
    {/if}
    {#if saveSuccess}
        <div class="banner banner-ok" in:fly={{ y: -8, duration: 200 }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
            </svg>
            {$i18n.t('Plan sauvegardé avec succès !')}
        </div>
    {/if}

    <!-- Empty plan warning -->
    {#if chapters.length === 0}
        <div class="empty-plan-warn" in:fly={{ y: 8, duration: 250 }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="20" height="20">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            {$i18n.t('Aucun chapitre généré — ajoutez-en manuellement ci-dessous.')}
        </div>
    {/if}

    <!-- Main grid -->
    <div class="editor-main">

        <!-- LEFT: structure -->
        <div class="card">
            <div class="card-head">
                <div class="card-icon blue-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h10M4 18h6"/>
                    </svg>
                </div>
                <div>
                    <div class="card-title">{$i18n.t('Structure du cours')}</div>
                    <div class="card-sub">{$i18n.t('Chapitres & sections')}</div>
                </div>
            </div>

            <div class="ch-list">
                {#each chapters as ch, idx (ch.id)}
                    <div class="ch-block" in:fly={{ y: 10, duration: 220, easing: cubicOut }}>
                        <div class="ch-row" class:open={expandedChapters.has(ch.id)}>
                            <button class="ch-toggle" on:click={() => toggleChapter(ch.id)}>
                                <span class="ch-num">{String(idx+1).padStart(2,'0')}</span>
                                <svg class="ch-arr" class:rotated={expandedChapters.has(ch.id)}
                                    viewBox="0 0 24 24" fill="none" stroke="currentColor" width="13" height="13">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 18l6-6-6-6"/>
                                </svg>
                            </button>

                            {#if editingChapterId === ch.id}
                                <div class="iedit">
                                    <input type="text" bind:value={editingChapterTitle} class="ifield"
                                        on:keydown={(e)=>{ if(e.key==='Enter') saveEditChapter(); if(e.key==='Escape') cancelEditChapter(); }}/>
                                    <button class="iact ok" on:click={saveEditChapter}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="13" height="13"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg></button>
                                    <button class="iact no" on:click={cancelEditChapter}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="13" height="13"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/></svg></button>
                                </div>
                            {:else}
                                <span class="ch-name">{ch.title}</span>
                                <div class="acts">
                                    <button class="iact ed" on:click={() => startEditChapter(ch)} title={$i18n.t('Modifier')}>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="13" height="13"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                                    </button>
                                    <button class="iact rm" on:click={() => deleteChapter(ch.id)} title={$i18n.t('Supprimer')}>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="13" height="13"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                                    </button>
                                </div>
                            {/if}
                        </div>

                        {#if expandedChapters.has(ch.id)}
                            <div class="sec-list" transition:fly={{ y: -6, duration: 200, easing: cubicOut }}>
                                {#each ch.sections as sec (sec.id)}
                                    <div class="sec-row" in:fly={{ x: -6, duration: 200 }}>
                                        <span class="sec-dot"></span>
                                        {#if editingSection?.chapterId === ch.id && editingSection?.sectionId === sec.id}
                                            <div class="iedit">
                                                <input type="text" bind:value={editingSectionTitle} class="ifield sm"
                                                    on:keydown={(e)=>{ if(e.key==='Enter') saveEditSection(); if(e.key==='Escape') cancelEditSection(); }}/>
                                                <button class="iact ok" on:click={saveEditSection}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg></button>
                                                <button class="iact no" on:click={cancelEditSection}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/></svg></button>
                                            </div>
                                        {:else}
                                            <span class="sec-name">{sec.title}</span>
                                            <div class="acts sec-acts">
                                                <button class="iact ed" on:click={() => startEditSection(ch.id, sec)} title={$i18n.t('Modifier')}>
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                                                </button>
                                                <button class="iact rm" on:click={() => deleteSection(ch.id, sec.id)} title={$i18n.t('Supprimer')}>
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                                                </button>
                                            </div>
                                        {/if}
                                    </div>
                                {/each}

                                {#if addingSectionForChapterId === ch.id}
                                    <div class="sec-row new-sec-row" transition:fly={{ x: -6, duration: 200 }}>
                                        <span class="sec-dot accent-dot"></span>
                                        <div class="iedit">
                                            <input type="text" bind:value={newSectionTitle} class="ifield sm"
                                                placeholder={$i18n.t('Titre de la section')}
                                                on:keydown={(e)=>{ if(e.key==='Enter') addSection(ch.id); if(e.key==='Escape') cancelAddSection(); }}/>
                                            <button class="iact ok" on:click={() => addSection(ch.id)}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg></button>
                                            <button class="iact no" on:click={cancelAddSection}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/></svg></button>
                                        </div>
                                    </div>
                                {:else}
                                    <button class="add-sec-btn" on:click={() => startAddSection(ch.id)}>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/></svg>
                                        {$i18n.t('Ajouter une section')}
                                    </button>
                                {/if}
                            </div>
                        {/if}
                    </div>
                {/each}

                <div class="add-ch-row">
                    <input type="text" bind:value={newChapterTitle} class="add-ch-input"
                        placeholder={$i18n.t('Titre du nouveau chapitre...')}
                        on:keydown={(e) => e.key === 'Enter' && addChapter()}/>
                    <button class="add-ch-btn" on:click={addChapter}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/></svg>
                        {$i18n.t('Ajouter')}
                    </button>
                </div>
            </div>
        </div>

        <!-- RIGHT: objectives + files -->
        <div class="right-col">
            <div class="card">
                <div class="card-head">
                    <div class="card-icon green-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                    </div>
                    <div>
                        <div class="card-title">{$i18n.t('Objectifs pédagogiques')}</div>
                        <div class="card-sub">{$i18n.t('Générés par l\'IA - modifiables')}</div>
                    </div>
                </div>

                <div class="ai-badge">AI-Generated</div>

                <textarea
                    bind:value={editableObjectives}
                    class="obj-ta"
                    rows="11"
                    placeholder={$i18n.t("À la fin de ce cours, l'étudiant sera capable de...")}
                ></textarea>
            </div>

            <div class="card">
                <div class="card-head small-head">
                    <div class="card-icon gray-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
                        </svg>
                    </div>
                    <div class="files-head">
                        {$i18n.t('Fichiers sources')}
                        <span class="files-count">{courseData.files?.length ?? 0}</span>
                    </div>
                </div>
                <div class="files-body">
                    {#each (courseData.files ?? []) as file}
                        <div class="file-chip">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                            </svg>
                            {file.name}
                        </div>
                    {/each}
                </div>
            </div>
        </div>
    </div>

    <!-- Bottom actions -->
    <div class="editor-actions">
        <button class="btn-outline" on:click={goBackToEditCourse}>
            {$i18n.t('Retour')}
        </button>
        <button class="btn-primary" on:click={validateCourse} disabled={isSaving}>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="18" height="18">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            {$i18n.t('Valider le cours')}
        </button>
    </div>

    <!-- ═══════════════════════════════════════════════════════
         CODE MODAL — updated: "Continuer" → dashboard redirect
         ═══════════════════════════════════════════════════════ -->
    {#if showCodeModal}
        <div
            class="modal-overlay"
            role="button"
            tabindex="0"
            on:click={closeCodeModal}
            on:keydown={(e) => e.key === 'Escape' && closeCodeModal()}
        >
            <div
                class="modal-card"
                role="dialog"
                aria-modal="true"
                on:click|stopPropagation
                on:keydown|stopPropagation
            >
                <button class="modal-close" on:click={closeCodeModal} aria-label="Fermer">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="20" height="20">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>

                <div class="code-modal-content">
                    <!-- Success badge -->
                    <div class="code-success-badge">
                        <img src="{TUTOR_FRONT_URL}/static/favicon.png" alt="OT AI" class="code-logo" />
                        <div class="code-check-badge">
                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="14" height="14">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                            </svg>
                        </div>
                    </div>

                    <h2 class="code-modal-title">{$i18n.t('Cours créé avec succès !')}</h2>
                    <p class="code-modal-subtitle">{$i18n.t('Partagez ce code avec vos étudiants pour qu\'ils rejoignent le cours')}</p>

                    <!-- Course title display -->
                    <div class="course-title-display">
                        <span class="course-title-label">{$i18n.t('Cours')}</span>
                        <span class="course-title-value">{courseData.title}</span>
                    </div>

                    <!-- Code box -->
                    <div class="code-display">
                        <p class="code-label">{$i18n.t('Code de participation')}</p>
                        <div class="code-box">
                            <span class="code-text">{courseCode}</span>
                            <button class="copy-btn" on:click={copyCodeToClipboard} title={$i18n.t('Copier le code')}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="17" height="17">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                                </svg>
                                {$i18n.t('Copier')}
                            </button>
                        </div>
                    </div>

                    <p class="code-hint">
                        {$i18n.t('Les étudiants entreront ce code pour rejoindre votre cours.')}
                    </p>

                    <!-- Continuer → redirect to dashboard -->
                    <button class="btn-primary-modal" on:click={closeCodeModal}>
                        {$i18n.t('Continuer vers le tableau de bord')}
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="16" height="16">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    {/if}
</div>

<!-- ==================== STYLES ==================== -->
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

.plan-editor {
    font-family: 'Plus Jakarta Sans', sans-serif;
    max-width: 1400px; margin: 0 auto;
    padding: 0 0 1.5rem; color: #1e293b;
    background: #f3f5fb; min-height: 100vh;
}
:global(.dark) .plan-editor { color: #e2e8f0; background: #0f172a; }

/* banners */
.banner {
    display: flex; align-items: center; gap: .75rem;
    margin: 0 2rem 1.25rem; padding: .875rem 1.25rem;
    border-radius: .875rem; font-size: .875rem; font-weight: 600;
}
.banner-error { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; }
.banner-ok    { background: #f0fdf4; border: 1px solid #bbf7d0; color: #16a34a; }
:global(.dark) .banner-error { background: #450a0a; border-color: #991b1b; color: #fca5a5; }
:global(.dark) .banner-ok    { background: #052e16; border-color: #166534; color: #86efac; }
.banner-close { margin-left: auto; background: none; border: none; cursor: pointer; color: inherit; font-size: 1rem; }

.empty-plan-warn {
    display: flex; align-items: center; gap: .6rem;
    margin: 0 2rem 1.25rem; padding: .875rem 1.25rem;
    background: #fffbeb; border: 1px solid #fde68a; border-radius: .875rem;
    font-size: .875rem; font-weight: 500; color: #92400e;
}
:global(.dark) .empty-plan-warn { background: #451a03; border-color: #92400e; color: #fde68a; }

/* hero */
.hero {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 1.5rem;
    padding: 2rem 1.75rem 1.875rem;
    background: linear-gradient(135deg,#fff 0%,#eef1ff 100%);
    border-bottom: 1px solid #e0e4f5; margin-bottom: 2rem; border-radius: .5rem;
}
:global(.dark) .hero { background: linear-gradient(135deg,#1e293b 0%,#0f172a 100%); border-bottom-color: #334155; }
.hero-content { flex: 1; }
.hero-eyebrow { font-size:.68rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:#3b5bdb; margin-bottom:.5rem; }
:global(.dark) .hero-eyebrow { color:#818cf8; }
.hero-title { font-size:clamp(1.5rem,3vw,2.25rem); font-weight:800; color:#111428; margin:0 0 .875rem; letter-spacing:-.025em; line-height:1.15; }
:global(.dark) .hero-title { color:#f8fafc; }
.hero-tags { display:flex; gap:.45rem; flex-wrap:wrap; }
.htag { font-size:.72rem; font-weight:600; padding:.25rem .75rem; border-radius:9999px; }
.htag-blue { background:#dbe4ff; color:#3b5bdb; }
.htag-green{ background:#d3f9d8; color:#2f9e44; }
.htag-amber{ background:#fff3bf; color:#e67700; }
:global(.dark) .htag-blue { background:#1e3a8a; color:#bfdbfe; }
:global(.dark) .htag-green{ background:#14532d; color:#bbf7d0; }
:global(.dark) .htag-amber{ background:#78350f; color:#fde68a; }
.hero-stats { display:flex; align-items:center; gap:1.75rem; background:white; border:1px solid #e5e8f4; border-radius:1rem; padding:1.125rem 1.75rem; box-shadow:0 1px 6px rgba(0,0,0,.04); }
:global(.dark) .hero-stats { background:#1e293b; border-color:#334155; }
.hstat { display:flex; flex-direction:column; align-items:center; gap:.15rem; }
.hstat-n { font-size:1.75rem; font-weight:800; color:#1a1d2e; line-height:1; }
:global(.dark) .hstat-n { color:#f1f5f9; }
.hstat-l { font-size:.65rem; font-weight:600; text-transform:uppercase; letter-spacing:.08em; color:#a0a8c3; }
.hstat-sep { width:1px; height:36px; background:#eaecf5; }
:global(.dark) .hstat-sep { background:#475569; }

/* layout */
.editor-main { display:grid; grid-template-columns:1.5fr 1fr; gap:1.75rem; margin-bottom:2.5rem; padding:0 2rem; }
.right-col { display:flex; flex-direction:column; gap:1.75rem; }
@media(max-width:900px){ .editor-main { grid-template-columns:1fr; padding:0 1rem; } .hero { padding:1.5rem 1rem; } }

/* card */
.card {
    background:rgba(255,255,255,.75); backdrop-filter:blur(12px);
    border:1px solid rgba(255,255,255,.5); border-radius:1rem; overflow:hidden;
    box-shadow:0 20px 35px -10px rgba(0,0,0,.08);
}
:global(.dark) .card { background:rgba(30,41,59,.75); border-color:rgba(255,255,255,.1); }
.card-head { display:flex; align-items:center; gap:1rem; padding:1.5rem 1.75rem; border-bottom:1px solid rgba(203,213,225,.3); }
.small-head { padding:1.25rem 1.5rem; }
:global(.dark) .card-head { border-bottom-color:rgba(51,65,85,.6); }
.card-icon { width:42px; height:42px; border-radius:1rem; display:flex; align-items:center; justify-content:center; }
.blue-icon  { background:linear-gradient(145deg,#3b5bdb,#2563eb); color:white; box-shadow:0 8px 15px -5px rgba(59,91,219,.4); }
.green-icon { background:linear-gradient(145deg,#2b8c4a,#16a34a); color:white; box-shadow:0 8px 15px -5px rgba(43,140,74,.4); }
.gray-icon  { background:linear-gradient(145deg,#94a3b8,#64748b); color:white; width:34px; height:34px; border-radius:.8rem; }
:global(.dark) .blue-icon  { background:linear-gradient(145deg,#4f6edb,#3b5bdb); }
:global(.dark) .green-icon { background:linear-gradient(145deg,#3a9e5a,#2b8c4a); }
.card-title { font-size:1rem; font-weight:700; color:#0f172a; }
.card-sub   { font-size:.8rem; color:#64748b; margin-top:.2rem; font-weight:500; }
:global(.dark) .card-title { color:#f8fafc; }
:global(.dark) .card-sub   { color:#94a3b8; }

/* chapters */
.ch-list { padding:.5rem 0 0; }
.ch-block { border-bottom:1px solid rgba(225,203,217,.2); }
.ch-block:last-child { border-bottom:none; }
:global(.dark) .ch-block { border-bottom-color:rgba(51,65,85,.5); }
.ch-row { display:flex; align-items:center; gap:.875rem; padding:.875rem 1.75rem; transition:background .2s,padding-left .2s; border-radius:0; }
.ch-row:hover,.ch-row.open { background:rgba(59,91,219,.04); padding-left:2rem; }
:global(.dark) .ch-row:hover,:global(.dark) .ch-row.open { background:rgba(96,165,250,.08); }
.ch-toggle { display:flex; align-items:center; gap:.6rem; background:none; border:none; cursor:pointer; padding:0; flex-shrink:0; }
.ch-num { font-size:.75rem; font-weight:800; color:#3b5bdb; background:rgba(59,91,219,.1); padding:.2rem .4rem; border-radius:.5rem; min-width:28px; text-align:center; }
:global(.dark) .ch-num { color:#93c5fd; background:rgba(96,165,250,.15); }
.ch-arr { color:#64748b; transition:transform .25s cubic-bezier(.34,1.56,.64,1); }
.ch-arr.rotated { transform:rotate(90deg); }
.ch-name { flex:1; font-size:.95rem; font-weight:600; color:#1e293b; }
:global(.dark) .ch-name { color:#e2e8f0; }
.sec-list { margin-left:3.75rem; border-left:2px solid rgba(59,91,219,.2); padding:.35rem 0 .875rem; }
:global(.dark) .sec-list { border-left-color:rgba(96,165,250,.3); }
.sec-row { display:flex; align-items:center; gap:.875rem; padding:.5rem 1.25rem; border-radius:.75rem; margin:.1rem .5rem; transition:all .2s; }
.sec-row:hover { background:rgba(59,91,219,.05); padding-left:1.5rem; }
:global(.dark) .sec-row:hover { background:rgba(96,165,250,.08); }
.sec-dot { width:7px; height:7px; border-radius:2px; flex-shrink:0; background:#3b5bdb; transform:rotate(45deg); opacity:.7; }
.accent-dot { background:#10b981; opacity:1; box-shadow:0 0 0 2px rgba(16,185,129,.2); }
.sec-name { flex:1; font-size:.875rem; color:#475569; font-weight:500; }
:global(.dark) .sec-name { color:#cbd5e1; }
.add-sec-btn { display:flex; align-items:center; gap:.6rem; background:none; border:1.5px dashed rgba(59,91,219,.4); border-radius:1rem; cursor:pointer; font-size:.8rem; font-weight:600; color:#3b5bdb; padding:.6rem 1.2rem; margin-left:.5rem; width:calc(100% - 1rem); transition:all .2s; justify-content:center; }
.add-sec-btn:hover { background:rgba(59,91,219,.05); border-color:#3b5bdb; }
:global(.dark) .add-sec-btn { border-color:rgba(96,165,250,.4); color:#90aef8; }
.add-ch-row { display:flex; gap:.875rem; padding:1.25rem 1.75rem; border-top:1px solid rgba(203,213,225,.3); background:rgba(248,250,252,.5); }
:global(.dark) .add-ch-row { background:rgba(15,23,42,.6); border-top-color:rgba(51,65,85,.6); }
.add-ch-input { flex:1; background:rgba(255,255,255,.9); border:1.5px solid rgba(203,213,225,.8); border-radius:1rem; padding:.7rem 1rem; font-size:.9rem; color:#1e293b; transition:all .2s; }
.add-ch-input:focus { border-color:#3b5bdb; box-shadow:0 0 0 4px rgba(59,91,219,.15); outline:none; }
:global(.dark) .add-ch-input { background:rgba(15,23,42,.8); border-color:#475569; color:white; }
:global(.dark) .add-ch-input:focus { border-color:#60a5fa; }
.add-ch-btn { background:linear-gradient(145deg,#3b5bdb,#2563eb); border:none; border-radius:1rem; padding:.7rem 1.5rem; font-size:.9rem; font-weight:700; color:white; cursor:pointer; display:flex; align-items:center; gap:.6rem; box-shadow:0 10px 18px -8px rgba(37,99,235,.4); transition:all .2s; }
.add-ch-btn:hover { transform:translateY(-2px); box-shadow:0 14px 22px -10px rgba(37,99,235,.5); }
.iedit { display:flex; align-items:center; gap:.5rem; flex:1; }
.ifield { flex:1; background:white; border:1.5px solid #cbd5e1; border-radius:.75rem; padding:.5rem .8rem; font-size:.9rem; color:#1e293b; transition:border .15s,box-shadow .15s; }
.ifield:focus { border-color:#3b5bdb; box-shadow:0 0 0 3px rgba(59,91,219,.1); outline:none; }
.ifield.sm { font-size:.85rem; padding:.45rem .7rem; }
:global(.dark) .ifield { background:#1e293b; border-color:#475569; color:white; }
.acts { display:flex; gap:.3rem; opacity:0; transition:opacity .2s; }
.sec-acts { opacity:0; }
.ch-row:hover .acts,.sec-row:hover .sec-acts { opacity:1; }
.iact { display:flex; align-items:center; justify-content:center; width:32px; height:32px; background:white; border:1px solid rgba(203,213,225,.5); border-radius:.75rem; color:#64748b; cursor:pointer; transition:all .2s; }
.iact:hover { transform:scale(1.08); }
.iact.ed:hover { background:#3b5bdb; border-color:#3b5bdb; color:white; }
.iact.rm:hover { background:#ef4444; border-color:#ef4444; color:white; }
.iact.ok:hover { background:#10b981; border-color:#10b981; color:white; }
.iact.no:hover { background:#f43f5e; border-color:#f43f5e; color:white; }
:global(.dark) .iact { background:#1e293b; border-color:#475569; color:#cbd5e1; }

/* objectives */
.obj-ta { width:100%; background:rgba(255,255,255,.5); border:none; outline:none; padding:1.5rem 1.75rem; font-size:.95rem; line-height:1.7; color:#1e293b; resize:vertical; min-height:220px; border-radius:0 0 1.75rem 1.75rem; box-sizing:border-box; }
:global(.dark) .obj-ta { background:rgba(15,23,42,.6); color:#e2e8f0; }

/* files */
.files-head { display:flex; align-items:center; gap:.75rem; font-size:.95rem; font-weight:700; color:#1e293b; }
:global(.dark) .files-head { color:#f1f5f9; }
.files-count { background:linear-gradient(145deg,#3b5bdb,#2563eb); color:white; font-size:.7rem; font-weight:700; padding:.2rem .6rem; border-radius:9999px; }
.files-body { display:flex; flex-wrap:wrap; gap:.6rem; padding:1.25rem 1.5rem 1.5rem; }
.file-chip { display:inline-flex; align-items:center; gap:.5rem; background:rgba(255,255,255,.8); border:1px solid rgba(203,213,225,.6); padding:.4rem 1rem; border-radius:2rem; font-size:.8rem; font-weight:500; color:#334155; transition:all .2s; }
.file-chip:hover { background:white; border-color:#3b5bdb; transform:translateY(-1px); }
:global(.dark) .file-chip { background:rgba(30,41,59,.7); border-color:#475569; color:#cbd5e1; }

/* actions */
.editor-actions { display:flex; justify-content:flex-end; gap:1rem; padding:1.75rem 2rem .5rem; border-top:1px solid rgba(203,213,225,.4); margin-top:2rem; }
:global(.dark) .editor-actions { border-top-color:rgba(51,65,85,.6); }
.btn-outline { padding:.9rem 2rem; border-radius:1.5rem; border:1.5px solid rgba(203,213,225,.8); background:rgba(255,255,255,.7); color:#1e293b; font-weight:600; cursor:pointer; transition:all .25s; font-family:inherit; }
.btn-outline:hover { background:white; border-color:#3b5bdb; color:#3b5bdb; transform:translateY(-2px); }
:global(.dark) .btn-outline { background:rgba(30,41,59,.7); border-color:#475569; color:#cbd5e1; }
.btn-primary { padding:.9rem 2.5rem; border-radius:1.5rem; border:none; background:linear-gradient(145deg,#3b5bdb,#2563eb); color:white; font-weight:700; display:flex; align-items:center; gap:.7rem; cursor:pointer; box-shadow:0 12px 20px -8px rgba(37,99,235,.4); transition:all .25s; font-family:inherit; }
.btn-primary:hover:not(:disabled) { background:linear-gradient(145deg,#2563eb,#1d4ed8); transform:translateY(-3px); box-shadow:0 18px 25px -10px rgba(37,99,235,.5); }
.btn-primary:disabled { opacity:.6; cursor:default; }

/* ══════════════════════════════
   MODAL
   ══════════════════════════════ */
.modal-overlay {
    position: fixed; top:0; left:0; right:0; bottom:0;
    background: rgba(15,23,42,0.55);
    backdrop-filter: blur(6px);
    display: flex; align-items: center; justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.25s ease-out;
}
.modal-card {
    background: white;
    border-radius: 1.75rem;
    padding: 2.25rem 2rem 2rem;
    max-width: 420px; width: 92%;
    box-shadow: 0 32px 64px -12px rgba(0,0,0,0.22), 0 0 0 1px rgba(0,0,0,0.04);
    position: relative;
    animation: slideUp 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
:global(.dark) .modal-card { background: #1e293b; border: 1px solid rgba(51,65,85,.5); }

.modal-close {
    position: absolute; top: 1.1rem; right: 1.1rem;
    background: #f1f5f9; border: none; cursor: pointer;
    color: #64748b; border-radius: .6rem;
    width: 32px; height: 32px;
    display: flex; align-items: center; justify-content: center;
    transition: all .2s;
}
.modal-close:hover { background: #e2e8f0; color: #1e293b; }
:global(.dark) .modal-close { background: #334155; color: #94a3b8; }
:global(.dark) .modal-close:hover { background: #475569; color: #f1f5f9; }

.code-modal-content {
    display: flex; flex-direction: column; align-items: center; gap: 1.1rem;
    text-align: center;
}

/* success badge */
.code-success-badge { position: relative; width: 78px; height: 78px; margin-bottom: .25rem; }
.code-logo { width: 78px; height: 78px; object-fit: contain; border-radius: 50%; background: #eff6ff; padding: 13px; border: 2px solid #bfdbfe; box-sizing: border-box; }
:global(.dark) .code-logo { background: #0c2340; border-color: #1e3a5f; }
.code-check-badge { position: absolute; bottom: -2px; right: -2px; width: 26px; height: 26px; background: #22c55e; border-radius: 50%; border: 2.5px solid white; display: flex; align-items: center; justify-content: center; color: white; }
:global(.dark) .code-check-badge { border-color: #1e293b; }

.code-modal-title { font-size: 1.35rem; font-weight: 800; color: #0f172a; margin: 0; letter-spacing: -.3px; }
:global(.dark) .code-modal-title { color: #f8fafc; }
.code-modal-subtitle { font-size: .875rem; color: #64748b; margin: 0; line-height: 1.55; max-width: 310px; }
:global(.dark) .code-modal-subtitle { color: #94a3b8; }

/* course title display */
.course-title-display {
    display: flex; align-items: center; gap: .6rem;
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: .875rem; padding: .6rem 1.1rem;
    width: 100%; box-sizing: border-box;
}
:global(.dark) .course-title-display { background: #0f172a; border-color: #334155; }
.course-title-label { font-size: .7rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: .07em; white-space: nowrap; }
.course-title-value { font-size: .9rem; font-weight: 600; color: #1e293b; flex: 1; text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
:global(.dark) .course-title-value { color: #f1f5f9; }

/* code display */
.code-display { width: 100%; }
.code-label { font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #94a3b8; margin: 0 0 .5rem; text-align: left; }
:global(.dark) .code-label { color: #64748b; }
.code-box {
    display: flex; align-items: center; gap: .75rem;
    background: #eff6ff; border: 1.5px solid #bfdbfe;
    border-radius: 1rem; padding: .9rem 1.1rem;
}
:global(.dark) .code-box { background: rgba(59,91,219,.1); border-color: rgba(96,165,250,.25); }
.code-text { flex: 1; font-size: 1.2rem; font-weight: 800; color: #2563eb; letter-spacing: .04em; font-family: 'Courier New', monospace; text-align: left; word-break: break-all; }
:global(.dark) .code-text { color: #60a5fa; }
.copy-btn {
    display: flex; align-items: center; gap: .4rem;
    background: white; border: 1.5px solid #bfdbfe;
    border-radius: .75rem; padding: .5rem .875rem;
    font-size: .8rem; font-weight: 600; color: #2563eb;
    cursor: pointer; transition: all .2s; white-space: nowrap;
    font-family: inherit;
}
.copy-btn:hover { background: #2563eb; color: white; border-color: #2563eb; transform: scale(1.03); }
:global(.dark) .copy-btn { background: #1e293b; border-color: rgba(96,165,250,.3); color: #60a5fa; }

.code-hint { font-size: .8rem; color: #94a3b8; margin: 0; }
:global(.dark) .code-hint { color: #64748b; }

/* primary modal btn */
.btn-primary-modal {
    display: flex; align-items: center; justify-content: center; gap: .5rem;
    padding: .875rem 1.5rem; border-radius: 1rem; border: none;
    background: linear-gradient(145deg, #3b5bdb, #2563eb);
    color: white; font-weight: 700; font-size: .95rem;
    cursor: pointer; width: 100%; transition: all .2s;
    font-family: inherit; box-shadow: 0 8px 16px -6px rgba(37,99,235,.4);
}
.btn-primary-modal:hover { background: linear-gradient(145deg,#2563eb,#1d4ed8); transform: translateY(-2px); box-shadow: 0 12px 20px -8px rgba(37,99,235,.5); }

@keyframes fadeIn { from { opacity:0; } to { opacity:1; } }
@keyframes slideUp { from { transform:translateY(20px); opacity:0; } to { transform:translateY(0); opacity:1; } }

.ai-badge {
    margin: 0 1.75rem 0.75rem;
    display: inline-flex;
    align-items: center;
    font-size: 0.72rem;
    font-weight: 700;
    color: #7c3aed;
    background: #f3e8ff;
    border: 1px solid #e9d5ff;
    border-radius: 9999px;
    padding: 0.2rem 0.65rem;
}
:global(.dark) .ai-badge {
    color: #c4b5fd;
    background: #2e1065;
    border-color: #6d28d9;
}
</style>