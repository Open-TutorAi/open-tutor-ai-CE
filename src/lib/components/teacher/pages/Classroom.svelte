<script lang="ts">
    import { getContext } from 'svelte';
    import { goto } from '$app/navigation';
    import { fly } from 'svelte/transition';
    
    const i18n = getContext('i18n');

    export let courseData: {
        title: string;
        language: string;
        category: string;
        level: string;
        objectives: string;
        files: File[];
    };

    // ---------- نموذج بيانات الفصول ----------
    interface Section {
        id: string;
        title: string;
    }

    interface Chapter {
        id: string;
        title: string;
        sections: Section[];
    }

    // بيانات وهمية (ستستبدل لاحقاً)
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

    let editableObjectives = courseData.objectives;

    // حالات الإضافة والتعديل
    let newChapterTitle = '';
    let editingChapterId: string | null = null;
    let editingChapterTitle = '';

    let newSectionTitle = '';
    let addingSectionForChapterId: string | null = null;
    let editingSection: { chapterId: string; sectionId: string } | null = null;
    let editingSectionTitle = '';

    function generateId(): string {
        return crypto.randomUUID();
    }

    // ---------- عمليات الفصول ----------
    function addChapter() {
        if (!newChapterTitle.trim()) return;
        chapters = [...chapters, {
            id: generateId(),
            title: newChapterTitle.trim(),
            sections: []
        }];
        newChapterTitle = '';
    }

    function startEditChapter(chapter: Chapter) {
        editingChapterId = chapter.id;
        editingChapterTitle = chapter.title;
    }

    function saveEditChapter() {
        if (editingChapterId && editingChapterTitle.trim()) {
            chapters = chapters.map(ch => 
                ch.id === editingChapterId ? { ...ch, title: editingChapterTitle.trim() } : ch
            );
        }
        editingChapterId = null;
        editingChapterTitle = '';
    }

    function cancelEditChapter() {
        editingChapterId = null;
        editingChapterTitle = '';
    }

    function deleteChapter(id: string) {
        chapters = chapters.filter(ch => ch.id !== id);
    }

    // ---------- عمليات الأقسام ----------
    function startAddSection(chapterId: string) {
        addingSectionForChapterId = chapterId;
        newSectionTitle = '';
    }

    function addSection(chapterId: string) {
        if (!newSectionTitle.trim()) return;
        chapters = chapters.map(ch => {
            if (ch.id === chapterId) {
                return {
                    ...ch,
                    sections: [...ch.sections, {
                        id: generateId(),
                        title: newSectionTitle.trim()
                    }]
                };
            }
            return ch;
        });
        addingSectionForChapterId = null;
        newSectionTitle = '';
    }

    function cancelAddSection() {
        addingSectionForChapterId = null;
        newSectionTitle = '';
    }

    function startEditSection(chapterId: string, section: Section) {
        editingSection = { chapterId, sectionId: section.id };
        editingSectionTitle = section.title;
    }

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

    function cancelEditSection() {
        editingSection = null;
        editingSectionTitle = '';
    }

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

    // ---------- التحقق النهائي ----------
    function validateCourse() {
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
        goto('/teacher/courses');
    }

    $: totalSections = chapters.reduce((a, c) => a + c.sections.length, 0);
</script>

<div class="plan-editor">
    <!-- Hero Section (بدل editor-header القديم) -->
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

    <!-- المحتوى الرئيسي (عمودين) -->
    <div class="editor-main">
        <!-- العمود الأيسر: الفصول والأقسام -->
        <div class="plan-section">
            <div class="section-header">
                <h2 class="section-title">
                    <svg class="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    {$i18n.t('Structure du cours')}
                </h2>
                <p class="section-hint">{$i18n.t('Ajoutez, modifiez ou supprimez des chapitres et sections')}</p>
            </div>

            <div class="chapters-list">
                {#each chapters as chapter (chapter.id)}
                    <div class="chapter-item" in:fly={{ y: 10, duration: 200 }}>
                        <div class="chapter-header">
                            {#if editingChapterId === chapter.id}
                                <div class="edit-form">
                                    <input
                                        type="text"
                                        bind:value={editingChapterTitle}
                                        class="edit-input"
                                        placeholder={$i18n.t('Titre du chapitre')}
                                    />
                                    <div class="edit-actions">
                                        <button class="btn-icon save" on:click={saveEditChapter}>✓</button>
                                        <button class="btn-icon cancel" on:click={cancelEditChapter}>✕</button>
                                    </div>
                                </div>
                            {:else}
                                <div class="chapter-title-wrap">
                                    <span class="chapter-title">{chapter.title}</span>
                                </div>
                                <div class="chapter-actions">
                                    <button class="btn-icon edit" on:click={() => startEditChapter(chapter)} title={$i18n.t('Modifier')}>
                                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="16" height="16">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                        </svg>
                                    </button>
                                    <button class="btn-icon delete" on:click={() => deleteChapter(chapter.id)} title={$i18n.t('Supprimer')}>
                                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="16" height="16">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        </svg>
                                    </button>
                                </div>
                            {/if}
                        </div>

                        <!-- الأقسام -->
                        <div class="sections-list">
                            {#each chapter.sections as section (section.id)}
                                <div class="section-item" in:fly={{ y: 10, duration: 200 }}>
                                    {#if editingSection?.chapterId === chapter.id && editingSection?.sectionId === section.id}
                                        <div class="edit-form inline">
                                            <input
                                                type="text"
                                                bind:value={editingSectionTitle}
                                                class="edit-input"
                                                placeholder={$i18n.t('Titre de la section')}
                                            />
                                            <div class="edit-actions">
                                                <button class="btn-icon save" on:click={saveEditSection}>✓</button>
                                                <button class="btn-icon cancel" on:click={cancelEditSection}>✕</button>
                                            </div>
                                        </div>
                                    {:else}
                                        <span class="section-title">{section.title}</span>
                                        <div class="section-actions">
                                            <button class="btn-icon edit" on:click={() => startEditSection(chapter.id, section)} title={$i18n.t('Modifier')}>
                                                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="14" height="14">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                                </svg>
                                            </button>
                                            <button class="btn-icon delete" on:click={() => deleteSection(chapter.id, section.id)} title={$i18n.t('Supprimer')}>
                                                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="14" height="14">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                        </div>
                                    {/if}
                                </div>
                            {/each}

                            <!-- إضافة قسم جديد -->
                            {#if addingSectionForChapterId === chapter.id}
                                <div class="add-section-form">
                                    <input
                                        type="text"
                                        bind:value={newSectionTitle}
                                        class="add-input"
                                        placeholder={$i18n.t('Titre de la section')}
                                        on:keydown={(e) => e.key === 'Enter' && addSection(chapter.id)}
                                    />
                                    <div class="form-actions">
                                        <button class="btn-icon save" on:click={() => addSection(chapter.id)}>✓</button>
                                        <button class="btn-icon cancel" on:click={cancelAddSection}>✕</button>
                                    </div>
                                </div>
                            {:else}
                                <button class="add-section-btn" on:click={() => startAddSection(chapter.id)}>
                                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="16" height="16">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                                    </svg>
                                    {$i18n.t('Ajouter une section')}
                                </button>
                            {/if}
                        </div>
                    </div>
                {/each}

                <!-- إضافة فصل جديد -->
                <div class="add-chapter-form">
                    <input
                        type="text"
                        bind:value={newChapterTitle}
                        class="add-input"
                        placeholder={$i18n.t('Titre du chapitre')}
                        on:keydown={(e) => e.key === 'Enter' && addChapter()}
                    />
                    <button class="btn-add" on:click={addChapter}>
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="16" height="16">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                        </svg>
                        {$i18n.t('Ajouter un chapitre')}
                    </button>
                </div>
            </div>
        </div>

        <!-- العمود الأيمن: الأهداف -->
        <div class="objectives-section">
            <div class="section-header">
                <h2 class="section-title">
                    <svg class="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    {$i18n.t('Objectifs pédagogiques')}
                </h2>
                <p class="section-hint">{$i18n.t('Décrivez ce que les étudiants apprendront')}</p>
            </div>

            <textarea
                bind:value={editableObjectives}
                class="objectives-textarea"
                rows="12"
                placeholder={$i18n.t('Exemple : À la fin de ce cours, l\'étudiant sera capable de...')}
            ></textarea>

            <!-- الملفات المرفقة -->
            <div class="files-summary">
                <h3 class="files-title">{$i18n.t('Fichiers sources')}</h3>
                <div class="files-list">
                    {#each courseData.files as file}
                        <div class="file-tag">
                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="16" height="16">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <span>{file.name}</span>
                        </div>
                    {/each}
                </div>
            </div>
        </div>
    </div>

    <!-- شريط الأزرار السفلي -->
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

<style>
    /* ========== FONTS ========== */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

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

    .hero-content {
        flex: 1;
    }

    .hero-eyebrow {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #3b5bdb;
        margin-bottom: 0.5rem;
    }
    :global(.dark) .hero-eyebrow {
        color: #818cf8;
    }

    .hero-title {
        font-size: clamp(1.5rem, 3vw, 2.25rem);
        font-weight: 800;
        color: #111428;
        margin: 0 0 0.875rem;
        letter-spacing: -0.025em;
        line-height: 1.15;
    }
    :global(.dark) .hero-title {
        color: #f8fafc;
    }

    .hero-tags {
        display: flex;
        gap: 0.45rem;
        flex-wrap: wrap;
    }

    .htag {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
    }

    .htag-blue {
        background: #dbe4ff;
        color: #3b5bdb;
    }
    :global(.dark) .htag-blue {
        background: #1e3a8a;
        color: #bfdbfe;
    }

    .htag-green {
        background: #d3f9d8;
        color: #2f9e44;
    }
    :global(.dark) .htag-green {
        background: #14532d;
        color: #bbf7d0;
    }

    .htag-amber {
        background: #fff3bf;
        color: #e67700;
    }
    :global(.dark) .htag-amber {
        background: #78350f;
        color: #fde68a;
    }

    .hero-stats {
        display: flex;
        align-items: center;
        gap: 1.75rem;
        background: white;
        border: 1px solid #e5e8f4;
        border-radius: 1rem;
        padding: 1.125rem 1.75rem;
        box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    }
    :global(.dark) .hero-stats {
        background: #1e293b;
        border-color: #334155;
        box-shadow: 0 1px 6px rgba(0,0,0,0.3);
    }

    .hstat {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.15rem;
    }

    .hstat-n {
        font-size: 1.75rem;
        font-weight: 800;
        color: #1a1d2e;
        line-height: 1;
    }
    :global(.dark) .hstat-n {
        color: #f1f5f9;
    }

    .hstat-l {
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #a0a8c3;
    }
    :global(.dark) .hstat-l {
        color: #94a3b8;
    }

    .hstat-sep {
        width: 1px;
        height: 36px;
        background: #eaecf5;
    }
    :global(.dark) .hstat-sep {
        background: #475569;
    }

    /* ========== LAYOUT ========== */
    .editor-main {
        display: grid;
        grid-template-columns: 1.5fr 1fr;
        gap: 1.5rem;
        margin-bottom: 2rem;
        padding: 0 1.75rem;
    }
    @media (max-width: 900px) {
        .editor-main {
            grid-template-columns: 1fr;
            padding: 0 1rem;
        }
        .hero {
            padding: 1.5rem 1rem;
        }
        .hero-stats {
            width: 100%;
            justify-content: space-around;
        }
    }

    /* ========== CARDS ========== */
    .plan-section, .objectives-section {
        background: white;
        border-radius: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        padding: 1.5rem;
    }
    :global(.dark) .plan-section,
    :global(.dark) .objectives-section {
        background: #1e293b;
        border-color: #334155;
    }

    .section-header {
        margin-bottom: 1.5rem;
    }

    .section-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.25rem;
        font-weight: 600;
        margin: 0 0 0.25rem 0;
        color: #1e293b;
    }
    :global(.dark) .section-title {
        color: #f1f5f9;
    }

    .section-icon {
        width: 20px;
        height: 20px;
        color: #2563eb;
    }
    :global(.dark) .section-icon {
        color: #60a5fa;
    }

    .section-hint {
        font-size: 0.8rem;
        color: #64748b;
        margin: 0;
    }
    :global(.dark) .section-hint {
        color: #94a3b8;
    }

    /* ========== CHAPITRES ========== */
    .chapters-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .chapter-item {
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 1rem;
    }
    :global(.dark) .chapter-item {
        border-bottom-color: #334155;
    }

    .chapter-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.75rem;
    }

    .chapter-title-wrap {
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
    }

    .chapter-title {
        font-weight: 600;
        font-size: 1.1rem;
        color: #1e293b;
    }
    :global(.dark) .chapter-title {
        color: #e2e8f0;
    }

    .chapter-actions {
        display: flex;
        gap: 0.25rem;
    }

    .sections-list {
        margin-left: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .section-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.25rem 0;
    }

    .section-title {
        font-size: 0.95rem;
        color: #334155;
    }
    :global(.dark) .section-title {
        color: #cbd5e1;
    }

    .section-actions {
        display: flex;
        gap: 0.25rem;
        opacity: 0;
        transition: opacity 0.15s;
    }
    .section-item:hover .section-actions {
        opacity: 1;
    }

    /* ========== FORMULAIRES ========== */
    .edit-form {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex: 1;
    }
    .edit-form.inline {
        width: 100%;
    }

    .edit-input, .add-input {
        flex: 1;
        padding: 0.4rem 0.6rem;
        border: 1px solid #cbd5e1;
        border-radius: 0.375rem;
        background: white;
        font-size: 0.95rem;
        color: #1e293b;
    }
    :global(.dark) .edit-input,
    :global(.dark) .add-input {
        background: #0f172a;
        border-color: #475569;
        color: white;
    }

    .edit-actions {
        display: flex;
        gap: 0.25rem;
    }

    .btn-icon {
        background: none;
        border: none;
        cursor: pointer;
        padding: 0.25rem;
        border-radius: 0.25rem;
        color: #64748b;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: all 0.15s;
    }
    .btn-icon:hover {
        background: #f1f5f9;
        color: #1e293b;
    }
    .btn-icon.save:hover { color: #10b981; }
    .btn-icon.delete:hover { color: #ef4444; }
    :global(.dark) .btn-icon {
        color: #94a3b8;
    }
    :global(.dark) .btn-icon:hover {
        background: #334155;
        color: #e2e8f0;
    }

    .add-section-btn {
        background: none;
        border: 1px dashed #cbd5e1;
        border-radius: 0.5rem;
        padding: 0.5rem;
        width: 100%;
        text-align: left;
        font-size: 0.9rem;
        color: #2563eb;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        margin-top: 0.25rem;
        transition: background 0.15s;
    }
    .add-section-btn:hover {
        background: #f8fafc;
    }
    :global(.dark) .add-section-btn {
        border-color: #475569;
        color: #60a5fa;
    }
    :global(.dark) .add-section-btn:hover {
        background: #1e293b;
    }

    .add-section-form {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }

    .add-chapter-form {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 1rem;
    }

    .btn-add {
        background: #2563eb;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        color: white;
        font-weight: 500;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
        cursor: pointer;
        transition: background 0.15s;
        white-space: nowrap;
    }
    .btn-add:hover {
        background: #1d4ed8;
    }
    :global(.dark) .btn-add {
        background: #2563eb;
    }
    :global(.dark) .btn-add:hover {
        background: #1d4ed8;
    }

    /* ========== OBJECTIFS ========== */
    .objectives-textarea {
        width: 100%;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        background: #f8fafc;
        padding: 1rem;
        font-family: inherit;
        font-size: 0.95rem;
        line-height: 1.6;
        resize: vertical;
        color: #1e293b;
        margin-bottom: 1.5rem;
    }
    :global(.dark) .objectives-textarea {
        background: #0f172a;
        border-color: #334155;
        color: #f1f5f9;
    }

    .files-summary {
        border-top: 1px solid #e2e8f0;
        padding-top: 1.5rem;
    }
    :global(.dark) .files-summary {
        border-top-color: #334155;
    }

    .files-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #475569;
        margin: 0 0 0.75rem 0;
    }
    :global(.dark) .files-title {
        color: #94a3b8;
    }

    .files-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .file-tag {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        background: #f1f5f9;
        padding: 0.3rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        color: #334155;
    }
    :global(.dark) .file-tag {
        background: #334155;
        color: #cbd5e1;
    }

    /* ========== ACTIONS ========== */
    .editor-actions {
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
        padding: 1.5rem 1.75rem 0;
        border-top: 1px solid #e2e8f0;
        margin-top: 1rem;
    }
    :global(.dark) .editor-actions {
        border-top-color: #334155;
    }

    .btn-outline {
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #cbd5e1;
        background: white;
        color: #475569;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.15s;
    }
    .btn-outline:hover {
        background: #f8fafc;
        border-color: #94a3b8;
    }
    :global(.dark) .btn-outline {
        background: #1e293b;
        border-color: #475569;
        color: #cbd5e1;
    }
    :global(.dark) .btn-outline:hover {
        background: #334155;
    }

    .btn-primary {
        padding: 0.75rem 2rem;
        border-radius: 0.5rem;
        border: none;
        background: #2563eb;
        color: white;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        transition: all 0.15s;
    }
    .btn-primary:hover {
        background: #1d4ed8;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -2px rgba(37,99,235,0.3);
    }
</style>