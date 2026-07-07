<script lang="ts">
    import { createEventDispatcher, getContext } from 'svelte';
    import { get } from 'svelte/store';
    import { user, models, settings } from '$lib/stores';
    import { generateChatCompletion } from '$lib/apis/ollama';

    const dispatch = createEventDispatcher();
    const i18n: any = getContext('i18n');

    let currentView = 'main';

    export let conversationContext: string = '';

    let quizOpen = false;
    let quizLoading = false;
    let quizError = '';
    let quizData: any = null;
    let currentQuestion = 0;
    let selectedAnswer: string | null = null;
    let answered = false;
    let score = 0;
    let quizFinished = false;

    $: understandActions = [
        { label: $i18n.t('Analogy'), prompt: $i18n.t('Explain this concept using a creative analogy from everyday life.') },
        { label: $i18n.t('Example'), prompt: $i18n.t('Give me a concrete, real-world application of this concept.') },
        { label: $i18n.t('Visual'), prompt: $i18n.t('Organize the key components into a clear Markdown table.') }
    ];

    $: difficultyLevels = [
        { label: $i18n.t('Beginner'), color: 'rgba(34,197,94,0.15)', border: 'rgba(34,197,94,0.3)', text: '#4ade80', prompt: $i18n.t('Explain using very simple language, as if I am 5 years old.') },
        { label: $i18n.t('Intermediate'), color: 'rgba(234,179,8,0.15)', border: 'rgba(234,179,8,0.3)', text: '#facc15', prompt: $i18n.t('Explain with more depth, using standard technical terms.') },
        { label: $i18n.t('Advanced'), color: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.3)', text: '#f87171', prompt: $i18n.t('Provide a deep-dive, technical explanation with nuances.') }
    ];

    function sendAction(prompt: string) {
        dispatch('submit', prompt);
        currentView = 'main';
    }

    function getToken(): string {
        try {
            const u = get(user);
            if (u?.token) return u.token;
        } catch {}
        try {
            const t = localStorage.getItem('token') || sessionStorage.getItem('token');
            if (t) return t.replace(/^"|"$/g, '');
        } catch {}
        return '';
    }

    // ── Bouton "Je n'ai pas compris" ──
    function didntUnderstand() {
        sendAction(
            "Je n'ai pas compris ce que tu viens d'expliquer. Réexplique ce concept de 3 façons différentes :\n" +
            "1) 🔁 Une analogie simple tirée de la vie quotidienne\n" +
            "2) 💡 Un exemple concret et pratique, étape par étape\n" +
            "3) 📊 Un schéma ou tableau textuel qui organise les idées\n\n" +
            "Utilise un langage simple, clair, et adapté à un étudiant débutant."
        );
    }

    async function openQuiz() {
        currentView = 'main';
        quizOpen = true;
        quizLoading = true;
        quizError = '';
        quizData = null;
        currentQuestion = 0;
        selectedAnswer = null;
        answered = false;
        score = 0;
        quizFinished = false;

        const topic = conversationContext || 'le sujet discuté dans cette conversation';

        const prompt = `Génère exactement 4 questions QCM DIFFÉRENTES sur : "${topic}".
Réponds UNIQUEMENT avec du JSON valide, sans texte avant ou après :
{"questions":[{"question":"question ?","options":["A: option","B: option","C: option","D: option"],"correct":"A","explanation":"explication","recap":"réexplication si erreur"}]}`;

        try {
            const token = getToken();
            const currentModels = get(models);
            const currentSettings = get(settings);
            const selectedModel = currentSettings?.models?.[0] || currentModels?.[0]?.id || 'qwen2.5:1.5b';

            const result = await generateChatCompletion(token, {
                model: selectedModel,
                messages: [
                    { role: 'system', content: 'Tu es un générateur de quiz. Réponds UNIQUEMENT en JSON valide.' },
                    { role: 'user', content: prompt }
                ],
                stream: false,
                options: { temperature: 0.2, num_predict: 1800 }
            });

            const [res] = Array.isArray(result) ? result : [result];

            if (!res || !res.ok) throw new Error(`Erreur ${res?.status || 'serveur'}`);

            const data = await res.json();
            let text = data?.message?.content || data?.choices?.[0]?.message?.content || data?.response || '';

            text = text.replace(/```json|```/g, '').trim();
            const start = text.indexOf('{');
            if (start === -1) throw new Error('Aucun JSON dans la réponse');

            let depth = 0, end = -1, inStr = false, esc = false;
            for (let i = start; i < text.length; i++) {
                const c = text[i];
                if (esc) { esc = false; continue; }
                if (c === '\\') { esc = true; continue; }
                if (c === '"') { inStr = !inStr; continue; }
                if (inStr) continue;
                if (c === '{') depth++;
                if (c === '}') { depth--; if (depth === 0) { end = i; break; } }
            }
            if (end === -1) throw new Error('JSON incomplet');

            let jsonStr = text.slice(start, end + 1);
            jsonStr = jsonStr.replace(/""(\w)/g, '"$1').replace(/,(\s*[}\]])/g, '$1');

            const parsed = JSON.parse(jsonStr);
            if (!parsed?.questions?.length) throw new Error('Format invalide');

            quizData = parsed;
        } catch (e: any) {
            quizError = e.message || 'Erreur de génération';
        }
        quizLoading = false;
    }

    function selectAnswer(letter: string) {
        if (answered) return;
        selectedAnswer = letter;
        answered = true;
        if (letter === quizData.questions[currentQuestion].correct) score++;
    }

    function next() {
        if (currentQuestion < quizData.questions.length - 1) {
            currentQuestion++;
            selectedAnswer = null;
            answered = false;
        } else {
            quizFinished = true;
        }
    }

    function retryQuestion() {
        selectedAnswer = null;
        answered = false;
    }

    function closeQuiz() {
        quizOpen = false;
    }

    $: question = quizData?.questions?.[currentQuestion];
    $: isCorrect = selectedAnswer === question?.correct;
</script>

<!-- Barre de raccourcis -->
<div class="shortcut-row">
    {#if currentView === 'main'}
        <button type="button" on:click={() => (currentView = 'difficulty')} class="nav-button menu-theme">
            🎚️ {$i18n.t('Difficulty')} <span class="chevron">›</span>
        </button>
        <button type="button" on:click={() => (currentView = 'understand')} class="nav-button menu-theme">
            🔍 {$i18n.t('Understand')} <span class="chevron">›</span>
        </button>
        <button type="button" on:click={didntUnderstand} class="nav-button confused-theme">
            🤔 Je n'ai pas compris
        </button>
        <button type="button" on:click={() => sendAction($i18n.t('Synthesize our conversation into 3-5 bullet points.'))} class="nav-button">
            📝 {$i18n.t('Summarize')}
        </button>
        <button type="button" on:click={() => sendAction($i18n.t('What is the most logical next concept I should learn?'))} class="nav-button">
            ⏭️ {$i18n.t('Next Step')}
        </button>
        <button type="button" on:click={openQuiz} class="nav-button quiz-theme">
            🧠 {$i18n.t('Quiz')}
        </button>
    {:else if currentView === 'difficulty'}
        <button type="button" on:click={() => (currentView = 'main')} class="nav-button back-button">⬅️ {$i18n.t('Back')}</button>
        {#each difficultyLevels as level}
            <button type="button" on:click={() => sendAction(level.prompt)} class="nav-button" style="background:{level.color};border-color:{level.border};color:{level.text}">{level.label}</button>
        {/each}
    {:else if currentView === 'understand'}
        <button type="button" on:click={() => (currentView = 'main')} class="nav-button back-button">⬅️ {$i18n.t('Back')}</button>
        {#each understandActions as action}
            <button type="button" on:click={() => sendAction(action.prompt)} class="nav-button">{action.label}</button>
        {/each}
    {/if}
</div>

<!-- Widget Quiz Interactif -->
{#if quizOpen}
<div class="overlay" on:click|self={closeQuiz}>
    <div class="modal">
        <div class="modal-header">
            <span>🧠 Quiz Interactif</span>
            <button class="close-btn" on:click={closeQuiz}>✕</button>
        </div>

        {#if quizLoading}
            <div class="loading">
                <div class="spinner"></div>
                <p>Génération du quiz...</p>
            </div>

        {:else if quizError}
            <div class="error-box">
                <p>⚠️ {quizError}</p>
                <button class="next-btn" on:click={openQuiz}>🔄 Réessayer</button>
                <button class="close-final-btn" on:click={closeQuiz}>Fermer</button>
            </div>

        {:else if quizData && !quizFinished}
            <div class="progress-bar">
                <div class="progress-fill" style="width:{(currentQuestion / quizData.questions.length) * 100}%"></div>
            </div>
            <div class="quiz-stats">
                <span>Q{currentQuestion + 1}/{quizData.questions.length}</span>
                <span class="score-good">✓ {score}</span>
                <span class="score-bad">✗ {currentQuestion - score + (answered && !isCorrect ? 1 : 0)}</span>
            </div>

            <div class="question">{question?.question}</div>

            <div class="options">
                {#each question?.options || [] as option, i}
                    {@const letter = ['A','B','C','D'][i]}
                    <button
                        class="opt"
                        class:correct={answered && letter === question.correct}
                        class:wrong={answered && selectedAnswer === letter && letter !== question.correct}
                        class:neutral={answered && letter !== selectedAnswer && letter !== question.correct}
                        on:click={() => selectAnswer(letter)}
                        disabled={answered}
                    >
                        <span class="letter">{letter}</span>
                        <span>{option.replace(/^[A-D]:\s*/, '')}</span>
                        {#if answered && letter === question.correct}<span class="icon">✓</span>{/if}
                        {#if answered && selectedAnswer === letter && letter !== question.correct}<span class="icon">✗</span>{/if}
                    </button>
                {/each}
            </div>

            {#if answered}
                {#if isCorrect}
                    <div class="feedback success">
                        <div class="feedback-title">🎉 Bonne réponse !</div>
                        <p>{question?.explanation}</p>
                        <button class="next-btn" on:click={next}>
                            {currentQuestion < quizData.questions.length - 1 ? 'Question suivante →' : 'Voir le résultat 🏆'}
                        </button>
                    </div>
                {:else}
                    <div class="feedback error-fb">
                        <div class="feedback-title">📚 Pas tout à fait — révisons !</div>
                        {#if question?.recap}
                            <p class="recap">💡 {question.recap}</p>
                        {/if}
                        <p>{question?.explanation}</p>
                        <div class="error-btns">
                            <button class="retry-small-btn" on:click={retryQuestion}>🔄 Réessayer</button>
                            <button class="next-btn" style="margin-top:0;flex:1" on:click={next}>
                                {currentQuestion < quizData.questions.length - 1 ? 'Passer →' : 'Résultat'}
                            </button>
                        </div>
                    </div>
                {/if}
            {/if}

        {:else if quizFinished}
            <div class="final">
                <div class="score-circle"
                    class:perfect={score === quizData.questions.length}
                    class:good={score >= quizData.questions.length / 2 && score < quizData.questions.length}
                    class:bad={score < quizData.questions.length / 2}>
                    {score}/{quizData.questions.length}
                </div>
                <p class="final-msg">
                    {#if score === quizData.questions.length}🏆 Parfait ! Tu as tout bon !
                    {:else if score >= quizData.questions.length / 2}👍 Bien joué ! Continue !
                    {:else}📖 Continue à réviser, tu vas y arriver !{/if}
                </p>
                <div class="final-btns">
                    <button class="next-btn" on:click={openQuiz}>🔄 Refaire le quiz</button>
                    <button class="close-final-btn" on:click={closeQuiz}>Fermer</button>
                </div>
            </div>
        {/if}
    </div>
</div>
{/if}

<style>
    /* ═══════════════════════════════════════════
       PEDAGOGICAL SHORTCUTS — MODE CLAIR FORCÉ
       ═══════════════════════════════════════════ */

    /* ── Barre de raccourcis ── */
    .shortcut-row {
        display: flex;
        flex-wrap: nowrap;
        overflow-x: auto;
        gap: 8px;
        width: 100%;
        margin-bottom: 8px;
        margin-top: 5px;
        padding-bottom: 4px;
        align-items: center;
    }
    .nav-button {
        flex: 0 0 auto;
        display: flex;
        align-items: center;
        gap: 5px;
        padding: 7px 13px;
        background: #f3f4f6;
        border: 0.5px solid #e5e7eb;
        border-radius: 20px;
        font-size: 13px;
        color: #374151;
        cursor: pointer;
        white-space: nowrap;
        transition: all 0.2s;
        font-family: inherit;
    }
    .nav-button:hover {
        filter: brightness(0.95);
        background: #e5e7eb;
    }
    .menu-theme {
        background: #eff6ff;
        border-color: #bfdbfe;
        color: #2563eb;
    }
    .quiz-theme {
        background: #f3e8ff;
        border-color: #ddd6fe;
        color: #7c3aed;
        font-weight: 500;
    }
    .confused-theme {
        background: #fff7ed;
        border-color: #fed7aa;
        color: #ea580c;
    }
    .back-button {
        background: transparent;
        border: 0.5px dashed #d1d5db;
        color: #6b7280;
    }
    .chevron {
        opacity: 0.5;
    }

    /* ── Overlay ── */
.overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.3);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px;          /* ← Réduit de 16px à 8px */
}

/* ── Modal (PLUS LARGE) ── */
.modal {
    background: #ffffff !important;
    border-radius: 16px;
    border: 1px solid #e5e7eb !important;
    width: 80vw;            /* ← 95% de la largeur écran */
    max-width: 700px;      /* ← Augmenté à 1200px */
    max-height: 90vh;       /* ← Un peu plus haut aussi */
    overflow-y: auto;
    padding: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12) !important;
    color: #111827 !important;
}

    /* ── Header ── */
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        font-size: 16px;
        font-weight: 600;
        color: #111827 !important;
    }
    .close-btn {
        background: #f3f4f6;
        border: 1px solid #e5e7eb;
        cursor: pointer;
        color: #6b7280;
        font-size: 18px;
        padding: 4px 8px;
        border-radius: 6px;
    }
    .close-btn:hover {
        background: #e5e7eb;
        color: #111827;
    }

    /* ── Loading ── */
    .loading {
        text-align: center;
        padding: 40px 20px;
        color: #6b7280;
    }
    .loading p {
        margin-top: 12px;
        font-size: 14px;
        color: #111827 !important;
    }
    .spinner {
        width: 36px;
        height: 36px;
        border: 3px solid #e5e7eb;
        border-top-color: #7c3aed;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin: 0 auto;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* ── Error ── */
    .error-box {
        padding: 20px;
        text-align: center;
        color: #dc2626;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    /* ── Progress bar ── */
    .progress-bar {
        height: 4px;
        background: #e5e7eb;
        border-radius: 4px;
        margin-bottom: 10px;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        background: #7c3aed;
        border-radius: 4px;
        transition: width 0.3s;
    }

    /* ── Stats ── */
    .quiz-stats {
        display: flex;
        gap: 12px;
        font-size: 13px;
        color: #6b7280;
        margin-bottom: 16px;
    }
    .score-good {
        color: #16a34a;
        font-weight: 600;
    }
    .score-bad {
        color: #dc2626;
        font-weight: 600;
    }

    /* ── Question ── */
    .question {
        font-size: 15px;
        font-weight: 500;
        color: #111827 !important;
        margin-bottom: 14px;
        line-height: 1.6;
    }

    /* ── Options ── */
    .options {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .opt {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 14px;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        color: #374151;
        font-size: 14px;
        text-align: left;
        cursor: pointer;
        transition: all 0.15s;
        width: 100%;
        font-family: inherit;
    }
    .opt:hover:not(:disabled) {
        border-color: #7c3aed;
        background: #f3e8ff;
    }
    /* Bonne réponse — VERT plus visible */
.opt.correct {
    background: #dcfce7 !important;        /* vert clair */
    border-color: #16a34a !important;      /* vert bordure */
    color: #14532d !important;             /* vert foncé texte */
    box-shadow: 0 0 0 2px #16a34a;         /* halo vert */
}

/* Mauvaise réponse — ROUGE plus visible */
.opt.wrong {
    background: #fee2e2 !important;        /* rouge clair */
    border-color: #dc2626 !important;      /* rouge bordure */
    color: #7f1d1d !important;             /* rouge foncé texte */
    box-shadow: 0 0 0 2px #dc2626;         /* halo rouge */
}
    .opt.neutral {
        opacity: 0.4;
    }
    .opt:disabled {
        cursor: default;
    }
    .letter {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        border: 1px solid currentColor;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
        flex-shrink: 0;
    }
    .icon {
        margin-left: auto;
        font-weight: 700;
    }

    /* ── Feedback ── */
    .feedback {
        margin-top: 14px;
        padding: 14px;
        border-radius: 10px;
        font-size: 13px;
        line-height: 1.6;
    }
    .feedback.success {
        background: #f0fdf4;
        border: 0.5px solid #bbf7d0;
        color: #15803d;
    }
    .feedback.error-fb {
        background: #fffbeb;
        border: 0.5px solid #fde68a;
        color: #92400e;
    }
    .feedback-title {
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 8px;
    }
    .recap {
        background: #fef3c7;
        border-radius: 6px;
        padding: 8px 10px;
        margin-bottom: 8px;
        border-left: 3px solid #dc2626;
        color: #92400e;
    }

    /* ── Boutons ── */
    .next-btn {
        margin-top: 12px;
        padding: 10px 20px;
        background: #7c3aed;
        border: none;
        border-radius: 10px;
        color: white;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        font-family: inherit;
        transition: background 0.15s;
    }
    .next-btn:hover {
        background: #6d28d9;
    }
    .error-btns {
        display: flex;
        gap: 8px;
        margin-top: 12px;
    }
    .retry-small-btn {
        flex: 1;
        padding: 10px;
        border: 0.5px solid #dc2626;
        border-radius: 10px;
        background: transparent;
        color: #dc2626;
        font-size: 13px;
        cursor: pointer;
        font-family: inherit;
    }

    /* ── Final ── */
    .final {
        text-align: center;
        padding: 20px 0;
    }
    .score-circle {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        font-weight: 800;
        margin: 0 auto 16px;
        border: 3px solid;
    }
    .score-circle.perfect {
        border-color: #16a34a;
        color: #16a34a;
        background: #f0fdf4;
    }
    .score-circle.good {
        border-color: #ca8a04;
        color: #ca8a04;
        background: #fefce8;
    }
    .score-circle.bad {
        border-color: #dc2626;
        color: #dc2626;
        background: #fef2f2;
    }
    .final-msg {
        font-size: 16px;
        color: #111827 !important;
        margin-bottom: 20px;
    }
    .final-btns {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .close-final-btn {
        padding: 10px;
        border: 0.5px solid #e5e7eb;
        border-radius: 10px;
        background: #f3f4f6;
        color: #6b7280;
        cursor: pointer;
        font-size: 13px;
        font-family: inherit;
    }
    .close-final-btn:hover {
        background: #e5e7eb;
        color: #111827;
    }
</style>