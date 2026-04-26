<!--
    Component: CoursePlanEditor.svelte
    Description: Lets the teacher review and edit a generated course plan
    (chapters, sections, learning objectives) before final validation.
-->
<script lang="ts">
    // ========== IMPORTS ==========
    import { getContext } from 'svelte';
    import { goto } from '$app/navigation';
    import { fly } from 'svelte/transition';
    import { cubicOut } from 'svelte/easing';

    // Get internationalization context (i18n)
    const i18n = getContext('i18n');

    // ========== PROPS ==========
    // Course data passed from the previous page (via state)
    export let courseData: {
        title: string;
        language: string;
        category: string;
        level: string;
        objectives: string;
        files: File[];
    };

    // ========== TYPES ==========
    // Section structure (subchapter)
    interface Section {
        id: string;
        title: string;
    }

    // Chapter structure
    interface Chapter {
        id: string;
        title: string;
        sections: Section[];
    }

    // ========== LOCAL STATE ==========
    // Chapter list (mock data for demo, to be replaced by PDF analysis)
    let chapters: Chapter[] = [
        {
            id: 'ch1',
            title: 'Introduction à Java',
            sections: [
                { id: 'sec1-1', title: 'Historique du langage' },
                { id: 'sec1-2', title: 'Installation de l\'environnement' }
            ]
        },
        {
            id: 'ch2',
            title: 'Bases du langage',
            sections: [
                { id: 'sec2-1', title: 'Variables et types' },
                { id: 'sec2-2', title: 'Structures de contrôle' }
            ]
        }
    ];

    // Editable learning objectives (initialized with incoming value)
    let editableObjectives = courseData.objectives;

    // ----- Chapter edit states -----
    let newChapterTitle = '';                         // Title of the new chapter to add
    let editingChapterId: string | null = null;       // ID of the chapter currently being edited
    let editingChapterTitle = '';                     // Temporary title while editing

    // ----- Section edit states -----
    let newSectionTitle = '';                                           // Title of the new section
    let addingSectionForChapterId: string | null = null;                // ID of the chapter receiving a new section
    let editingSection: { chapterId: string; sectionId: string } | null = null;  // Reference to the section being edited
    let editingSectionTitle = '';                                       // Temporary title for the edited section

    // ----- Chapter expand/collapse state -----
    // Set of IDs for currently expanded chapters
    let expandedChapters = new Set(chapters.map(c => c.id));

    // ========== UTILITY FUNCTIONS ==========
    // Generate a unique identifier (uses native crypto API)
    function generateId(): string {
        return crypto.randomUUID();
    }

    // Toggle chapter open/closed state
    function toggleChapter(id: string) {
        if (expandedChapters.has(id)) {
            expandedChapters.delete(id);
        } else {
            expandedChapters.add(id);
        }
        // Recreate the Set to trigger reactivity
        expandedChapters = new Set(expandedChapters);
    }

    // ========== CHAPTER OPERATIONS ==========
    // Add a new chapter
    function addChapter() {
        if (!newChapterTitle.trim()) return;
        const id = generateId();
        chapters = [...chapters, { id, title: newChapterTitle.trim(), sections: [] }];
        // Automatically open the new chapter
        expandedChapters.add(id);
        expandedChapters = new Set(expandedChapters);
        newChapterTitle = '';
    }

    // Start editing an existing chapter
    function startEditChapter(chapter: Chapter) {
        editingChapterId = chapter.id;
        editingChapterTitle = chapter.title;
    }

    // Save edits for the chapter currently being edited
    function saveEditChapter() {
        if (editingChapterId && editingChapterTitle.trim()) {
            chapters = chapters.map(ch =>
                ch.id === editingChapterId ? { ...ch, title: editingChapterTitle.trim() } : ch
            );
        }
        editingChapterId = null;
        editingChapterTitle = '';
    }

    // Cancel chapter editing
    function cancelEditChapter() {
        editingChapterId = null;
        editingChapterTitle = '';
    }

    // Delete a chapter (and its sections)
    function deleteChapter(id: string) {
        chapters = chapters.filter(ch => ch.id !== id);
        // Also remove it from the expanded chapter list
        expandedChapters.delete(id);
        expandedChapters = new Set(expandedChapters);
    }

    // ========== SECTION OPERATIONS ==========
    // Start adding a section to a given chapter
    function startAddSection(chapterId: string) {
        addingSectionForChapterId = chapterId;
        newSectionTitle = '';
        // Ensure the chapter is open
        if (!expandedChapters.has(chapterId)) {
            expandedChapters.add(chapterId);
            expandedChapters = new Set(expandedChapters);
        }
    }

    // Actually add the section
    function addSection(chapterId: string) {
        if (!newSectionTitle.trim()) return;
        chapters = chapters.map(ch => {
            if (ch.id === chapterId) {
                return {
                    ...ch,
                    sections: [...ch.sections, { id: generateId(), title: newSectionTitle.trim() }]
                };
            }
            return ch;
        });
        addingSectionForChapterId = null;
        newSectionTitle = '';
    }

    // Cancel section addition
    function cancelAddSection() {
        addingSectionForChapterId = null;
        newSectionTitle = '';
    }

    // Start editing an existing section
    function startEditSection(chapterId: string, section: Section) {
        editingSection = { chapterId, sectionId: section.id };
        editingSectionTitle = section.title;
    }

    // Save section edits
    function saveEditSection() {
        if (editingSection && editingSectionTitle.trim()) {
            const { chapterId, sectionId } = editingSection;
            chapters = chapters.map(ch => {
                if (ch.id === chapterId) {
                    return {
                        ...ch,
                        sections: ch.sections.map(sec =>
                            sec.id === sectionId ? { ...sec, title: editingSectionTitle.trim() } : sec
                        )
                    };
                }
                return ch;
            });
        }
        editingSection = null;
        editingSectionTitle = '';
    }

    // Cancel section editing
    function cancelEditSection() {
        editingSection = null;
        editingSectionTitle = '';
    }

    // Delete a section
    function deleteSection(chapterId: string, sectionId: string) {
        chapters = chapters.map(ch => {
            if (ch.id === chapterId) {
                return {
                    ...ch,
                    sections: ch.sections.filter(sec => sec.id !== sectionId)
                };
            }
            return ch;
        });
    }

    // ========== FINAL VALIDATION ==========
    function validateCourse() {
        // Build final payload to send to backend
        const finalPlan = {
            title: courseData.title,
            language: courseData.language,
            category: courseData.category,
            level: courseData.level,
            objectives: editableObjectives,
            chapters: chapters,
            files: courseData.files
        };
        
        console.log('Plan validé:', finalPlan);
        alert($i18n.t('Cours validé avec succès !'));
        // Return to course list
        goto('/teacher/courses');
    }

    // ========== REACTIVE VALUES ==========
    // Total section count (across all chapters)
    $: totalSections = chapters.reduce((acc, ch) => acc + ch.sections.length, 0);
</script>

<!-- ==================== TEMPLATE (USER INTERFACE) ==================== -->
<div class="plan-editor">
    <!-- Hero header with title and stats -->
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
                <span class="hstat-n">{courseData.files.length}</span>
                <span class="hstat-l">{$i18n.t('Fichiers')}</span>
            </div>
        </div>
    </div>

    <!-- Main two-column grid -->
    <div class="editor-main">
        <!-- LEFT COLUMN: Course structure (chapters and sections) -->
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

            <!-- Chapter list -->
            <div class="ch-list">
                {#each chapters as ch, idx (ch.id)}
                    <div class="ch-block" in:fly={{ y: 12, duration: 250, easing: cubicOut }}>
                        <!-- Chapter header -->
                        <div class="ch-row" class:open={expandedChapters.has(ch.id)}>
                            <button class="ch-toggle" on:click={() => toggleChapter(ch.id)}>
                                <span class="ch-num">{String(idx+1).padStart(2,'0')}</span>
                                <svg class="ch-arr" class:rotated={expandedChapters.has(ch.id)}
                                    viewBox="0 0 24 24" fill="none" stroke="currentColor" width="13" height="13">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 18l6-6-6-6"/>
                                </svg>
                            </button>

                            <!-- Edit mode or normal display -->
                            {#if editingChapterId === ch.id}
                                <!-- Chapter title edit form -->
                                <div class="iedit">
                                    <input type="text" bind:value={editingChapterTitle} class="ifield"
                                        on:keydown={(e)=>{ if(e.key==='Enter') saveEditChapter(); if(e.key==='Escape') cancelEditChapter(); }}/>
                                    <button class="iact ok" on:click={saveEditChapter}>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="13" height="13"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
                                    </button>
                                    <button class="iact no" on:click={cancelEditChapter}>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="13" height="13"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/></svg>
                                    </button>
                                </div>
                            {:else}
                                <!-- Normal chapter title display -->
                                <span class="ch-name">{ch.title}</span>
                                <!-- Action buttons (always visible) -->
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

                        <!-- Section list (shown when chapter is expanded) -->
                        {#if expandedChapters.has(ch.id)}
                            <div class="sec-list" transition:fly={{ y: -6, duration: 200, easing: cubicOut }}>
                                {#each ch.sections as sec (sec.id)}
                                    <div class="sec-row" in:fly={{ x: -6, duration: 200 }}>
                                        <span class="sec-dot"></span>
                                        <!-- Edit mode or normal display for section -->
                                        {#if editingSection?.chapterId === ch.id && editingSection?.sectionId === sec.id}
                                            <div class="iedit">
                                                <input type="text" bind:value={editingSectionTitle} class="ifield sm"
                                                    on:keydown={(e)=>{ if(e.key==='Enter') saveEditSection(); if(e.key==='Escape') cancelEditSection(); }}/>
                                                <button class="iact ok" on:click={saveEditSection}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg></button>
                                                <button class="iact no" on:click={cancelEditSection}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/></svg></button>
                                            </div>
                                        {:else}
                                            <span class="sec-name">{sec.title}</span>
                                            <!-- Section action buttons (always visible) -->
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

                                <!-- UI for adding a new section -->
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
                                    <!-- Button to show add-section form -->
                                    <button class="add-sec-btn" on:click={() => startAddSection(ch.id)}>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/></svg>
                                        {$i18n.t('Ajouter une section')}
                                    </button>
                                {/if}
                            </div>
                        {/if}
                    </div>
                {/each}

                <!-- Form for adding a new chapter -->
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

        <!-- RIGHT COLUMN: Learning objectives and source files -->
        <div class="right-col">
            <!-- Objectives card -->
            <div class="card">
                <div class="card-head">
                    <div class="card-icon green-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                    </div>
                    <div>
                        <div class="card-title">{$i18n.t('Objectifs pédagogiques')}</div>
                        <div class="card-sub">{$i18n.t('Ce que les étudiants apprendront')}</div>
                    </div>
                </div>
                <textarea bind:value={editableObjectives} class="obj-ta" rows="11"
                    placeholder={$i18n.t("À la fin de ce cours, l'étudiant sera capable de...")}></textarea>
            </div>

            <!-- Source files card -->
            <div class="card">
                <div class="card-head small-head">
                    <div class="card-icon gray-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
                        </svg>
                    </div>
                    <div class="files-head">
                        {$i18n.t('Fichiers sources')}
                        <span class="files-count">{courseData.files.length}</span>
                    </div>
                </div>
                <div class="files-body">
                    {#each courseData.files as file}
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

    <!-- Bottom action bar (Validate / Back) -->
    <div class="editor-actions">
        <button class="btn-outline" on:click={() => history.back()}>
            {$i18n.t('Retour')}
        </button>
        <button class="btn-primary" on:click={validateCourse}>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="18" height="18">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            {$i18n.t('Valider le cours')}
        </button>
    </div>
</div>

<!-- ==================== STYLES ==================== -->
<style>
    /* Import modern Plus Jakarta Sans font */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* Main container */
    .plan-editor {
        font-family: 'Plus Jakarta Sans', sans-serif;
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 0 1.5rem 0;
        color: #1e293b;
        background: #f3f5fb;
        min-height: 100vh;
    }
    :global(.dark) .plan-editor {
        color: #e2e8f0;
        background: #0f172a;
    }

    /* ========== HERO SECTION ========== */
    .hero {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 1.5rem;
        padding: 2rem 1.75rem 1.875rem;
        background: linear-gradient(135deg, #ffffff 0%, #eef1ff 100%);
        border-bottom: 1px solid #e0e4f5;
        margin-bottom: 2rem;
        border-radius: 0.5rem;
         
    }
    :global(.dark) .hero {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-bottom: 1px solid #334155;
    }
    .hero-content { flex: 1; }
    .hero-eyebrow {
        font-size: 0.68rem; font-weight: 700; letter-spacing: 0.14em;
        text-transform: uppercase; color: #3b5bdb; margin-bottom: 0.5rem;
    }
    :global(.dark) .hero-eyebrow { color: #818cf8; }
    .hero-title {
        font-size: clamp(1.5rem, 3vw, 2.25rem); font-weight: 800;
        color: #111428; margin: 0 0 0.875rem; letter-spacing: -0.025em; line-height: 1.15;
    }
    :global(.dark) .hero-title { color: #f8fafc; }
    .hero-tags { display: flex; gap: 0.45rem; flex-wrap: wrap; }
    .htag {
        font-size: 0.72rem; font-weight: 600; padding: 0.25rem 0.75rem; border-radius: 9999px;
    }
    .htag-blue { background: #dbe4ff; color: #3b5bdb; }
    :global(.dark) .htag-blue { background: #1e3a8a; color: #bfdbfe; }
    .htag-green { background: #d3f9d8; color: #2f9e44; }
    :global(.dark) .htag-green { background: #14532d; color: #bbf7d0; }
    .htag-amber { background: #fff3bf; color: #e67700; }
    :global(.dark) .htag-amber { background: #78350f; color: #fde68a; }

    .hero-stats {
        display: flex; align-items: center; gap: 1.75rem;
        background: white; border: 1px solid #e5e8f4; border-radius: 1rem;
        padding: 1.125rem 1.75rem; box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    }
    :global(.dark) .hero-stats { background: #1e293b; border-color: #334155; box-shadow: 0 1px 6px rgba(0,0,0,0.3); }
    .hstat { display: flex; flex-direction: column; align-items: center; gap: 0.15rem; }
    .hstat-n { font-size: 1.75rem; font-weight: 800; color: #1a1d2e; line-height: 1; }
    :global(.dark) .hstat-n { color: #f1f5f9; }
    .hstat-l { font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #a0a8c3; }
    :global(.dark) .hstat-l { color: #94a3b8; }
    .hstat-sep { width: 1px; height: 36px; background: #eaecf5; }
    :global(.dark) .hstat-sep { background: #475569; }

    /* ========== LAYOUT ========== */
    .editor-main {
        display: grid;
        grid-template-columns: 1.5fr 1fr;
        gap: 1.75rem;
        margin-bottom: 2.5rem;
        padding: 0 2rem;
    }
    .right-col { display: flex; flex-direction: column; gap: 1.75rem; }
    @media (max-width: 900px) {
        .editor-main { grid-template-columns: 1fr; padding: 0 1rem; }
        .hero { padding: 1.5rem 1rem; }
        .hero-stats { width: 100%; justify-content: space-around; }
    }
    /* ========== CARDS (Design Verre / Glassmorphism) ========== */
    .card {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 1rem;
        overflow: hidden;
        box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.02) inset;
       /* transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);*/
    }
    .card:hover {
        background: rgba(255, 255, 255, 0.85);
        box-shadow: 0 30px 50px -15px rgba(59, 91, 219, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.6) inset;
        /*transform: translateY(-3px);*/
    }
    :global(.dark) .card {
        background: rgba(30, 41, 59, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.4);
    }
    :global(.dark) .card:hover {
        background: rgba(30, 41, 59, 0.9);
        box-shadow: 0 30px 50px -15px rgba(96, 165, 250, 0.2);
    }

    /* Card header */
    .card-head {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.5rem 1.75rem;
        border-bottom: 1px solid rgba(203, 213, 225, 0.3);
        background: transparent;
    }
    .small-head {
        padding: 1.25rem 1.5rem;
    }
    :global(.dark) .card-head {
        border-bottom-color: rgba(51, 65, 85, 0.6);
    }

    /* Modern gradient icons */
    .card-icon {
        width: 42px;
        height: 42px;
        border-radius: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
        box-shadow: 0 6px 10px -4px rgba(0, 0, 0, 0.1);
    }
    .blue-icon {
        background: linear-gradient(145deg, #3b5bdb, #2563eb);
        color: white;
        box-shadow: 0 8px 15px -5px rgba(59, 91, 219, 0.4);
    }
    .green-icon {
        background: linear-gradient(145deg, #2b8c4a, #16a34a);
        color: white;
        box-shadow: 0 8px 15px -5px rgba(43, 140, 74, 0.4);
    }
    .gray-icon {
        background: linear-gradient(145deg, #94a3b8, #64748b);
        color: white;
        width: 34px;
        height: 34px;
        border-radius: 0.8rem;
        box-shadow: 0 6px 10px -4px rgba(100, 116, 139, 0.3);
    }
    :global(.dark) .blue-icon {
        background: linear-gradient(145deg, #4f6edb, #3b5bdb);
    }
    :global(.dark) .green-icon {
        background: linear-gradient(145deg, #3a9e5a, #2b8c4a);
    }
    :global(.dark) .gray-icon {
        background: linear-gradient(145deg, #64748b, #475569);
    }

    .card-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.01em;
    }
    .card-sub {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 0.2rem;
        font-weight: 500;
    }
    :global(.dark) .card-title {
        color: #f8fafc;
    }
    :global(.dark) .card-sub {
        color: #94a3b8;
    }

    /* ========== CHAPTER LIST (new clean style) ========== */
    .ch-list {
        padding: 0.5rem 0 0;
    }

    .ch-block {
        border-bottom: 1px solid rgba(225, 203, 217, 0.2);
    }
    .ch-block:last-child {
        border-bottom: none;
    }
    :global(.dark) .ch-block {
        border-bottom-color: rgba(51, 65, 85, 0.5);
    }

    .ch-row {
        display: flex;
        align-items: center;
        gap: 0.875rem;
        padding: 0.875rem 1.75rem;
        transition: background 0.2s ease, padding-left 0.2s ease;
        border-radius: 0;
    }
    .ch-row:hover,
    .ch-row.open {
        background: rgba(59, 91, 219, 0.04);
        padding-left: 2rem;
    }
    :global(.dark) .ch-row:hover,
    :global(.dark) .ch-row.open {
        background: rgba(96, 165, 250, 0.08);
    }

    .ch-toggle {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        background: none;
        border: none;
        cursor: pointer;
        padding: 0;
        flex-shrink: 0;
    }
    .ch-num {
        font-size: 0.75rem;
        font-weight: 800;
        color: #3b5bdb;
        background: rgba(59, 91, 219, 0.1);
        padding: 0.2rem 0.4rem;
        border-radius: 0.5rem;
        letter-spacing: -0.02em;
        min-width: 28px;
        text-align: center;
    }
    :global(.dark) .ch-num {
        color: #93c5fd;
        background: rgba(96, 165, 250, 0.15);
    }
    .ch-arr {
        color: #64748b;
        transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
        width: 16px;
        height: 16px;
    }
    .ch-arr.rotated {
        transform: rotate(90deg);
    }
    .ch-name {
        flex: 1;
        font-size: 0.95rem;
        font-weight: 600;
        color: #1e293b;
    }
    :global(.dark) .ch-name {
        color: #e2e8f0;
    }

    /* Enhanced sections */
    .sec-list {
        margin-left: 3.75rem;
        border-left: 2px solid rgba(59, 91, 219, 0.2);
        padding: 0.35rem 0 0.875rem;
    }
    :global(.dark) .sec-list {
        border-left-color: rgba(96, 165, 250, 0.3);
    }

    .sec-row {
        display: flex;
        align-items: center;
        gap: 0.875rem;
        padding: 0.5rem 1.25rem 0.5rem 1.25rem;
        border-radius: 0.75rem;
        margin: 0.1rem 0.5rem;
        transition: all 0.2s ease;
    }
    .sec-row:hover {
        background: rgba(59, 91, 219, 0.05);
        padding-left: 1.5rem;
    }
    :global(.dark) .sec-row:hover {
        background: rgba(96, 165, 250, 0.08);
    }
    .sec-dot {
        width: 7px;
        height: 7px;
        border-radius: 2px;
        flex-shrink: 0;
        background: #3b5bdb;
        transform: rotate(45deg);
        opacity: 0.7;
    }
    .accent-dot {
        background: #10b981;
        opacity: 1;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
    }
    .sec-name {
        flex: 1;
        font-size: 0.875rem;
        color: #475569;
        font-weight: 500;
    }
    :global(.dark) .sec-name {
        color: #cbd5e1;
    }

    /* Add section button */
    .add-sec-btn {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        background: none;
        border: 1.5px dashed rgba(59, 91, 219, 0.4);
        border-radius: 1rem;
        cursor: pointer;
        font-size: 0.8rem;
        font-weight: 600;
        color: #3b5bdb;
        padding: 0.6rem 1.2rem;
        margin-left: 0.5rem;
        width: calc(100% - 1rem);
        transition: all 0.2s ease;
        justify-content: center;
    }
    .add-sec-btn:hover {
        background: rgba(59, 91, 219, 0.05);
        border-color: #3b5bdb;
        color: #1d4ed8;
    }
    :global(.dark) .add-sec-btn {
        border-color: rgba(96, 165, 250, 0.4);
        color: #90aef8;
    }
    :global(.dark) .add-sec-btn:hover {
        background: rgba(96, 165, 250, 0.1);
        border-color: #60a5fa;
        color: #bfdbfe;
    }

    /* Add chapter form */
    .add-ch-row {
        display: flex;
        gap: 0.875rem;
        padding: 1.25rem 1.75rem;
        border-top: 1px solid rgba(203, 213, 225, 0.3);
        background: rgba(248, 250, 252, 0.5);
        backdrop-filter: blur(8px);
    }
    :global(.dark) .add-ch-row {
        background: rgba(15, 23, 42, 0.6);
        border-top-color: rgba(51, 65, 85, 0.6);
    }

    .add-ch-input {
        flex: 1;
        background: rgba(255, 255, 255, 0.9);
        border: 1.5px solid rgba(203, 213, 225, 0.8);
        border-radius: 1rem;
        padding: 0.7rem 1rem;
        font-size: 0.9rem;
        color: #1e293b;
        backdrop-filter: blur(4px);
        transition: all 0.2s ease;
    }
    .add-ch-input:focus {
        border-color: #3b5bdb;
        box-shadow: 0 0 0 4px rgba(59, 91, 219, 0.15);
        outline: none;
        background: white;
    }
    :global(.dark) .add-ch-input {
        background: rgba(15, 23, 42, 0.8);
        border-color: #475569;
        color: white;
    }
    :global(.dark) .add-ch-input:focus {
        border-color: #60a5fa;
        box-shadow: 0 0 0 4px rgba(96, 165, 250, 0.2);
        background: #0f172a;
    }

    .add-ch-btn {
        background: linear-gradient(145deg, #3b5bdb, #2563eb);
        border: none;
        border-radius: 1rem;
        padding: 0.7rem 1.5rem;
        font-size: 0.9rem;
        font-weight: 700;
        color: white;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        white-space: nowrap;
        box-shadow: 0 10px 18px -8px rgba(37, 99, 235, 0.4);
        transition: all 0.2s ease;
    }
    .add-ch-btn:hover {
        background: linear-gradient(145deg, #2563eb, #1d4ed8);
        transform: translateY(-2px);
        box-shadow: 0 14px 22px -10px rgba(37, 99, 235, 0.5);
    }

    /* ========== INLINE EDIT (enhanced) ========== */
    .iedit {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex: 1;
    }
    .ifield {
        flex: 1;
        background: white;
        border: 1.5px solid #cbd5e1;
        border-radius: 0.75rem;
        padding: 0.5rem 0.8rem;
        font-size: 0.9rem;
        color: #1e293b;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        transition: border 0.15s, box-shadow 0.15s;
    }
    .ifield:focus {
        border-color: #3b5bdb;
        box-shadow: 0 0 0 3px rgba(59, 91, 219, 0.1);
        outline: none;
    }
    .ifield.sm {
        font-size: 0.85rem;
        padding: 0.45rem 0.7rem;
    }
    :global(.dark) .ifield {
        background: #1e293b;
        border-color: #475569;
        color: white;
    }

    /* Action buttons (hidden by default, shown on hover) */
    .acts {
        display: flex;
        gap: 0.3rem;
        opacity: 0;
        transition: opacity 0.2s ease;
    }
    .sec-acts {
        opacity: 0;
    }
    .ch-row:hover .acts,
    .sec-row:hover .sec-acts {
        opacity: 1;
    }

    .iact {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        background: white;
        border: 1px solid rgba(203, 213, 225, 0.5);
        border-radius: 0.75rem;
        color: #64748b;
        cursor: pointer;
        backdrop-filter: blur(4px);
        transition: all 0.2s cubic-bezier(0.23, 1, 0.32, 1);
        box-shadow: 0 4px 6px -2px rgba(0,0,0,0.05);
    }
    .iact:hover {
        transform: scale(1.08);
    }
    .iact.ed:hover {
        background: #3b5bdb;
        border-color: #3b5bdb;
        color: white;
        box-shadow: 0 8px 12px -4px rgba(59, 91, 219, 0.4);
    }
    .iact.rm:hover {
        background: #ef4444;
        border-color: #ef4444;
        color: white;
        box-shadow: 0 8px 12px -4px rgba(239, 68, 68, 0.4);
    }
    .iact.ok:hover {
        background: #10b981;
        border-color: #10b981;
        color: white;
        box-shadow: 0 8px 12px -4px rgba(16, 185, 129, 0.3);
    }
    .iact.no:hover {
        background: #f43f5e;
        border-color: #f43f5e;
        color: white;
    }
    :global(.dark) .iact {
        background: #1e293b;
        border-color: #475569;
        color: #cbd5e1;
    }
    :global(.dark) .iact.ed:hover {
        background: #2563eb;
        border-color: #2563eb;
        color: white;
    }
    :global(.dark) .iact.rm:hover {
        background: #dc2626;
        border-color: #dc2626;
        color: white;
    }

    /* ========== OBJECTIVES & FILES (modernized) ========== */
    .obj-ta {
        width: 100%;
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(4px);
        border: none;
        outline: none;
        padding: 1.5rem 1.75rem;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #1e293b;
        resize: vertical;
        min-height: 220px;
        border-radius: 0 0 1.75rem 1.75rem;
    }
    :global(.dark) .obj-ta {
        background: rgba(15, 23, 42, 0.6);
        color: #e2e8f0;
    }

    .files-head {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-size: 0.95rem;
        font-weight: 700;
        color: #1e293b;
    }
    :global(.dark) .files-head {
        color: #f1f5f9;
    }
    .files-count {
        background: linear-gradient(145deg, #3b5bdb, #2563eb);
        color: white;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        box-shadow: 0 4px 6px -2px rgba(59, 91, 219, 0.3);
    }

    .files-body {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        padding: 1.25rem 1.5rem 1.5rem;
    }
    .file-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(203, 213, 225, 0.6);
        padding: 0.4rem 1rem;
        border-radius: 2rem;
        font-size: 0.8rem;
        font-weight: 500;
        color: #334155;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        transition: all 0.2s ease;
    }
    .file-chip:hover {
        background: white;
        border-color: #3b5bdb;
        transform: translateY(-1px);
        box-shadow: 0 6px 10px -4px rgba(59, 91, 219, 0.15);
    }
    :global(.dark) .file-chip {
        background: rgba(30, 41, 59, 0.7);
        border-color: #475569;
        color: #cbd5e1;
    }
    :global(.dark) .file-chip:hover {
        background: #1e293b;
        border-color: #60a5fa;
    }

    /* ========== ACTIONS (bottom bar) ========== */
    .editor-actions {
        display: flex;
        justify-content: flex-end;
        gap: 1.5rem;
        padding: 1.75rem 2rem 0.5rem;
        border-top: 1px solid rgba(203, 213, 225, 0.4);
        margin-top: 2rem;
    }
    :global(.dark) .editor-actions {
        border-top-color: rgba(51, 65, 85, 0.6);
    }

    .btn-outline {
        padding: 0.9rem 2rem;
        border-radius: 1.5rem;
        border: 1.5px solid rgba(203, 213, 225, 0.8);
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(8px);
        color: #1e293b;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.25s ease;
        box-shadow: 0 4px 8px -2px rgba(0,0,0,0.05);
    }
    .btn-outline:hover {
        background: white;
        border-color: #3b5bdb;
        color: #3b5bdb;
        transform: translateY(-2px);
        box-shadow: 0 12px 18px -8px rgba(59, 91, 219, 0.2);
    }
    :global(.dark) .btn-outline {
        background: rgba(30, 41, 59, 0.7);
        border-color: #475569;
        color: #cbd5e1;
    }
    :global(.dark) .btn-outline:hover {
        background: #1e293b;
        border-color: #60a5fa;
        color: #bfdbfe;
    }

    .btn-primary {
        padding: 0.9rem 2.5rem;
        border-radius: 1.5rem;
        border: none;
        background: linear-gradient(145deg, #3b5bdb, #2563eb);
        color: white;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 0.7rem;
        cursor: pointer;
        box-shadow: 0 12px 20px -8px rgba(37, 99, 235, 0.4);
        transition: all 0.25s cubic-bezier(0.23, 1, 0.32, 1);
    }
    .btn-primary:hover {
        background: linear-gradient(145deg, #2563eb, #1d4ed8);
        transform: translateY(-3px);
        box-shadow: 0 18px 25px -10px rgba(37, 99, 235, 0.5);
    }
</style>