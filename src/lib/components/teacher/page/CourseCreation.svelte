<script lang="ts">
    import { getContext } from 'svelte';
    import { goto } from '$app/navigation';
    import { TUTOR_FRONT_URL } from '$lib/constants';

    const i18n = getContext('i18n');

    let courseTitle = '';
    let courseLanguage = 'fr-FR';
    let courseCategory = '';
    let customCategory = '';
    let showCustomCategory = false;
    let courseLevel = '';
    let pedagogicalObjectives = '';
    let uploadedFiles: File[] = [];
    let isDragOver = false;

    // UI States l'Custom Select
    let isLangOpen = false;
    let isCategoryOpen = false;

    // === Modal States ===
    let isGenerating = false;          // Modal visible ?
    let generationSuccess = false;     // Fin de génération ?
    let progress = 0;                 // Progress bar

    // === Fonction pour locker/délocker le scroll du body ===
    function lockBodyScroll(lock: boolean) {
        if (typeof document !== 'undefined') {
            document.body.style.overflow = lock ? 'hidden' : '';
        }
    }

    // Category keys (will be translated when displayed)
    const categoryKeys = [
        'Informatique',
        'Chimie',
        'Mathématique',
        'Autre'
    ];

    // Level keys (will be translated when displayed)
    const levelKeys = [
        { id: 'easy', key: 'Facile' },
        { id: 'medium', key: 'Moyen' },
        { id: 'difficult', key: 'Difficile' }
    ];

    // Language keys (will be translated when displayed)
    const languageKeys = [
        { id: 'en-US', key: 'English' },
        { id: 'fr-FR', key: 'Français' },
        { id: 'ar-MA', key: 'العربية' }
    ];

    // Reactive categories with current language
    $: categories = categoryKeys.map(key => ({ key, label: $i18n.t(key) }));
    
    // Reactive levels with current language
    $: levels = levelKeys.map(item => ({ id: item.id, label: $i18n.t(item.key) }));
    
    // Reactive languages with current language
    $: languages = languageKeys.map(item => ({ id: item.id, label: $i18n.t(item.key) }));

    $: showCustomCategory = courseCategory === 'Autre';
    $: selectedLangLabel = languages.find(l => l.id === courseLanguage)?.label || $i18n.t('Sélectionnez une langue');
    $: selectedCatLabel = courseCategory ? categories.find(c => c.key === courseCategory)?.label || courseCategory : $i18n.t('Sélectionnez une catégorie');

    function closeLangMenu() { setTimeout(() => isLangOpen = false, 150); }
    function closeCatMenu() { setTimeout(() => isCategoryOpen = false, 150); }

    function handleDragOver(e: DragEvent) {
        e.preventDefault();
        isDragOver = true;
    }

    function handleDragLeave(e: DragEvent) {
        e.preventDefault();
        isDragOver = false;
    }

    function handleDrop(e: DragEvent) {
        e.preventDefault();
        isDragOver = false;
        if (e.dataTransfer?.files) {
            uploadedFiles = [...uploadedFiles, ...Array.from(e.dataTransfer.files)];
        }
    }

    function handleFileInput(e: Event) {
        const target = e.target as HTMLInputElement;
        if (target.files) {
            uploadedFiles = [...uploadedFiles, ...Array.from(target.files)];
        }
    }

    function removeUploadedFile(index: number) {
        uploadedFiles = uploadedFiles.filter((_, i) => i !== index);
    }

    // === Fermer le modal (appelé aussi après succès) ===
    function closeModal() {
        isGenerating = false;
        generationSuccess = false;
        progress = 0;
        lockBodyScroll(false); // Réactive le scroll
    }

    // === Génération simulée ===
    function generateCourse() {
        const finalCategory = showCustomCategory ? customCategory : courseCategory;

        if (!courseTitle || !courseLanguage || !finalCategory || !courseLevel || !pedagogicalObjectives) {
            alert($i18n.t('Veuillez remplir tous les champs obligatoires'));
            return;
        }

        if (uploadedFiles.length === 0) {
            alert($i18n.t('Veuillez uploader au moins un fichier PDF'));
            return;
        }

        // Validation passée -> On affiche le modal et on bloque le scroll
        isGenerating = true;
        generationSuccess = false;
        progress = 0;
        lockBodyScroll(true);

        // Simulation de progression
        const interval = setInterval(() => {
            if (progress < 90) {
                progress += 10;
            }
        }, 200);

        // Simule un appel API (2 secondes)
        setTimeout(() => {
            clearInterval(interval);
            progress = 100;
            
            // Logique métier ici
            console.log({
                title: courseTitle,
                language: courseLanguage,
                category: finalCategory,
                level: courseLevel,
                objectives: pedagogicalObjectives,
                files: uploadedFiles
            });

            generationSuccess = true;
            // Le scroll reste bloqué jusqu'à ce que l'utilisateur ferme le modal
            
        }, 2000);
    }
</script>

<div class="header-banner">
    <div class="header-illustration">
        <div class="icon-books">
            <svg width="70" height="70" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="4" y="10" width="18" height="24" rx="2" fill="#378add" opacity="0.85"/>
                <rect x="8" y="6" width="18" height="24" rx="2" fill="#1eb288" opacity="0.85"/>
                <rect x="3" y="13" width="6" height="18" rx="1.5" fill="#2563eb" opacity="0.7"/>
                <rect x="11" y="8" width="2.5" height="5" rx="1" fill="white" opacity="0.8"/>
                <path d="M22 24 L27 12 L32 24 M23.5 21 H30.5" stroke="#378add" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
    </div>

    <div class="header-text-content">
        <h1 class="page-title">{$i18n.t('Mes')} <span class="text-blue">{$i18n.t('Cours')}</span></h1>
        <p class="page-subtitle">{$i18n.t('Créez et gérez vos cours avec simplicité')}</p>
    </div>
</div>

<div class="card">

    <div class="section">
        <h2 class="section-title">{$i18n.t('Informations Générales')}</h2>

        <div class="form-group">
            <label for="courseTitle" class="form-label">
                {$i18n.t('Titre de cours')} <span class="required-asterisk">*</span>
            </label>
            <input
                type="text"
                id="courseTitle"
                bind:value={courseTitle}
                placeholder={$i18n.t('Entrez le titre du cours')}
                class="form-control"
            />
        </div>

        <div class="form-row">
            <div class="form-group">
                <label for="courseLanguage" class="form-label">
                    {$i18n.t('Langue de cours')} <span class="required-asterisk">*</span>
                </label>
                <div class="custom-select-wrapper" tabindex="0" on:blur={closeLangMenu}>
                    <div class="form-control custom-select-trigger {isLangOpen ? 'open' : ''}" on:click={() => isLangOpen = !isLangOpen}>
                        <span>{selectedLangLabel}</span>
                        <svg class="chevron {isLangOpen ? 'rotate' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                    </div>
                    
                    {#if isLangOpen}
                        <ul class="custom-select-options">
                            {#each languages as lang}
                                <li class="custom-option {courseLanguage === lang.id ? 'selected' : ''}" 
                                    on:click={() => { courseLanguage = lang.id; isLangOpen = false; }}>
                                    {lang.label}
                                    {#if courseLanguage === lang.id}
                                        <svg class="check-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                    {/if}
                                </li>
                            {/each}
                        </ul>
                    {/if}
                </div>
            </div>

            <div class="form-group">
                <label for="courseCategory" class="form-label">
                    {$i18n.t('Catégorie')} <span class="required-asterisk">*</span>
                </label>
                <div class="custom-select-wrapper" tabindex="0" on:blur={closeCatMenu}>
                    <div class="form-control custom-select-trigger {isCategoryOpen ? 'open' : ''}" on:click={() => isCategoryOpen = !isCategoryOpen}>
                        <span class="{!courseCategory ? 'placeholder' : ''}">{selectedCatLabel}</span>
                        <svg class="chevron {isCategoryOpen ? 'rotate' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                    </div>

                    {#if isCategoryOpen}
                        <ul class="custom-select-options">
                            {#each categories as category}
                                <li class="custom-option {courseCategory === category.key ? 'selected' : ''}" 
                                    on:click={() => { courseCategory = category.key; isCategoryOpen = false; }}>
                                    {category.label}
                                    {#if courseCategory === category.key}
                                        <svg class="check-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                    {/if}
                                </li>
                            {/each}
                        </ul>
                    {/if}
                </div>
                
                {#if showCustomCategory}
                    <input
                        type="text"
                        bind:value={customCategory}
                        placeholder={$i18n.t('Votre catégorie personnalisée')}
                        class="form-control custom-input-mt"
                    />
                {/if}
            </div>
        </div>

        <div class="form-group">
            <label class="form-label">
                {$i18n.t('Niveau du cours')} <span class="required-asterisk">*</span>
            </label>
            <div class="level-group">
                {#each levels as level}
                    <button
                        type="button"
                        class="level-btn {courseLevel === level.id ? 'active' : ''}"
                        on:click={() => courseLevel = level.id}
                    >
                        {#if level.id === 'easy'}
                            <span class="level-dot easy"></span>
                        {:else if level.id === 'medium'}
                            <span class="level-dot medium"></span>
                        {:else}
                            <span class="level-dot difficult"></span>
                        {/if}
                        {level.label}
                    </button>
                {/each}
            </div>
        </div>
    </div>

    <div class="section">
        <h2 class="section-title">
            {$i18n.t('Objectifs pédagogiques')} <span class="required-asterisk">*</span>
        </h2>
        <textarea
            bind:value={pedagogicalObjectives}
            placeholder={$i18n.t('Décrivez les objectifs pédagogiques et ce que les étudiants apprendront...')}
            rows="5"
            class="form-control textarea"
        ></textarea>
    </div>

    <div class="section">
        <h2 class="section-title">
            {$i18n.t('Matériel Pédagogique')} <span class="required-asterisk">*</span>
        </h2>

        <div
            class="dropzone {isDragOver ? 'active' : ''}"
            on:dragover={handleDragOver}
            on:dragleave={handleDragLeave}
            on:drop={handleDrop}
            role="button"
            tabindex="0"
        >
            <label for="fileInput" class="dropzone-label">
                <div class="dropzone-icon">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                    </svg>
                </div>
                <p class="dropzone-text">
                    {$i18n.t('Glissez-déposez vos fichiers PDF ici ou')}
                    <span class="dropzone-link">{$i18n.t('parcourez vos dossiers')}</span>
                </p>
                <p class="dropzone-hint">{$i18n.t('Formats acceptés : PDF (Max 500MB chacun)')}</p>
            </label>
            <input
                type="file"
                id="fileInput"
                on:change={handleFileInput}
                accept=".pdf"
                multiple
                class="hidden-input"
            />
        </div>

        {#if uploadedFiles.length > 0}
            <div class="files-container">
                <h3 class="files-title">{$i18n.t('Fichiers uploadés')} ({uploadedFiles.length})</h3>
                <div class="files-list">
                    {#each uploadedFiles as file, index}
                        <div class="file-item">
                            <div class="file-icon-wrap">
                                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                </svg>
                            </div>
                            <div class="file-info">
                                <p class="file-name">{file.name}</p>
                                <p class="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                            </div>
                            <button
                                type="button"
                                on:click={() => removeUploadedFile(index)}
                                class="btn-remove"
                                aria-label={$i18n.t('Supprimer le fichier')}
                            >
                                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                                </svg>
                            </button>
                        </div>
                    {/each}
                </div>
            </div>
        {/if}
    </div>

    <div class="form-actions">
        <button type="button" on:click={generateCourse} class="btn-primary">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            {$i18n.t('Générer le cours')}
        </button>
    </div>
</div>

<!-- ================= MODAL DE GÉNÉRATION ================= -->
{#if isGenerating}
    <div class="modal-overlay" role="dialog" aria-modal="true">
        <div class="modal-card">

            {#if !generationSuccess}
                <!-- ÉTAT : CHARGEMENT -->
                <div class="modal-loading">
                    <!-- Logo + Spinner combinés -->
                    <div class="logo-spinner-wrap">
                        <svg class="spinner-ring" viewBox="0 0 80 80">
                            <circle cx="40" cy="40" r="34" fill="none" stroke="#e2e8f0" stroke-width="5"/>
                            <circle class="spin-arc" cx="40" cy="40" r="34" fill="none" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
                        </svg>
                        <div class="logo-center">
                            <img src="{TUTOR_FRONT_URL}/static/favicon.png" alt="OT AI" />
                        </div>
                    </div>

                    <h3 class="modal-title">{$i18n.t('Génération en cours')}</h3>
                    <p class="modal-subtitle">{$i18n.t('Veuillez patienter pendant que nous créons votre cours...')}</p>
                    
                    <div class="progress-container">
                        <div class="progress-bar" style="width: {progress}%;">
                            <span class="progress-text">{progress}%</span>
                        </div>
                    </div>
                </div>

            {:else}
                <!-- ÉTAT : SUCCÈS -->
                <div class="modal-success">
                    <div class="success-logo-wrap">
                        <img src="{TUTOR_FRONT_URL}/static/favicon.png" alt="OT AI" class="success-logo" />
                        <div class="success-badge">
                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                            </svg>
                        </div>
                    </div>

                    <h3 class="modal-title">{$i18n.t('Cours généré avec succès !')}</h3>
                    <p class="modal-subtitle">{$i18n.t('Votre cours a été créé et est maintenant disponible.')}</p>
                    
                    <div class="modal-actions">
                        <button class="btn-secondary" on:click={closeModal}>
                            {$i18n.t('Fermer')}
                        </button>
                        <button class="btn-primary" on:click={() => {
                            closeModal();
                            const finalCategory = showCustomCategory ? customCategory : courseCategory;
                            goto('/teacher/courses?view=plan', {
                                state: {
                                    courseData: {
                                        title: courseTitle,
                                        language: courseLanguage,
                                        category: finalCategory,
                                        level: courseLevel,
                                        objectives: pedagogicalObjectives,
                                        files: uploadedFiles
                                    }
                                }
                            });
                        }}>
                            {$i18n.t('Voir le cours')}
                        </button>
                    </div>
                </div>
            {/if}

        </div>
    </div>
{/if}
<style>
    /* ============================================
       MODAL STYLES (CORRIGÉS)
       ============================================ */
 /* ============================================
   MODAL STYLES
   ============================================ */
    .modal-overlay {
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-color: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.25s ease-out;
    }

    .modal-card {
        background: #ffffff;
        border-radius: 2rem;
        padding: 2.75rem 2.5rem 2.25rem;
        max-width: 440px;
        width: 90%;
        box-shadow: 0 32px 64px -12px rgba(0,0,0,0.22), 0 0 0 1px rgba(0,0,0,0.04);
        text-align: center;
        animation: slideUp 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    :global(.dark) .modal-card {
        background: #0f172a;
        box-shadow: 0 32px 64px -12px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.06);
    }

    /* --- Loading State --- */
    .modal-loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }

    /* Spinner ring avec logo au centre */
    .logo-spinner-wrap {
        position: relative;
        width: 100px;
        height: 100px;
        margin-bottom: 0.5rem;
    }

    .spinner-ring {
        width: 100%;
        height: 100%;
        animation: rotate 1.6s linear infinite;
    }

    .spin-arc {
        stroke-dasharray: 80 134;
        stroke-dashoffset: 0;
        animation: dash 1.6s ease-in-out infinite;
    }

    .logo-center {
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        width: 56px;
        height: 56px;
        background: #f8fafc;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    :global(.dark) .logo-center {
        background: #1e293b;
    }

    .logo-center img {
        width: 38px;
        height: 38px;
        object-fit: contain;
    }

    /* --- Success State --- */
    .modal-success {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.875rem;
    }

    .success-logo-wrap {
        position: relative;
        width: 88px;
        height: 88px;
        margin-bottom: 0.5rem;
    }

    .success-logo {
        width: 88px;
        height: 88px;
        object-fit: contain;
        border-radius: 50%;
        background: #f0f9ff;
        padding: 14px;
        border: 2px solid #e0f2fe;
    }

    :global(.dark) .success-logo {
        background: #0c2340;
        border-color: #1e3a5f;
    }

    .success-badge {
        position: absolute;
        bottom: -2px;
        right: -2px;
        width: 28px;
        height: 28px;
        background: #22c55e;
        border-radius: 50%;
        border: 2.5px solid #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
    }

    :global(.dark) .success-badge {
        border-color: #0f172a;
    }

    .success-badge svg {
        width: 14px;
        height: 14px;
    }

    /* --- Shared text --- */
    .modal-title {
        font-size: 1.375rem;
        font-weight: 700;
        margin: 0;
        color: #0f172a;
        letter-spacing: -0.3px;
    }

    :global(.dark) .modal-title { color: #f8fafc; }

    .modal-subtitle {
        font-size: 0.9375rem;
        color: #64748b;
        margin: 0;
        line-height: 1.55;
        max-width: 300px;
    }

    :global(.dark) .modal-subtitle { color: #94a3b8; }

    /* --- Progress Bar --- */
    .progress-container {
        width: 100%;
        height: 9px;
        background: #f1f5f9;
        border-radius: 99px;
        overflow: hidden;
        margin-top: 0.25rem;
    }

    :global(.dark) .progress-container { background: #1e293b; }

    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #2563eb 0%, #1eb288 100%);
        border-radius: 99px;
        transition: width 0.3s ease-out;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 6px;
        min-width: 28px;
    }

    .progress-text {
        font-size: 0.65rem;
        font-weight: 700;
        color: white;
    }

    /* --- Actions --- */
    .modal-actions {
        display: flex;
        gap: 0.75rem;
        margin-top: 1rem;
        width: 100%;
    }

    .btn-secondary {
        flex: 1;
        padding: 0.7rem 1rem;
        border-radius: 0.875rem;
        border: 1.5px solid #e2e8f0;
        background: white;
        color: #475569;
        font-family: inherit;
        font-weight: 500;
        font-size: 0.9375rem;
        cursor: pointer;
        transition: all 0.15s;
    }

    .btn-secondary:hover {
        background: #f8fafc;
        border-color: #cbd5e1;
    }

    :global(.dark) .btn-secondary {
        background: #1e293b;
        border-color: #334155;
        color: #cbd5e1;
    }

    :global(.dark) .btn-secondary:hover {
        background: #334155;
    }

    /* --- Animations --- */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes slideUp {
        from { opacity: 0; transform: translateY(24px) scale(0.96); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    @keyframes rotate {
        100% { transform: rotate(360deg); }
    }

    @keyframes dash {
        0%   { stroke-dasharray: 1 213; stroke-dashoffset: 0; }
        50%  { stroke-dasharray: 120 94; stroke-dashoffset: -45; }
        100% { stroke-dasharray: 120 94; stroke-dashoffset: -165; }
    }
    /* ============================================
       STYLES EXISTANTS (INCHANGÉS)
       ============================================ */
	.header-banner {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 1.5rem;
		position: relative;
	}

    .header-illustration {
        display: flex;
    }

    .icon-books svg {
        height: 70px;
        width: 80px; 
        display: block;
        object-fit: contain;
    }

    .page-title {
        font-size: 2.25rem;
        font-weight: 800;
        margin: 0 0 0.35rem 0;
        color: #1e293b;
        letter-spacing: -0.5px;
    }

    .text-blue {
        color: #2563eb;
    }

    .page-subtitle {
        font-size: 1rem;
        color: #64748b;
        margin: 0;
    }

    .card {
        background-color: #ffffff;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04);
        padding: 2rem;
        border: 1px solid #f1f5f9;
    }

    .section {
        margin-bottom: 2rem;
        padding-bottom: 2rem;
        border-bottom: 1px solid #f1f5f9;
    }

    .section:last-of-type {
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }

    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1e293b;
        margin: 0 0 1.25rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .section-title::before {
        content: '';
        display: inline-block;
        width: 3px;
        height: 1.1em;
        background: #2563eb;
        border-radius: 2px;
    }

    .required-asterisk {
        color: #ef4444;
        font-weight: bold;
        margin-left: 0.15rem;
    }

    .form-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.25rem;
    }

    .form-group {
        margin-bottom: 1.25rem;
    }

    .form-group:last-child {
        margin-bottom: 0;
    }

    .form-label {
        display: block;
        font-size: 0.8125rem;
        font-weight: 500;
        color: #475569;
        margin-bottom: 0.4rem;
        letter-spacing: 0.01em;
    }

    .form-control {
        width: 100%;
        padding: 0.55rem 0.875rem;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        background-color: #f8fafc;
        color: #1e293b;
        outline: none;
        box-sizing: border-box;
        font-family: inherit;
        font-size: 0.9375rem;
        transition: border-color 0.15s, background-color 0.15s, box-shadow 0.15s;
    }

    .form-control:focus {
        border-color: #2563eb;
        background-color: #ffffff;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
    }

    .form-control::placeholder {
        color: #94a3b8;
    }

    .custom-input-mt {
        margin-top: 0.625rem;
    }

    .textarea {
        resize: vertical;
        min-height: 120px;
        line-height: 1.6;
    }

    .custom-select-wrapper {
        position: relative;
        outline: none;
    }

    .custom-select-trigger {
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
        user-select: none;
    }

    .custom-select-trigger.open {
        border-color: #2563eb;
        background-color: #ffffff;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
    }

    .custom-select-trigger .placeholder {
        color: #94a3b8;
    }

    .chevron {
        width: 1.25rem;
        height: 1.25rem;
        color: #94a3b8;
        transition: transform 0.2s ease;
    }

    .chevron.rotate {
        transform: rotate(180deg);
    }

    .custom-select-options {
        position: absolute;
        top: calc(100% + 0.5rem);
        left: 0;
        right: 0;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        z-index: 50;
        max-height: 200px;
        overflow-y: auto;
        padding: 0.5rem;
        margin: 0;
        list-style: none;
        animation: fadeInDown 0.2s ease-out;
    }

    .custom-option {
        padding: 0.5rem 0.75rem;
        border-radius: 0.375rem;
        cursor: pointer;
        font-size: 0.9375rem;
        color: #1e293b;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: background-color 0.15s;
    }

    .custom-option:hover {
        background-color: #f1f5f9;
    }

    .custom-option.selected {
        background-color: #eff6ff;
        color: #2563eb;
        font-weight: 500;
    }

    .check-icon {
        width: 1rem;
        height: 1rem;
        color: #2563eb;
    }

    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .level-group {
        display: flex;
        gap: 0.625rem;
    }

    .level-btn {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
        padding: 0.55rem 0;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        background: #f8fafc;
        color: #64748b;
        font-family: inherit;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.15s;
    }

    .level-btn:hover {
        border-color: #2563eb;
        color: #2563eb;
        background: #eff6ff;
    }

    .level-btn.active {
        border-color: #2563eb;
        background: #eff6ff;
        color: #2563eb;
    }

    .level-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .level-dot.easy { background: #22c55e; }
    .level-dot.medium { background: #f59e0b; }
    .level-dot.difficult { background: #ef4444; }

    .dropzone {
        border: 2px dashed #cbd5e1;
        border-radius: 0.75rem;
        padding: 2.5rem 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        background-color: #f8fafc;
    }

    .dropzone:hover,
    .dropzone.active {
        border-color: #1eb288;
        background-color: #f0fdf8;
    }

    .dropzone-label {
        cursor: pointer;
        display: block;
    }

    .dropzone-icon {
        color: #1eb288;
        margin-bottom: 0.75rem;
        display: flex;
        justify-content: center;
    }

    .dropzone-icon svg {
        width: 2.75rem;
        height: 2.75rem;
    }

    .dropzone-text {
        color: #374151;
        font-weight: 500;
        font-size: 0.9375rem;
        margin: 0 0 0.25rem 0;
    }

    .dropzone-link {
        color: #1eb288;
        text-decoration: underline;
        text-underline-offset: 2px;
    }

    .dropzone-hint {
        font-size: 0.75rem;
        color: #94a3b8;
        margin: 0;
    }

    .hidden-input {
        display: none;
    }

    .files-container {
        margin-top: 1rem;
    }

    .files-title {
        font-size: 0.8125rem;
        font-weight: 500;
        color: #475569;
        margin: 0 0 0.625rem 0;
    }

    .files-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .file-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        background: #f1f5f9;
        padding: 0.625rem 0.875rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
    }

    .file-icon-wrap {
        color: #ef4444;
        flex-shrink: 0;
    }

    .file-icon-wrap svg {
        width: 1.25rem;
        height: 1.25rem;
    }

    .file-info {
        flex: 1;
        min-width: 0;
    }

    .file-name {
        font-size: 0.875rem;
        font-weight: 500;
        color: #1e293b;
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .file-size {
        font-size: 0.75rem;
        color: #94a3b8;
        margin: 0;
    }

    .btn-remove {
        background: none;
        border: none;
        cursor: pointer;
        padding: 0.25rem;
        color: #94a3b8;
        border-radius: 0.25rem;
        display: flex;
        align-items: center;
        transition: color 0.15s;
        flex-shrink: 0;
    }

    .btn-remove svg {
        width: 1rem;
        height: 1rem;
    }

    .btn-remove:hover {
        color: #ef4444;
    }

    .form-actions {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 0.75rem;
        padding-top: 1.5rem;
        border-top: 1px solid #f1f5f9;
        margin-top: 1.5rem;
    }

    .btn-primary {
        background-color: #2563eb;
        color: #ffffff;
        font-family: inherit;
        font-weight: 500;
        font-size: 0.9375rem;
        padding: 0.55rem 1.5rem;
        border-radius: 0.5rem;
        border: none;
        cursor: pointer;
        transition: background-color 0.15s, transform 0.1s;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .btn-primary:hover {
        background-color: #1d4ed8;
    }

    .btn-primary:active {
        transform: scale(0.98);
    }

    .btn-primary svg {
        width: 1.1rem;
        height: 1.1rem;
    }

    /* DARK MODE */
    :global(.dark) .page-title {
        color: #f1f5f9;
    }

    :global(.dark) .page-subtitle {
        color: #94a3b8;
    }

    :global(.dark) .card {
        background-color: #111827;
        border-color: #1f2937;
        box-shadow: none;
    }

    :global(.dark) .section {
        border-bottom-color: #1f2937;
    }

    :global(.dark) .section-title {
        color: #f1f5f9;
    }

    :global(.dark) .form-label,
    :global(.dark) .files-title {
        color: #94a3b8;
    }

    :global(.dark) .form-control {
        border-color: #374151;
        background-color: #1f2937;
        color: #f1f5f9;
    }

    :global(.dark) .form-control:focus,
    :global(.dark) .custom-select-trigger.open {
        border-color: #2563eb;
        background-color: #1f2937;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
    }

    :global(.dark) .custom-select-options {
        background: #1f2937;
        border-color: #374151;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    
    :global(.dark) .custom-option {
        color: #f1f5f9;
    }

    :global(.dark) .custom-option:hover {
        background-color: #374151;
    }

    :global(.dark) .custom-option.selected {
        background-color: #1e3a5f;
        color: #60a5fa;
    }
    
    :global(.dark) .check-icon {
        color: #60a5fa;
    }

    :global(.dark) .level-btn {
        border-color: #374151;
        background: #1f2937;
        color: #94a3b8;
    }

    :global(.dark) .level-btn:hover,
    :global(.dark) .level-btn.active {
        border-color: #2563eb;
        background: #1e3a5f;
        color: #60a5fa;
    }

    :global(.dark) .dropzone {
        border-color: #374151;
        background-color: #1f2937;
    }

    :global(.dark) .dropzone:hover,
    :global(.dark) .dropzone.active {
        background-color: #0f2d2a;
        border-color: #1eb288;
    }

    :global(.dark) .dropzone-text {
        color: #d1d5db;
    }

    :global(.dark) .dropzone-hint {
        color: #6b7280;
    }

    :global(.dark) .file-item {
        background-color: #1f2937;
        border-color: #374151;
    }

    :global(.dark) .file-name {
        color: #e5e7eb;
    }

    :global(.dark) .file-size {
        color: #6b7280;
    }

    :global(.dark) .btn-remove {
        color: #6b7280;
    }

    :global(.dark) .btn-remove:hover {
        color: #f87171;
    }

    :global(.dark) .form-actions {
        border-top-color: #1f2937;
    }

    @media (max-width: 640px) {
        .header-banner {
            padding: 1rem;
            flex-direction: column;
            gap: 1rem;
        }

        .page-title {
            font-size: 1.75rem;
        }

        .card {
            padding: 1.25rem;
        }

        .form-row {
            grid-template-columns: 1fr;
            gap: 0;
        }

        .level-group {
            flex-direction: column;
        }

        .form-actions {
            flex-direction: column-reverse;
        }

        .btn-primary {
            width: 100%;
            justify-content: center;
        }

        .modal-actions {
            flex-direction: column;
        }
    }
</style>