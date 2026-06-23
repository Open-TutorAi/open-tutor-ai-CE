<script lang="ts">
    import { onMount } from 'svelte';
    import {
        listErrorCards,
        deleteErrorCard,
        type ErrorCard as ErrorCardType
    } from '$lib/apis/supports/error-cards';
    import { exportErrorCardsToPdf } from './exportErrorCardsPdf';

    export let supportId: string;
    export let token: string;

    let cards: ErrorCardType[] = [];
    let loading = true;
    let errorMsg: string | null = null;
    let expanded = true;

    export async function refresh(): Promise<void> {
        if (!supportId || !token) return;
        loading = true;
        errorMsg = null;
        try {
            cards = await listErrorCards(token, supportId);
        } catch (err) {
            errorMsg = err instanceof Error ? err.message : 'Erreur de chargement';
        } finally {
            loading = false;
        }
    }

    export function addCard(card: ErrorCardType): void {
        if (cards.some((c) => c.id === card.id)) return;
        cards = [...cards, card];
    }

    async function handleDelete(cardId: string): Promise<void> {
        const ok = await deleteErrorCard(token, supportId, cardId);
        if (ok) cards = cards.filter((c) => c.id !== cardId);
    }

    function formatDate(iso: string | null): string {
        if (!iso) return '';
        try {
            return new Date(iso).toLocaleString('fr-FR', {
                day: '2-digit', month: 'short',
                hour: '2-digit', minute: '2-digit'
            });
        } catch { return iso; }
    }

    onMount(() => { refresh(); });
</script>

<aside class="report-card">
    <!-- En-tête de la fiche -->
    <div class="report-header" on:click={() => (expanded = !expanded)} role="button" tabindex="0"
         on:keydown={(e) => e.key === 'Enter' && (expanded = !expanded)}>
        <div class="report-title">
            <span class="report-icon">📚</span>
            <div>
                <h3>Rapport d'erreurs</h3>
                <p class="report-subtitle">Générées automatiquement depuis tes échanges</p>
            </div>
        </div>
        <div class="report-meta">
            {#if !loading && cards.length > 0}
                <span class="badge">{cards.length} erreur{cards.length > 1 ? 's' : ''}</span>
                <button
                    class="export-btn"
                    on:click|stopPropagation={() => exportErrorCardsToPdf(cards)}
                    title="Télécharger en PDF"
                    aria-label="Exporter le rapport en PDF"
                >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                    PDF
                </button>
            {/if}
            <svg class="chevron {expanded ? 'up' : ''}" width="16" height="16"
                 viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                 stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"/>
            </svg>
        </div>
    </div>

    <!-- Corps de la fiche -->
    {#if expanded}
        <div class="report-body">
            {#if loading}
                <div class="state-row">
                    <div class="spinner"></div>
                    <span>Chargement…</span>
                </div>
            {:else if errorMsg}
                <div class="state-error">{errorMsg}</div>
            {:else if cards.length === 0}
                <div class="state-empty">
                    <span class="empty-icon">📝</span>
                    <p>Aucune erreur détectée pour l'instant.</p>
                    <p class="hint">Continue à discuter avec ton tuteur — les difficultés de compréhension apparaîtront ici automatiquement.</p>
                </div>
            {:else}
                <div class="errors-list">
                    {#each cards as card, i (card.id)}
                        <div class="error-item">
                            <!-- Numéro + concept -->
                            <div class="error-item-header">
                                <span class="error-num">{i + 1}</span>
                                <span class="error-concept">{card.concept}</span>
                                <button class="delete-btn" on:click={() => handleDelete(card.id)}
                                        title="Supprimer" aria-label="Supprimer cette erreur">
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                                         stroke="currentColor" stroke-width="2.5"
                                         stroke-linecap="round" stroke-linejoin="round">
                                        <polyline points="3 6 5 6 21 6"/>
                                        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                                        <path d="M10 11v6M14 11v6"/>
                                        <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                                    </svg>
                                </button>
                            </div>

                            <!-- Détails -->
                            <div class="error-detail">
                                <div class="detail-label">⚠️ Erreur</div>
                                <p class="detail-text">{card.error_description}</p>
                            </div>
                            <div class="error-detail">
                                <div class="detail-label">💡 Explication</div>
                                <p class="detail-text">{card.simple_explanation}</p>
                            </div>
                            <div class="error-detail">
                                <div class="detail-label">✅ Exemple correct</div>
                                <pre class="detail-code">{card.correct_example}</pre>
                            </div>

                            {#if card.created_at}
                                <div class="error-date">{formatDate(card.created_at)}</div>
                            {/if}

                            {#if i < cards.length - 1}
                                <hr class="error-divider" />
                            {/if}
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    {/if}
</aside>

<style>
    .report-card {
        border: 1px solid rgb(229, 231, 235);
        border-left: 4px solid rgb(245, 158, 11);
        border-radius: 0.625rem;
        background: rgb(255, 251, 235);
        overflow: hidden;
    }
    :global(.dark) .report-card {
        background: rgba(245, 158, 11, 0.07);
        border-color: rgb(55, 65, 81);
        border-left-color: rgb(245, 158, 11);
    }

    /* En-tête cliquable */
    .report-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.875rem 1rem;
        cursor: pointer;
        user-select: none;
        gap: 0.5rem;
    }
    .report-header:hover { background: rgba(245, 158, 11, 0.06); }

    .report-title {
        display: flex;
        align-items: center;
        gap: 0.625rem;
    }
    .report-icon { font-size: 1.25rem; }

    h3 {
        margin: 0;
        font-size: 0.95rem;
        font-weight: 700;
        color: rgb(17, 24, 39);
    }
    :global(.dark) h3 { color: rgb(243, 244, 246); }

    .report-subtitle {
        margin: 0;
        font-size: 0.75rem;
        color: rgb(107, 114, 128);
        line-height: 1.3;
    }
    :global(.dark) .report-subtitle { color: rgb(156, 163, 175); }

    .report-meta {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-shrink: 0;
    }

    .badge {
        background: rgb(245, 158, 11);
        color: white;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: 9999px;
        white-space: nowrap;
    }

    .export-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: rgb(245, 158, 11);
        color: white;
        border: none;
        border-radius: 0.375rem;
        padding: 0.25rem 0.6rem;
        font-size: 0.72rem;
        font-weight: 700;
        cursor: pointer;
        transition: background 0.15s, opacity 0.15s;
        white-space: nowrap;
    }
    .export-btn:hover { background: rgb(217, 119, 6); }
    .export-btn:active { opacity: 0.8; }

    .chevron {
        color: rgb(107, 114, 128);
        transition: transform 0.2s ease;
    }
    .chevron.up { transform: rotate(180deg); }

    /* Corps */
    .report-body {
        border-top: 1px solid rgb(229, 231, 235);
        max-height: 520px;
        overflow-y: auto;
        padding: 1rem;
    }
    :global(.dark) .report-body { border-top-color: rgb(55, 65, 81); }

    /* États */
    .state-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: rgb(107, 114, 128);
        font-size: 0.875rem;
        padding: 0.5rem 0;
    }
    .state-error {
        color: rgb(220, 38, 38);
        font-size: 0.875rem;
        padding: 0.75rem;
        background: rgb(254, 242, 242);
        border-radius: 0.375rem;
    }
    .state-empty {
        text-align: center;
        padding: 1.5rem 0.5rem;
        color: rgb(107, 114, 128);
    }
    .empty-icon { font-size: 1.75rem; display: block; margin-bottom: 0.5rem; opacity: 0.6; }
    .state-empty p { margin: 0.2rem 0; font-size: 0.875rem; }
    .hint { font-size: 0.78rem; line-height: 1.5; margin-top: 0.4rem !important; }

    /* Liste des erreurs */
    .errors-list { display: flex; flex-direction: column; }

    .error-item { padding: 0.25rem 0; }

    .error-item-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.625rem;
    }

    .error-num {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: rgb(245, 158, 11);
        color: white;
        font-size: 0.7rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .error-concept {
        flex: 1;
        font-weight: 700;
        font-size: 0.875rem;
        color: rgb(17, 24, 39);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    :global(.dark) .error-concept { color: rgb(243, 244, 246); }

    .delete-btn {
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 0.2rem;
        border-radius: 0.25rem;
        color: rgb(156, 163, 175);
        display: flex;
        align-items: center;
        flex-shrink: 0;
        transition: color 0.15s;
    }
    .delete-btn:hover { color: rgb(220, 38, 38); }

    .error-detail { margin: 0.375rem 0; }

    .detail-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: rgb(107, 114, 128);
        margin-bottom: 0.2rem;
    }
    :global(.dark) .detail-label { color: rgb(156, 163, 175); }

    .detail-text {
        margin: 0;
        font-size: 0.83rem;
        line-height: 1.5;
        color: rgb(31, 41, 55);
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    :global(.dark) .detail-text { color: rgb(229, 231, 235); }

    .detail-code {
        margin: 0;
        font-size: 0.78rem;
        line-height: 1.45;
        background: rgb(243, 244, 246);
        padding: 0.4rem 0.5rem;
        border-radius: 0.25rem;
        white-space: pre-wrap;
        word-wrap: break-word;
        font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
    }
    :global(.dark) .detail-code {
        background: rgba(0, 0, 0, 0.25);
        color: rgb(229, 231, 235);
    }

    .error-date {
        font-size: 0.7rem;
        color: rgb(156, 163, 175);
        text-align: right;
        margin-top: 0.375rem;
    }

    .error-divider {
        border: none;
        border-top: 1px dashed rgb(229, 231, 235);
        margin: 0.75rem 0;
    }
    :global(.dark) .error-divider { border-top-color: rgb(55, 65, 81); }

    .spinner {
        width: 14px; height: 14px;
        border: 2px solid rgb(229, 231, 235);
        border-top-color: rgb(107, 114, 128);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        flex-shrink: 0;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
</style>
