<script lang="ts">
    import { getContext, onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { fade, slide } from 'svelte/transition';

    export let courseId: string;

    const i18n = getContext('i18n');

    // ── TYPES ──────────────────────────────────────────────
    interface Section {
        id: string;
        title: string;
        status: 'not-started' | 'in-progress' | 'completed';
    }

    interface Chapter {
        id: string;
        title: string;
        sections: Section[];
    }

    interface CourseFile {
        id: string;
        name: string;
        size_kb: number;
        type: string;
    }

    interface CourseDetail {
        id: string;
        title: string;
        language: string;
        category: string | null;
        level: string;
        teacher_name: string;
        objectives: string;
        welcome_message?: string;
        files: CourseFile[];
        chapters: Chapter[];
        enrolled_at: string;
        status: string;
    }

    // ── ÉTATS ──────────────────────────────────────────────
    let cours: CourseDetail | null = null;
    let estEnChargement = true;
    let erreurChargement = '';
    let chapitresDeveloppes = new Set<string>();

    // ── CHARGEMENT DES DONNÉES ─────────────────────────────
    async function chargerDetailsCours() {
        estEnChargement = true;
        erreurChargement = '';
        try {
            const token = localStorage.getItem('token') ?? '';
            const reponse = await fetch(`/api/v1/student/courses/${courseId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!reponse.ok) {
                const err = await reponse.json().catch(() => ({}));
                throw new Error(err.detail ?? `Erreur ${reponse.status}`);
            }
            cours = await reponse.json();

            // Développer le premier chapitre par défaut
            if (cours?.chapters?.length) {
                chapitresDeveloppes.add(cours.chapters[0].id);
                chapitresDeveloppes = new Set(chapitresDeveloppes);
            }
        } catch (e: any) {
            erreurChargement = e?.message ?? 'Erreur lors du chargement';
        } finally {
            estEnChargement = false;
        }
    }

    onMount(chargerDetailsCours);

    // ── FONCTIONS UTILITAIRES ──────────────────────────────
    function formaterTaille(kb: number): string {
        if (!kb) return '';
        if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`;
        return `${kb} KB`;
    }

    function retourArriere() {
        goto('/student/classrooms');
    }

    function demarrerApprentissage() {
        goto(`/student/classrooms/${courseId}/learn`);
    }

    function basculerChapitre(id: string) {
        if (chapitresDeveloppes.has(id)) {
            chapitresDeveloppes.delete(id);
        } else {
            chapitresDeveloppes.add(id);
        }
        chapitresDeveloppes = new Set(chapitresDeveloppes);
    }

    function obtenirCouleurStatut(statut: string): string {
        switch (statut) {
            case 'completed': return '#10b981';
            case 'in-progress': return '#f59e0b';
            default: return '#94a3b8';
        }
    }

    function obtenirTexteStatut(statut: string): string {
        switch (statut) {
            case 'completed': return $i18n.t('Terminé');
            case 'in-progress': return $i18n.t('En cours');
            default: return $i18n.t('Non commencé');
        }
    }

    // ── VARIABLES RÉACTIVES ────────────────────────────────
    $: listeObjectifs = cours?.objectives
        ? cours.objectives.split('\n').filter(l => l.trim())
        : [];

    $: nombreTotalSections = cours?.chapters?.reduce(
        (acc, chap) => acc + (chap.sections?.length ?? 0), 0
    ) ?? 0;
</script>

<!-- ════════════════════════════════════════════════════════ -->

<svelte:head>
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</svelte:head>

{#if estEnChargement}
    <div class="page-conteneur flex-centre">
        <div class="chargeur"></div>
    </div>

{:else if erreurChargement}
    <div class="page-conteneur flex-centre">
        <div class="boite-erreur">
            <p>{erreurChargement}</p>
            <button class="btn-primaire" on:click={chargerDetailsCours}>
                {$i18n.t('Réessayer')}
            </button>
        </div>
    </div>

{:else if cours}
    <div class="page-conteneur" in:fade={{ duration: 300 }}>
        
        <!-- BOUTON RETOUR -->
        <button class="btn-retour" on:click={retourArriere}>
            ← {$i18n.t('Retour aux cours')}
        </button>

        <!-- GRILLE BENTO -->
        <div class="grille-bento">
            
            <!-- 1. CARTE HERO (Gauche) -->
            <div class="carte carte-hero col-8">
                <div class="en-tete-hero">
                    <div class="info-prof">
                        <div class="avatar">
                            {cours.teacher_name?.slice(0, 2).toUpperCase() ?? 'PR'}
                        </div>
                        <span class="nom-prof">Pr. {cours.teacher_name}</span>
                    </div>
                    <div class="badges">
                        {#if cours.category}
                            <span class="etiquette-categorie">{cours.category}</span>
                        {/if}
                        <span class="etiquette-langue">{cours.language}</span>
                    </div>
                </div>

                <h1 class="titre-cours">{cours.title}</h1>
                
                <p class="texte-bienvenue">
                    {cours.welcome_message || $i18n.t('Bienvenue dans ce cours ! Préparez-vous à apprendre et à explorer de nouveaux concepts.')}
                </p>

                <!-- STATISTIQUES -->
                <div class="statistiques">
                    <div class="stat-item">
                        <span class="stat-nombre">{cours.chapters?.length ?? 0}</span>
                        <span class="stat-libelle">{$i18n.t('Chapitres')}</span>
                    </div>
                    <div class="stat-separateur"></div>
                    <div class="stat-item">
                        <span class="stat-nombre">{nombreTotalSections}</span>
                        <span class="stat-libelle">{$i18n.t('Sections')}</span>
                    </div>
                    <div class="stat-separateur"></div>
                    <div class="stat-item">
                        <span class="stat-nombre">{cours.files?.length ?? 0}</span>
                        <span class="stat-libelle">{$i18n.t('Ressources')}</span>
                    </div>
                </div>
            </div>

            <!-- 2. CARTE DISCUSSION (Droite) -->
            <div class="carte carte-discussion col-4 centre-contenu">
                <h2 class="titre-carte">{$i18n.t('Discussion de classe')}</h2>
                <hr class="separateur" />
                <p class="texte-carte texte-centre">
                    {$i18n.t('Connectez-vous avec vos camarades et discutez des concepts du cours.')}
                </p>
                <button class="btn-outline mt-auto">
                    {$i18n.t('Rejoindre')}
                </button>
            </div>

            <!-- 3. CARTE RESSOURCES (Gauche) -->
            <div class="carte col-6">
                <h2 class="titre-carte">{$i18n.t('Ressources du cours')}</h2>
                <hr class="separateur" />
                
                {#if cours.files && cours.files.length > 0}
                    <div class="liste-ressources">
                        {#each cours.files as fichier}
                            <div class="item-ressource">
                                <div class="icone-ressource">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                    </svg>
                                </div>
                                <div class="info-ressource">
                                    <p class="nom-ressource">{fichier.name}</p>
                                    <p class="meta-ressource">PDF • {formaterTaille(fichier.size_kb)}</p>
                                </div>
                            </div>
                        {/each}
                    </div>
                {:else}
                    <p class="texte-centre texte-muet">{$i18n.t('Aucune ressource disponible')}</p>
                {/if}
            </div>

            <!-- 4. CARTE OBJECTIFS (Droite) -->
            <div class="carte col-6">
                <h2 class="titre-carte">{$i18n.t('Objectifs d\'apprentissage')}</h2>
                <hr class="separateur" />
                
                {#if listeObjectifs.length > 0}
                    <p class="texte-carte mb-4">{$i18n.t('À la fin de ce cours, vous serez capable de :')}</p>
                    <ol class="liste-objectifs">
                        {#each listeObjectifs as objectif, i}
                            <li>{objectif}</li>
                        {/each}
                    </ol>
                {:else}
                    <p class="texte-centre texte-muet">{$i18n.t('Aucun objectif défini')}</p>
                {/if}
            </div>

            <!-- 5. CARTE CHAPITRES (Pleine largeur) -->
            <div class="carte col-12">
                <h2 class="titre-carte">{$i18n.t('Plan de cour')}</h2>
                <hr class="separateur" />
                
                {#if cours.chapters && cours.chapters.length > 0}
                    <div class="liste-chapitres">
                        {#each cours.chapters as chapitre, indice (chapitre.id)}
                            <div class="bloc-chapitre">
                                <!-- En-tête du chapitre (clicable) -->
                                <button 
                                    class="en-tete-chapitre"
                                    class:developpe={chapitresDeveloppes.has(chapitre.id)}
                                    on:click={() => basculerChapitre(chapitre.id)}
                                >
                                    <div class="numero-chapitre">{indice + 1}</div>
                                    <span class="titre-chapitre">{chapitre.title}</span>
                                    <span class="nombre-sections">
                                        {chapitre.sections?.length ?? 0} {$i18n.t('sections')}
                                    </span>
                                    <svg 
                                        class="fleche" 
                                        class:tournee={chapitresDeveloppes.has(chapitre.id)}
                                        viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                        width="18" height="18"
                                    >
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 18l6-6-6-6"/>
                                    </svg>
                                </button>

                                <!-- Sections du chapitre -->
                                {#if chapitresDeveloppes.has(chapitre.id)}
                                    <div class="contenu-chapitre" transition:slide={{ duration: 250 }}>
                                        {#if chapitre.sections && chapitre.sections.length > 0}
                                            <div class="liste-sections">
                                                {#each chapitre.sections as section, idx (section.id)}
                                                    <div class="item-section">
                                                        <div class="point-section" style="background: {obtenirCouleurStatut(section.status)};"></div>
                                                        <span class="titre-section">{section.title}</span>
                                                        <span 
                                                            class="statut-section"
                                                            style="color: {obtenirCouleurStatut(section.status)};"
                                                        >
                                                            {obtenirTexteStatut(section.status)}
                                                        </span>
                                                    </div>
                                                {/each}
                                            </div>
                                        {:else}
                                            <p class="texte-muet p-4">{$i18n.t('Aucune section disponible')}</p>
                                        {/if}
                                    </div>
                                {/if}
                            </div>
                        {/each}
                    </div>
                {:else}
                    <p class="texte-centre texte-muet">{$i18n.t('Aucun chapitre disponible')}</p>
                {/if}
            </div>

        </div>

        <!-- BARRE D'ACTION -->
        <div class="barre-action">
            <button class="btn-primaire btn-grand" on:click={demarrerApprentissage}>
                {$i18n.t('Commencer l\'apprentissage')}
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="20" height="20">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
                </svg>
            </button>
        </div>

    </div>
{/if}

<style>
    /* ══════════════════════════════════════════════════════
       STYLES GLOBAUX - DESIGN PROPRE ET MODERNE
       ══════════════════════════════════════════════════════ */
    
    :global(body) {
        background-color: #f8fafc;
        margin: 0;
        padding: 0;
    }

    .page-conteneur {
        font-family: 'Nunito', -apple-system, BlinkMacSystemFont, sans-serif;
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
        color: #334155;
    }

    .flex-centre {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 60vh;
    }

    /* ── BOUTON RETOUR ─────────────────────────────────── */
    .btn-retour {
        background: transparent;
        border: none;
        color: #64748b;
        font-family: inherit;
        font-weight: 600;
        font-size: 0.9rem;
        cursor: pointer;
        padding: 0.5rem 0;
        margin-bottom: 1.5rem;
        transition: color 0.2s;
    }
    .btn-retour:hover {
        color: #3b82f6;
    }

    /* ── SYSTÈME DE GRILLE BENTO ───────────────────────── */
    .grille-bento {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .col-4 { grid-column: span 4; }
    .col-6 { grid-column: span 6; }
    .col-8 { grid-column: span 8; }
    .col-12 { grid-column: span 12; }

    @media (max-width: 1024px) {
        .col-4, .col-6, .col-8 { grid-column: span 12; }
    }

    /* ── CARTES ────────────────────────────────────────── */
    .carte {
        background: #ffffff;
        border-radius: 16px;
        padding: 1.75rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        border: 1px solid #e2e8f0;
        display: flex;
        flex-direction: column;
    }

    .carte-hero {
        background: linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%);
        border: 1px solid #dbeafe;
    }

    .carte-discussion {
        background: linear-gradient(135deg, #fefce8 0%, #fef9c3 100%);
        border: 1px solid #fde68a;
    }

    .centre-contenu {
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    /* ── EN-TÊTE HERO ──────────────────────────────────── */
    .en-tete-hero {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.25rem;
        flex-wrap: wrap;
        gap: 0.75rem;
    }

    .info-prof {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .avatar {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 0.85rem;
        font-weight: 700;
        color: white;
    }

    .nom-prof {
        font-size: 0.9rem;
        font-weight: 600;
        color: #475569;
    }

    .badges {
        display: flex;
        gap: 0.5rem;
    }

    .etiquette-categorie {
        background: #dbeafe;
        color: #1e40af;
        padding: 0.3rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
    }

    .etiquette-langue {
        background: #f1f5f9;
        color: #64748b;
        padding: 0.3rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .titre-cours {
        font-size: 1.75rem;
        font-weight: 800;
        color: #1e293b;
        margin: 0 0 0.75rem 0;
        line-height: 1.2;
    }

    .texte-bienvenue {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #475569;
        margin: 0 0 1.5rem 0;
    }

    /* ── STATISTIQUES ──────────────────────────────────── */
    .statistiques {
        display: flex;
        align-items: center;
        gap: 1.5rem;
        padding-top: 1.25rem;
        border-top: 1px solid #dbeafe;
    }

    .stat-item {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .stat-nombre {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1e40af;
    }

    .stat-libelle {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    .stat-separateur {
        width: 1px;
        height: 40px;
        background: #dbeafe;
    }

    /* ── CARTES STANDARD ───────────────────────────────── */
    .titre-carte {
        font-size: 1.05rem;
        font-weight: 700;
        color: #334155;
        text-align: center;
        margin: 0 0 1rem 0;
    }

    .separateur {
        border: none;
        border-top: 1px solid #e2e8f0;
        width: 60%;
        margin: 0 auto 1.25rem auto;
    }

    .texte-carte {
        font-size: 0.9rem;
        line-height: 1.6;
        color: #475569;
    }

    .texte-centre { text-align: center; }
    .texte-muet { color: #94a3b8; font-size: 0.9rem; }
    .mt-auto { margin-top: auto; }
    .mb-4 { margin-bottom: 1rem; }
    .p-4 { padding: 1rem; }

    /* ── BOUTONS ───────────────────────────────────────── */
    .btn-outline {
        background: transparent;
        border: 2px solid #cbd5e1;
        color: #475569;
        padding: 0.6rem 1.5rem;
        border-radius: 10px;
        font-weight: 700;
        font-size: 0.85rem;
        font-family: inherit;
        cursor: pointer;
        transition: all 0.2s;
    }
    .btn-outline:hover {
        border-color: #f59e0b;
        color: #d97706;
        background: #fffbeb;
    }

    .btn-primaire {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        border: none;
        padding: 0.75rem 1.75rem;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.95rem;
        font-family: inherit;
        cursor: pointer;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35);
        transition: transform 0.2s, box-shadow 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    .btn-primaire:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.45);
    }

    .btn-grand {
        padding: 1rem 2.5rem;
        font-size: 1.05rem;
    }

    .boite-erreur {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
    }

    /* ── RESSOURCES ────────────────────────────────────── */
    .liste-ressources {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .item-ressource {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.875rem;
        background: #f8fafc;
        border-radius: 10px;
        transition: background 0.2s;
    }
    .item-ressource:hover {
        background: #eff6ff;
    }

    .icone-ressource {
        color: #3b82f6;
    }

    .info-ressource {
        flex: 1;
    }

    .nom-ressource {
        font-size: 0.875rem;
        font-weight: 600;
        color: #334155;
        margin: 0 0 0.15rem 0;
    }

    .meta-ressource {
        font-size: 0.75rem;
        color: #94a3b8;
        margin: 0;
    }

    /* ── OBJECTIFS ─────────────────────────────────────── */
    .liste-objectifs {
        margin: 0;
        padding: 0 0 0 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .liste-objectifs li {
        font-size: 0.9rem;
        color: #475569;
        line-height: 1.5;
    }

    /* ── CHAPITRES ─────────────────────────────────────── */
    .liste-chapitres {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .bloc-chapitre {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden;
        transition: border-color 0.2s, box-shadow 0.2s;
    }

    .bloc-chapitre:hover {
        border-color: #93c5fd;
    }

    .en-tete-chapitre {
        display: flex;
        align-items: center;
        gap: 1rem;
        width: 100%;
        padding: 1rem 1.25rem;
        background: #f8fafc;
        border: none;
        cursor: pointer;
        text-align: left;
        font-family: inherit;
        transition: background 0.2s;
    }

    .en-tete-chapitre:hover,
    .en-tete-chapitre.developpe {
        background: #eff6ff;
    }

    .numero-chapitre {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        border-radius: 8px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 0.85rem;
        font-weight: 700;
        flex-shrink: 0;
    }

    .titre-chapitre {
        flex: 1;
        font-size: 0.95rem;
        font-weight: 600;
        color: #1e293b;
    }

    .nombre-sections {
        font-size: 0.75rem;
        font-weight: 600;
        color: #94a3b8;
        background: #f1f5f9;
        padding: 0.25rem 0.6rem;
        border-radius: 12px;
    }

    .fleche {
        color: #94a3b8;
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        flex-shrink: 0;
    }

    .fleche.tournee {
        transform: rotate(90deg);
        color: #3b82f6;
    }

    /* ── SECTIONS ──────────────────────────────────────── */
    .contenu-chapitre {
        background: #ffffff;
        border-top: 1px solid #e2e8f0;
    }

    .liste-sections {
        padding: 0.75rem 1rem 0.75rem 2.5rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .item-section {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.625rem 0.875rem;
        border-radius: 8px;
        transition: background 0.2s;
    }

    .item-section:hover {
        background: #f8fafc;
    }

    .point-section {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .titre-section {
        flex: 1;
        font-size: 0.875rem;
        color: #475569;
        font-weight: 500;
    }

    .statut-section {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }

    /* ── BARRE D'ACTION ────────────────────────────────── */
    .barre-action {
        display: flex;
        justify-content: center;
        padding-top: 0.5rem;
    }

    /* ── CHARGEUR ──────────────────────────────────────── */
    .chargeur {
        width: 44px;
        height: 44px;
        border: 4px solid #e2e8f0;
        border-top: 4px solid #3b82f6;
        border-radius: 50%;
        animation: tourner 0.8s linear infinite;
    }

    @keyframes tourner {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* ── RESPONSIVE ────────────────────────────────────── */
    @media (max-width: 640px) {
        .page-conteneur {
            padding: 1rem;
        }
        
        .titre-cours {
            font-size: 1.35rem;
        }
        
        .statistiques {
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .stat-separateur {
            display: none;
        }
        
        .en-tete-hero {
            flex-direction: column;
            align-items: flex-start;
        }
    }
</style>