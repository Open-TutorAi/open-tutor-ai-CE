<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { toast } from 'svelte-sonner';
	import { TUTOR_API_BASE_URL } from '$lib/constants';

	let evaluation: any = null;
	let loading = true;
	let submitting = false;
	let submitted = false;
	let results: any = null;
	let answers: Record<string, string> = {};
	let currentQ = 0;

	$: evalId = $page.params.id;

	onMount(async () => {
		if (!browser) return;
		const token = localStorage.getItem('token');
		if (!token) { goto('/auth'); return; }
		try {
			const res = await fetch(`${TUTOR_API_BASE_URL}/parent/evaluations/${evalId}`, {
				headers: { authorization: `Bearer ${token}` }
			});
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			evaluation = await res.json();
			if (evaluation.status === 'completed') {
				submitted = true;
				results = evaluation;
				answers = evaluation.student_answers ?? {};
			}
		} catch (e: any) {
			toast.error(e.message);
		} finally {
			loading = false;
		}
	});

	async function submitAnswers() {
		const token = localStorage.getItem('token');
		if (!token) return;
		submitting = true;
		try {
			const res = await fetch(`${TUTOR_API_BASE_URL}/parent/evaluations/${evalId}/submit`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json', authorization: `Bearer ${token}` },
				body: JSON.stringify({ answers })
			});
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			results = await res.json();
			submitted = true;
			toast.success(`Score : ${results.score}/100 🎉`);
		} catch (e: any) {
			toast.error(e.message);
		} finally {
			submitting = false;
		}
	}

	$: progress = evaluation ? Math.round((Object.keys(answers).length / evaluation.questions.length) * 100) : 0;
	$: allAnswered = evaluation ? Object.keys(answers).length === evaluation.questions.length : false;
	$: scoreColor = results ? (results.score >= 80 ? '#16A34A' : results.score >= 60 ? '#D97706' : '#DC2626') : '#2563EB';
</script>

<!-- BREADCRUMB -->
<div style="display:flex;align-items:center;gap:8px;margin-bottom:20px;font-size:13px;color:#6B7280;">
	<a href="/parent/evaluations" style="color:#2563EB;text-decoration:none;">← Évaluations</a>
	<span>/</span>
	<span>{evaluation?.title ?? 'Chargement...'}</span>
</div>

{#if loading}
	<div style="display:flex;align-items:center;justify-content:center;height:300px;color:#6B7280;gap:10px;">
		<div style="width:24px;height:24px;border:3px solid #2563EB;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;"></div>
		Chargement de l'évaluation...
	</div>

{:else if !evaluation}
	<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:48px;text-align:center;">
		<div style="font-size:40px;margin-bottom:12px;">❌</div>
		<h3 style="font-weight:600;">Évaluation introuvable</h3>
		<a href="/parent/evaluations" style="color:#2563EB;">← Retour</a>
	</div>

{:else if submitted && results}
	<!-- ═══ RÉSULTATS ═══ -->
	<div style="background:linear-gradient(135deg,#1E3A8A,#2563EB);border-radius:10px;padding:28px;color:#fff;text-align:center;margin-bottom:20px;">
		<div style="font-size:64px;font-weight:900;line-height:1;">{results.score}</div>
		<div style="font-size:18px;opacity:.8;margin-top:4px;">/ 100</div>
		<div style="font-size:16px;margin-top:12px;">{results.nb_correct}/{results.nb_total} questions correctes</div>
		<div style="font-size:14px;opacity:.8;margin-top:4px;">
			{results.score >= 80 ? '🎉 Excellent !' : results.score >= 60 ? '👍 Bien !' : '💪 À retravailler'}
		</div>
	</div>

	<!-- DÉTAIL DES QUESTIONS -->
	<div style="display:flex;flex-direction:column;gap:12px;">
		{#each (results.results ?? evaluation.questions) as q, i}
			{@const isCorrect = results.results ? q.is_correct : null}
			<div style="background:#fff;border:1px solid {isCorrect === true ? '#BBF7D0' : isCorrect === false ? '#FECACA' : '#E5E7EB'};border-radius:8px;overflow:hidden;">
				<div style="padding:14px 18px;border-bottom:1px solid #F3F4F6;display:flex;align-items:flex-start;gap:12px;">
					<div style="width:28px;height:28px;border-radius:50%;background:{isCorrect === true ? '#16A34A' : isCorrect === false ? '#DC2626' : '#6B7280'};color:#fff;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">{i+1}</div>
					<div style="font-size:14px;font-weight:600;color:#111827;flex:1;">{q.question}</div>
					{#if isCorrect !== null}
						<span style="font-size:16px;">{isCorrect ? '✅' : '❌'}</span>
					{/if}
				</div>
				<div style="padding:14px 18px;display:grid;grid-template-columns:1fr 1fr;gap:8px;">
					{#each Object.entries(q.choices ?? {}) as [key, choice]}
						{@const isAnswer = answers[String(q.id)] === key}
						{@const isRight = q.correct === key}
						<div style="padding:8px 12px;border-radius:6px;font-size:13px;display:flex;align-items:center;gap:8px;
							background:{isRight ? '#D1FAE5' : isAnswer && !isRight ? '#FEE2E2' : '#F9FAFB'};
							border:1px solid {isRight ? '#6EE7B7' : isAnswer && !isRight ? '#FECACA' : '#E5E7EB'};">
							<span style="font-weight:700;color:{isRight ? '#16A34A' : isAnswer && !isRight ? '#DC2626' : '#6B7280'};">{key}</span>
							<span style="color:#374151;">{choice}</span>
						</div>
					{/each}
				</div>
				{#if q.explanation}
					<div style="padding:10px 18px;background:#F0FDF4;border-top:1px solid #BBF7D0;font-size:12px;color:#15803D;">
						💡 {q.explanation}
					</div>
				{/if}
			</div>
		{/each}
	</div>

	<div style="margin-top:16px;display:flex;gap:10px;">
		<a href="/parent/evaluations" style="padding:10px 20px;background:#F3F4F6;color:#374151;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;">← Retour aux évaluations</a>
	</div>

{:else}
	<!-- ═══ QCM ═══ -->
	<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;overflow:hidden;margin-bottom:16px;">
		<div style="background:linear-gradient(135deg,#1E3A8A,#2563EB);padding:18px 22px;color:#fff;">
			<h2 style="font-size:17px;font-weight:700;margin-bottom:4px;">{evaluation.title}</h2>
			<div style="font-size:12px;opacity:.8;">{evaluation.questions.length} questions · {evaluation.subject}</div>
		</div>
		<!-- BARRE PROGRESSION -->
		<div style="padding:12px 22px;border-bottom:1px solid #E5E7EB;display:flex;align-items:center;gap:12px;">
			<div style="flex:1;height:6px;background:#F3F4F6;border-radius:10px;overflow:hidden;">
				<div style="height:100%;width:{progress}%;background:#2563EB;border-radius:10px;transition:width .3s;"></div>
			</div>
			<span style="font-size:12px;color:#6B7280;flex-shrink:0;">{Object.keys(answers).length}/{evaluation.questions.length}</span>
		</div>
	</div>

	<!-- QUESTIONS -->
	<div style="display:flex;flex-direction:column;gap:12px;margin-bottom:20px;">
		{#each evaluation.questions as q, i}
			<div style="background:#fff;border:2px solid {answers[String(q.id)] ? '#2563EB' : '#E5E7EB'};border-radius:8px;overflow:hidden;transition:border-color .15s;">
				<div style="padding:14px 18px;border-bottom:1px solid #F3F4F6;display:flex;align-items:flex-start;gap:12px;">
					<div style="width:28px;height:28px;border-radius:50%;background:{answers[String(q.id)] ? '#2563EB' : '#F3F4F6'};color:{answers[String(q.id)] ? '#fff' : '#6B7280'};font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .15s;">{i+1}</div>
					<div style="font-size:14px;font-weight:600;color:#111827;line-height:1.5;">{q.question}</div>
				</div>
				<div style="padding:14px 18px;display:grid;grid-template-columns:1fr 1fr;gap:8px;">
					{#each Object.entries(q.choices ?? {}) as [key, choice]}
						<button on:click={() => { answers[String(q.id)] = key; answers = answers; }}
							style="padding:10px 14px;border-radius:8px;font-size:13px;text-align:left;cursor:pointer;font-family:inherit;display:flex;align-items:center;gap:8px;transition:all .15s;
							background:{answers[String(q.id)] === key ? '#EFF6FF' : '#F9FAFB'};
							border:2px solid {answers[String(q.id)] === key ? '#2563EB' : '#E5E7EB'};">
							<span style="font-weight:700;color:{answers[String(q.id)] === key ? '#2563EB' : '#9CA3AF'};width:20px;flex-shrink:0;">{key}</span>
							<span style="color:#374151;">{choice}</span>
						</button>
					{/each}
				</div>
			</div>
		{/each}
	</div>

	<!-- BOUTON SOUMETTRE -->
	<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:18px;display:flex;align-items:center;justify-content:space-between;">
		<div style="font-size:13px;color:#6B7280;">
			{#if allAnswered}✅ Toutes les questions répondues !{:else}⚠️ {evaluation.questions.length - Object.keys(answers).length} question(s) sans réponse{/if}
		</div>
		<button on:click={submitAnswers} disabled={!allAnswered || submitting}
			style="padding:11px 28px;border-radius:8px;border:none;font-size:14px;font-weight:700;cursor:{allAnswered && !submitting ? 'pointer' : 'not-allowed'};
			background:{allAnswered && !submitting ? '#16A34A' : '#D1D5DB'};color:#fff;font-family:inherit;display:flex;align-items:center;gap:8px;">
			{#if submitting}
				<div style="width:16px;height:16px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;"></div>
				Correction...
			{:else}
				✓ Soumettre et corriger
			{/if}
		</button>
	</div>
{/if}

<style>
	@keyframes spin { to { transform: rotate(360deg); } }
</style>