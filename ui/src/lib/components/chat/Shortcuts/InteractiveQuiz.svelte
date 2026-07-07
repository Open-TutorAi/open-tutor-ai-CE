<!--
  InteractiveQuiz.svelte
  Emplacement: ui/src/lib/components/chat/Shortcuts/InteractiveQuiz.svelte
-->
<script lang="ts">
  import { createEventDispatcher, getContext } from 'svelte';
  import { get } from 'svelte/store';
  import { models, settings, user } from '$lib/stores';
  import { generateChatCompletion } from '$lib/apis/ollama';

  const dispatch = createEventDispatcher();
  const i18n: any = getContext('i18n');

  export let conversationContext: string = '';

  type Phase = 'idle' | 'loading' | 'quiz' | 'results' | 'error';
  let phase: Phase = 'idle';
  let questions: Question[] = [];
  let currentIndex = 0;
  let answers: Record<number, string> = {};
  let showExplanation = false;
  let errorMsg = '';

  interface Option { key: string; text: string; }
  interface Question {
    question: string;
    options: Option[];
    correct: string;
    explanation: string;
    recap?: string;
  }

  export async function generate(context: string) {
    phase = 'loading';
    errorMsg = '';
    questions = [];
    currentIndex = 0;
    answers = {};
    showExplanation = false;

    try {
      const currentSettings = get(settings);
      const currentModels = get(models);
      const selectedModel = currentSettings?.models?.[0] || currentModels?.[0]?.id || 'qwen2.5:1.5b';

      const currentUser = get(user);
      const token = currentUser?.token || localStorage.getItem('token')?.replace(/^"|"$/g, '') || '';

      const prompt = `Génère exactement 2 questions QCM en JSON sur ce sujet: "${context || 'algorithmique'}".
Réponds UNIQUEMENT avec du JSON valide:
{"questions":[{"question":"?","options":["A: ...","B: ...","C: ...","D: ..."],"correct":"A","explanation":"...","recap":"..."}]}`;

      const [res, controller] = await generateChatCompletion(token, {
        model: selectedModel,
        messages: [
          { role: 'system', content: 'Tu es un générateur de quiz. Réponds UNIQUEMENT en JSON valide.' },
          { role: 'user', content: prompt }
        ],
        stream: true
      });

      if (!res || !res.ok) {
        throw new Error(`Erreur serveur ${res?.status || 'inconnu'}`);
      }

      let fullText = '';
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('Impossible de lire la réponse');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split('\n')) {
          if (!line.trim()) continue;
          try {
            const parsed = JSON.parse(line);
            if (parsed?.message?.content) fullText += parsed.message.content;
            if (parsed?.done) break;
          } catch {}
        }
      }

      fullText = fullText.replace(/```json|```/g, '').trim();
      const match = fullText.match(/\{[\s\S]*\}/);
      if (!match) throw new Error('Format JSON invalide — réessayez');

      const parsed = JSON.parse(match[0]);
      if (!parsed?.questions?.length) throw new Error('Structure JSON incorrecte');

      questions = parsed.questions.map((q: any) => ({
        question: q.question || '',
        options: Array.isArray(q.options)
          ? q.options.map((opt: string, i: number) => {
              const key = String.fromCharCode(65 + i);
              const text = opt.replace(/^[A-D]:\s*/, '');
              return { key, text };
            })
          : [],
        correct: String(q.correct || 'A').toUpperCase().charAt(0),
        explanation: q.explanation || '',
        recap: q.recap || ''
      }));

      phase = 'quiz';
    } catch (e: any) {
      errorMsg = e.message || 'Erreur inconnue';
      phase = 'error';
    }
  }

  function selectAnswer(key: string) {
    if (answers[currentIndex] !== undefined) return;
    answers = { ...answers, [currentIndex]: key };
    showExplanation = true;
  }

  function nextQuestion() {
    showExplanation = false;
    if (currentIndex < questions.length - 1) {
      currentIndex++;
    } else {
      phase = 'results';
    }
  }

  function retry() {
    currentIndex = 0;
    answers = {};
    showExplanation = false;
    phase = 'quiz';
  }

  function close() {
    phase = 'idle';
    dispatch('close');
  }

  $: score = questions.filter((q, i) => answers[i] === q.correct).length;
  $: scorePct = questions.length > 0 ? Math.round((score / questions.length) * 100) : 0;
  $: currentQ = questions[currentIndex];
  $: selectedAns = answers[currentIndex];
  $: isCorrect = selectedAns === currentQ?.correct;
</script>

{#if phase !== 'idle'}
<div class="quiz-overlay" on:click|self={close} role="dialog" aria-modal="true">
  <div class="quiz-modal">

    <!-- Header -->
    <div class="quiz-header">
      <span class="quiz-title">🧠 Quiz Interactif
        {#if phase === 'quiz'}<span class="quiz-prog">Q{currentIndex+1}/{questions.length}</span>{/if}
      </span>
      <button class="quiz-close" on:click={close}>✕</button>
    </div>

    {#if phase === 'loading'}
      <div class="quiz-loading">
        <div class="spinner"></div>
        <p>🤖 Génération du quiz...</p>
        <p class="sub">Quelques secondes...</p>
      </div>

    {:else if phase === 'error'}
      <div class="quiz-error">
        <p>⚠️ {errorMsg}</p>
        <button class="btn-primary" on:click={() => generate(conversationContext)}>🔄 Réessayer</button>
        <button class="btn-secondary" on:click={close}>Fermer</button>
      </div>

    {:else if phase === 'quiz'}
      <div class="progress-bar">
        <div class="progress-fill" style="width:{((currentIndex)/questions.length)*100}%"></div>
      </div>
      <div class="quiz-body">
        <p class="q-text">{currentIndex+1}. {currentQ?.question}</p>
        <div class="options">
          {#each (currentQ?.options || []) as opt}
            {@const sel = selectedAns === opt.key}
            {@const right = opt.key === currentQ?.correct}
            {@const shown = selectedAns !== undefined}
            <button
              class="opt {shown && right ? 'opt-correct' : ''} {shown && sel && !right ? 'opt-wrong' : ''}"
              on:click={() => selectAnswer(opt.key)}
              disabled={shown}
            >
              <span class="opt-key {shown && right ? 'key-correct' : ''} {shown && sel && !right ? 'key-wrong' : ''}">{opt.key}</span>
              <span class="opt-text">{opt.text}</span>
              {#if shown && right}<span class="opt-icon">✅</span>{/if}
              {#if shown && sel && !right}<span class="opt-icon">❌</span>{/if}
            </button>
          {/each}
        </div>

        {#if showExplanation}
          <div class="expl {isCorrect ? 'expl-ok' : 'expl-ko'}">
            <strong>{isCorrect ? '🎉 Correct !' : '💡 Pas tout à fait'}</strong>
            <p>{currentQ?.explanation}</p>
            {#if !isCorrect && currentQ?.recap}<p class="recap">📚 {currentQ.recap}</p>{/if}
          </div>
          <div class="quiz-actions">
            <button class="btn-secondary" on:click={retry}>↻ Réessayer</button>
            <button class="btn-primary" on:click={nextQuestion}>
              {currentIndex < questions.length-1 ? 'Suivant →' : 'Résultats 🏆'}
            </button>
          </div>
        {/if}
      </div>

    {:else if phase === 'results'}
      <div class="results">
        <div class="score-card">
          <div class="score-num" style="color:{scorePct>=70?'#16a34a':scorePct>=40?'#ca8a04':'#dc2626'}">{score}/{questions.length}</div>
          <div class="score-pct">{scorePct}%</div>
          <div class="score-label">
            {#if scorePct>=80}🏆 Excellent !{:else if scorePct>=60}👍 Bien !{:else if scorePct>=40}📚 À revoir{:else}💪 Continue !{/if}
          </div>
        </div>
        {#each questions as q, i}
          <div class="recap-item {answers[i]===q.correct?'recap-ok':'recap-ko'}">
            <span>{answers[i]===q.correct?'✅':'❌'}</span>
            <div>
              <p class="recap-q">{q.question}</p>
              {#if answers[i]!==q.correct}
                <p class="recap-ans">Votre réponse: <strong>{answers[i]}</strong> | Correcte: <strong>{q.correct}</strong></p>
                {#if q.explanation}<p class="recap-exp">💡 {q.explanation}</p>{/if}
              {/if}
            </div>
          </div>
        {/each}
        <div class="quiz-actions">
          <button class="btn-secondary" on:click={retry}>↻ Réessayer</button>
          <button class="btn-primary" on:click={close}>✓ Terminer</button>
        </div>
      </div>
    {/if}

  </div>
</div>
{/if}
<style>
/* ── Overlay ── */
.quiz-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
:global(html.dark) .quiz-overlay {
  background: rgba(0, 0, 0, 0.6);
}

/* ── Modal ── */
.quiz-modal {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  width: 100%;
  max-width: 540px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
}
:global(html.dark) .quiz-modal {
  background: #1f2937;
  border-color: #374151;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

/* ── Header ── */
.quiz-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  border-radius: 16px 16px 0 0;
}
:global(html.dark) .quiz-header {
  background: #111827;
  border-bottom-color: #374151;
}
.quiz-title {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 8px;
}
:global(html.dark) .quiz-title {
  color: #f3f4f6;
}
.quiz-prog {
  font-size: 12px;
  background: #eff6ff;
  color: #3b82f6;
  border: 1px solid #bfdbfe;
  padding: 2px 10px;
  border-radius: 20px;
  font-weight: 600;
}
:global(html.dark) .quiz-prog {
  background: #1e3a8a;
  color: #93c5fd;
  border-color: #1d4ed8;
}
.quiz-close {
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  color: #6b7280;
  border-radius: 8px;
  width: 30px;
  height: 30px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.quiz-close:hover { background: #e5e7eb; color: #111827; }
:global(html.dark) .quiz-close {
  background: #374151;
  border-color: #4b5563;
  color: #d1d5db;
}
:global(html.dark) .quiz-close:hover {
  background: #4b5563;
  color: #f9fafb;
}

/* ── Loading ── */
.quiz-loading {
  text-align: center;
  padding: 48px 24px;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
:global(html.dark) .spinner {
  border-color: #374151;
  border-top-color: #3b82f6;
}
@keyframes spin { to { transform: rotate(360deg); } }
.quiz-loading p { font-size: 15px; color: #111827; margin: 0 0 4px; }
.quiz-loading .sub { font-size: 12px; color: #9ca3af; }
:global(html.dark) .quiz-loading p { color: #f3f4f6; }
:global(html.dark) .quiz-loading .sub { color: #6b7280; }

/* ── Error ── */
.quiz-error {
  padding: 32px 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}
.quiz-error p { color: #dc2626; font-size: 14px; }
:global(html.dark) .quiz-error p { color: #f87171; }

/* ── Progress bar ── */
.progress-bar { height: 3px; background: #e5e7eb; }
:global(html.dark) .progress-bar { background: #374151; }
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #6366f1);
  transition: width 0.4s;
}

/* ── Body ── */
.quiz-body { padding: 20px; }
.q-text {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  line-height: 1.6;
  margin: 0 0 16px;
}
:global(html.dark) .q-text { color: #f3f4f6; }

/* ── Options ── */
.options { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.opt {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  color: #374151;
  cursor: pointer;
  text-align: left;
  font-size: 14px;
  font-family: inherit;
  transition: all 0.15s;
  width: 100%;
}
:global(html.dark) .opt {
  background: #111827;
  border-color: #374151;
  color: #d1d5db;
}
.opt:not(:disabled):hover {
  border-color: #3b82f6;
  background: #eff6ff;
  color: #1d4ed8;
}
:global(html.dark) .opt:not(:disabled):hover {
  border-color: #3b82f6;
  background: #1e3a8a;
  color: #93c5fd;
}
.opt:disabled { cursor: default; }
.opt-correct { border-color: #16a34a !important; background: #f0fdf4 !important; color: #15803d !important; }
.opt-wrong   { border-color: #dc2626 !important; background: #fef2f2 !important; color: #b91c1c !important; }
:global(html.dark) .opt-correct { background: #14532d !important; color: #86efac !important; }
:global(html.dark) .opt-wrong   { background: #7f1d1d !important; color: #fca5a5 !important; }

.opt-key {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 12px;
  flex-shrink: 0;
  color: #374151;
}
:global(html.dark) .opt-key {
  background: #374151;
  color: #d1d5db;
}
.key-correct { background: #16a34a !important; color: white !important; }
.key-wrong   { background: #dc2626 !important; color: white !important; }
.opt-text { flex: 1; }
.opt-icon { margin-left: auto; flex-shrink: 0; font-size: 16px; }

/* ── Explanation ── */
.expl {
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 16px;
}
.expl-ok { background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; }
.expl-ko { background: #fffbeb; border: 1px solid #fde68a; color: #92400e; }
:global(html.dark) .expl-ok { background: #14532d; border-color: #166534; color: #86efac; }
:global(html.dark) .expl-ko { background: #451a03; border-color: #92400e; color: #fcd34d; }
.expl strong { display: block; margin-bottom: 4px; font-size: 14px; }
.expl p { margin: 0; }
.recap {
  margin-top: 6px !important;
  padding: 6px 10px;
  background: #fef3c7;
  border-radius: 6px;
  font-size: 12px;
}
:global(html.dark) .recap {
  background: #78350f;
  color: #fde68a;
}

/* ── Actions ── */
.quiz-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 4px; }
.btn-primary {
  padding: 10px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}
.btn-primary:hover { background: #2563eb; transform: translateY(-1px); }
.btn-secondary {
  padding: 10px 20px;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}
.btn-secondary:hover { background: #e5e7eb; color: #111827; }
:global(html.dark) .btn-secondary {
  background: #374151;
  border-color: #4b5563;
  color: #e5e7eb;
}
:global(html.dark) .btn-secondary:hover {
  background: #4b5563;
  color: #f9fafb;
}

/* ── Results ── */
.results { padding: 20px; }
.score-card {
  text-align: center;
  padding: 24px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  margin-bottom: 20px;
}
:global(html.dark) .score-card {
  background: #111827;
  border-color: #374151;
}
.score-num { font-size: 52px; font-weight: 900; line-height: 1; }
.score-pct { font-size: 22px; color: #6b7280; margin-top: 4px; font-weight: 600; }
.score-label { font-size: 16px; color: #374151; margin-top: 8px; }
:global(html.dark) .score-pct { color: #9ca3af; }
:global(html.dark) .score-label { color: #e5e7eb; }

.recap-item { display: flex; gap: 10px; padding: 12px 14px; border-radius: 10px; margin-bottom: 8px; }
.recap-ok { background: #f0fdf4; border: 1px solid #bbf7d0; }
.recap-ko { background: #fef2f2; border: 1px solid #fecaca; }
:global(html.dark) .recap-ok { background: #14532d; border-color: #166534; }
:global(html.dark) .recap-ko { background: #7f1d1d; border-color: #991b1b; }
.recap-q   { font-size: 13px; color: #111827; font-weight: 500; margin: 0 0 4px; }
.recap-ans { font-size: 12px; color: #6b7280; margin: 0 0 4px; }
.recap-exp { font-size: 12px; color: #92400e; margin: 0; }
:global(html.dark) .recap-q   { color: #f3f4f6; }
:global(html.dark) .recap-ans { color: #9ca3af; }
:global(html.dark) .recap-exp { color: #fcd34d; }
</style>