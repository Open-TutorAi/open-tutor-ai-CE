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

  type Phase = 'idle' | 'loading' | 'quiz' | 'results';
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

      // Lire le stream et accumuler le texte
      let fullText = '';
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('Impossible de lire la réponse');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        // Parser les lignes JSON du stream Ollama
        for (const line of chunk.split('\n')) {
          if (!line.trim()) continue;
          try {
            const parsed = JSON.parse(line);
            if (parsed?.message?.content) {
              fullText += parsed.message.content;
            }
            if (parsed?.done) break;
          } catch {}
        }
      }

      // Nettoyer et parser le JSON
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
          <div class="score-num" style="color:{scorePct>=70?'#4ade80':scorePct>=40?'#facc15':'#f87171'}">{score}/{questions.length}</div>
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
.quiz-overlay{position:fixed;inset:0;background:rgba(0,0,0,.55);backdrop-filter:blur(4px);z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px}
.quiz-modal{background:#1a1f2e;border:1px solid rgba(255,255,255,.1);border-radius:20px;width:100%;max-width:540px;max-height:85vh;overflow-y:auto;box-shadow:0 24px 64px rgba(0,0,0,.5);display:flex;flex-direction:column}
.quiz-header{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid rgba(255,255,255,.08)}
.quiz-title{font-size:16px;font-weight:700;color:#e2e8f0;display:flex;align-items:center;gap:10px}
.quiz-prog{font-size:12px;background:rgba(59,130,246,.2);color:#60a5fa;border:1px solid rgba(59,130,246,.3);padding:2px 10px;border-radius:20px}
.quiz-close{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.1);color:#94a3b8;border-radius:8px;width:30px;height:30px;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center}
.quiz-close:hover{background:rgba(255,255,255,.15);color:#e2e8f0}
.quiz-loading{text-align:center;padding:48px 24px;color:#94a3b8}
.spinner{width:40px;height:40px;border:3px solid rgba(255,255,255,.1);border-top-color:#60a5fa;border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 16px}
@keyframes spin{to{transform:rotate(360deg)}}
.quiz-loading p{font-size:15px;color:#e2e8f0;margin:0 0 4px}
.quiz-loading .sub{font-size:12px;color:#64748b}
.quiz-error{padding:32px 24px;text-align:center;display:flex;flex-direction:column;gap:12px;align-items:center}
.quiz-error p{color:#f87171;font-size:14px}
.progress-bar{height:3px;background:rgba(255,255,255,.08)}
.progress-fill{height:100%;background:linear-gradient(90deg,#3b82f6,#8b5cf6);transition:width .4s}
.quiz-body{padding:20px}
.q-text{font-size:15px;font-weight:600;color:#e2e8f0;line-height:1.6;margin:0 0 16px}
.options{display:flex;flex-direction:column;gap:8px;margin-bottom:16px}
.opt{display:flex;align-items:center;gap:12px;padding:12px 16px;border-radius:12px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);color:#cbd5e1;cursor:pointer;text-align:left;font-size:14px;font-family:inherit;transition:all .15s;width:100%}
.opt:not(:disabled):hover{border-color:rgba(99,102,241,.5);background:rgba(99,102,241,.1);color:#e2e8f0}
.opt:disabled{cursor:default}
.opt-correct{border-color:rgba(74,222,128,.5)!important;background:rgba(74,222,128,.1)!important;color:#4ade80!important}
.opt-wrong{border-color:rgba(248,113,113,.5)!important;background:rgba(248,113,113,.1)!important;color:#f87171!important}
.opt-key{width:28px;height:28px;border-radius:8px;background:rgba(255,255,255,.08);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;flex-shrink:0}
.key-correct{background:#4ade80!important;color:#052e16!important}
.key-wrong{background:#f87171!important;color:#1a0505!important}
.opt-text{flex:1}
.opt-icon{margin-left:auto;flex-shrink:0;font-size:16px}
.expl{padding:12px 16px;border-radius:10px;font-size:13px;line-height:1.6;margin-bottom:16px}
.expl-ok{background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.2);color:#86efac}
.expl-ko{background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.2);color:#fde68a}
.expl strong{display:block;margin-bottom:4px}
.expl p{margin:0}
.recap{margin-top:6px!important;padding:6px 10px;background:rgba(251,191,36,.1);border-radius:6px}
.quiz-actions{display:flex;gap:10px;justify-content:flex-end}
.btn-primary{padding:10px 20px;background:linear-gradient(135deg,#3b82f6,#6366f1);color:white;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit;transition:all .15s}
.btn-primary:hover{filter:brightness(1.1);transform:translateY(-1px)}
.btn-secondary{padding:10px 20px;background:rgba(255,255,255,.08);color:#94a3b8;border:1px solid rgba(255,255,255,.1);border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit;transition:all .15s}
.btn-secondary:hover{background:rgba(255,255,255,.12);color:#e2e8f0}
.results{padding:20px}
.score-card{text-align:center;padding:24px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:16px;margin-bottom:20px}
.score-num{font-size:52px;font-weight:900;line-height:1}
.score-pct{font-size:22px;color:#64748b;margin-top:4px;font-weight:600}
.score-label{font-size:16px;color:#94a3b8;margin-top:8px}
.recap-item{display:flex;gap:10px;padding:12px 14px;border-radius:10px;margin-bottom:8px}
.recap-ok{background:rgba(74,222,128,.06);border:1px solid rgba(74,222,128,.15)}
.recap-ko{background:rgba(248,113,113,.06);border:1px solid rgba(248,113,113,.15)}
.recap-q{font-size:13px;color:#e2e8f0;font-weight:500;margin:0 0 4px}
.recap-ans{font-size:12px;color:#94a3b8;margin:0 0 4px}
.recap-exp{font-size:12px;color:#fde68a;margin:0}
</style>