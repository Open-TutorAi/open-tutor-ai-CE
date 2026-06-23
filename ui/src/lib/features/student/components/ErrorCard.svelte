<script lang="ts">
    import type { ErrorCard } from '$lib/apis/supports/error-cards';

    export let card: ErrorCard;
    export let onDelete: ((id: string) => void) | null = null;

    let expanded = true;

    function formatDate(iso: string | null): string {
        if (!iso) return '';
        try {
            return new Date(iso).toLocaleString('fr-FR', {
                day: '2-digit',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return iso;
        }
    }
</script>

<article class="error-card">
    <header class="card-header">
        <span class="concept-badge" title={card.concept}>
            {card.concept}
        </span>

        <div class="actions">
            <button
                type="button"
                class="icon-btn"
                on:click={() => (expanded = !expanded)}
                aria-label={expanded ? 'Replier la fiche' : 'Déplier la fiche'}
                title={expanded ? 'Replier' : 'Déplier'}
            >
                {#if expanded}
                    <!-- chevron up -->
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>
                {:else}
                    <!-- chevron down -->
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
                {/if}
            </button>

            {#if onDelete}
                <button
                    type="button"
                    class="icon-btn danger"
                    on:click={() => onDelete?.(card.id)}
                    aria-label="Supprimer la fiche"
                    title="Supprimer"
                >
                    <!-- trash -->
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                        <path d="M10 11v6M14 11v6"/>
                        <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                    </svg>
                </button>
            {/if}
        </div>
    </header>

    {#if expanded}
        <section class="block error-block">
            <div class="block-label">⚠️ Erreur détectée</div>
            <p class="block-content">{card.error_description}</p>
        </section>

        <section class="block">
            <div class="block-label">💡 Explication</div>
            <p class="block-content">{card.simple_explanation}</p>
        </section>

        <section class="block">
            <div class="block-label">✅ Exemple correct</div>
            <pre class="block-code">{card.correct_example}</pre>
        </section>

        {#if card.created_at}
            <footer class="card-footer">
                Créée le {formatDate(card.created_at)}
            </footer>
        {/if}
    {/if}
</article>

<style>
    .error-card {
        border: 1px solid rgb(229, 231, 235);
        border-left: 4px solid rgb(245, 158, 11);
        border-radius: 0.5rem;
        padding: 0.875rem 1rem;
        margin-bottom: 0.75rem;
        background: rgb(255, 251, 235);
        transition: box-shadow 0.15s ease;
    }
    .error-card:hover {
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    :global(.dark) .error-card {
        background: rgba(245, 158, 11, 0.08);
        border-color: rgb(55, 65, 81);
        border-left-color: rgb(245, 158, 11);
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.625rem;
    }

    .concept-badge {
        display: inline-block;
        background: rgb(245, 158, 11);
        color: white;
        padding: 0.25rem 0.625rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
        line-height: 1.2;
        max-width: 260px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .actions {
        display: flex;
        gap: 0.25rem;
        flex-shrink: 0;
    }

    .icon-btn {
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 0.25rem;
        border-radius: 0.25rem;
        color: rgb(107, 114, 128);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: background 0.15s ease, color 0.15s ease;
    }
    .icon-btn:hover {
        background: rgba(0, 0, 0, 0.05);
        color: rgb(31, 41, 55);
    }
    .icon-btn.danger:hover {
        color: rgb(220, 38, 38);
    }
    :global(.dark) .icon-btn { color: rgb(156, 163, 175); }
    :global(.dark) .icon-btn:hover {
        background: rgba(255, 255, 255, 0.08);
        color: rgb(229, 231, 235);
    }

    .block {
        margin: 0.5rem 0;
    }

    .block-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: rgb(75, 85, 99);
        margin-bottom: 0.25rem;
    }
    :global(.dark) .block-label { color: rgb(209, 213, 219); }

    .block-content {
        margin: 0;
        font-size: 0.875rem;
        line-height: 1.5;
        color: rgb(31, 41, 55);
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    :global(.dark) .block-content { color: rgb(229, 231, 235); }

    .block-code {
        margin: 0;
        font-size: 0.825rem;
        line-height: 1.45;
        color: rgb(31, 41, 55);
        background: rgb(243, 244, 246);
        padding: 0.5rem 0.625rem;
        border-radius: 0.375rem;
        white-space: pre-wrap;
        word-wrap: break-word;
        font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
        overflow-x: auto;
    }
    :global(.dark) .block-code {
        background: rgba(0, 0, 0, 0.3);
        color: rgb(229, 231, 235);
    }

    .card-footer {
        font-size: 0.72rem;
        color: rgb(156, 163, 175);
        margin-top: 0.5rem;
        text-align: right;
    }
</style>
