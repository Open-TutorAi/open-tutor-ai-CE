import type { ErrorCard } from '$lib/apis/supports/error-cards';

function formatDate(iso: string | null): string {
    if (!iso) return '';
    try {
        return new Date(iso).toLocaleString('fr-FR', {
            day: '2-digit', month: 'short',
            hour: '2-digit', minute: '2-digit'
        });
    } catch { return iso; }
}

export function exportErrorCardsToPdf(cards: ErrorCard[]): void {
    const isDark = document.documentElement.classList.contains('dark');
    const date = new Date().toLocaleString('fr-FR', {
        day: '2-digit', month: 'long', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });

    const bg        = isDark ? '#111827' : '#fffbeb';
    const surface   = isDark ? '#1f2937' : '#ffffff';
    const border    = isDark ? '#374151' : '#e5e7eb';
    const text      = isDark ? '#f9fafb' : '#111827';
    const textMuted = isDark ? '#9ca3af' : '#6b7280';
    const textBody  = isDark ? '#e5e7eb' : '#374151';
    const codeBg    = isDark ? '#0f172a'  : '#f3f4f6';
    const codeText  = isDark ? '#e5e7eb' : '#1f2937';
    const amber     = '#f59e0b';
    const amberDark = '#b45309';

    const rows = cards.map((card, i) => [
        '<div class="card">',
        '  <div class="card-header">',
        `    <span class="num">${i + 1}</span>`,
        `    <span class="concept">${card.concept}</span>`,
        card.created_at ? `    <span class="date">${formatDate(card.created_at)}</span>` : '',
        '  </div>',
        '  <div class="section"><div class="label">&#x26A0;&#xFE0F; Erreur</div>',
        `    <p>${card.error_description}</p></div>`,
        '  <div class="section"><div class="label">&#x1F4A1; Explication</div>',
        `    <p>${card.simple_explanation}</p></div>`,
        '  <div class="section"><div class="label">&#x2705; Exemple correct</div>',
        `    <pre>${card.correct_example}</pre></div>`,
        '</div>',
    ].join('\n')).join('\n');

    const count = cards.length;
    const plural = count > 1;

    const css = [
        '* { box-sizing: border-box; margin: 0; padding: 0; }',
        `body { font-family: ui-sans-serif, system-ui, sans-serif; background: ${bg}; color: ${text}; padding: 2cm 2cm; font-size: 10.5pt; }`,
        `header { border-bottom: 3px solid ${amber}; padding-bottom: .75rem; margin-bottom: 1.5rem; }`,
        `header h1 { font-size: 17pt; color: ${amberDark}; font-weight: 800; }`,
        `header p { font-size: 9pt; color: ${textMuted}; margin-top: .3rem; }`,
        `.card { background: ${surface}; border: 1px solid ${border}; border-left: 4px solid ${amber}; border-radius: 8px; padding: .9rem 1rem; margin-bottom: 1.1rem; page-break-inside: avoid; }`,
        `.card-header { display: flex; align-items: center; gap: .55rem; margin-bottom: .65rem; }`,
        `.num { background: ${amber}; color: #fff; border-radius: 50%; width: 22px; height: 22px; font-size: 9pt; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }`,
        `.concept { font-size: 11.5pt; font-weight: 700; color: ${text}; flex: 1; }`,
        `.date { font-size: 8pt; color: ${textMuted}; white-space: nowrap; }`,
        `.section { margin-top: .45rem; }`,
        `.label { font-size: 8pt; font-weight: 700; color: ${textMuted}; margin-bottom: .2rem; letter-spacing: .02em; }`,
        `p { font-size: 9.5pt; line-height: 1.55; color: ${textBody}; }`,
        `pre { font-family: Menlo, monospace; font-size: 8.5pt; background: ${codeBg}; color: ${codeText}; padding: .45rem .6rem; border-radius: 5px; white-space: pre-wrap; word-break: break-word; line-height: 1.4; }`,
        `footer { margin-top: 2rem; border-top: 1px solid ${border}; padding-top: .5rem; font-size: 8pt; color: ${textMuted}; text-align: center; }`,
        '@page { margin: 0; }',
        '@media print { body { padding: 1.5cm; } }',
    ].join('\n');

    const html = [
        '<!DOCTYPE html>',
        '<html lang="fr">',
        '<head>',
        '<meta charset="UTF-8"/>',
        `<title>Rapport d'erreurs</title>`,
        `<style>${css}</style>`,
        '</head>',
        '<body>',
        '<header>',
        `<h1>&#x1F4DA; Rapport d'erreurs</h1>`,
        `<p>${count} erreur${plural ? 's' : ''} détectée${plural ? 's' : ''} — exporté le ${date}</p>`,
        '</header>',
        rows,
        '<footer>Généré par Open TutorAI</footer>',
        '<script>window.onload=function(){window.print();}<\/script>',
        '</body>',
        '</html>',
    ].join('\n');

    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const win = window.open(url, '_blank');
    if (win) {
        win.onafterprint = () => URL.revokeObjectURL(url);
    } else {
        URL.revokeObjectURL(url);
    }
}
