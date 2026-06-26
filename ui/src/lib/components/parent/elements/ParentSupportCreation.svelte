<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { user } from '$lib/stores';
	import { browser } from '$app/environment';
	import type { Writable } from 'svelte/store';
	import { createParentSupport, uploadParentSupportFile } from '$lib/apis/parent';

	interface I18n { t: (key: string) => string; }
	const i18n = getContext<Writable<I18n>>('i18n');

	// ── Étapes ──────────────────────────────────────────────────────────────
	const steps = ['Enfant', 'Sujet', 'Cours', 'Objectifs', 'Niveau', 'Révision'];
	let currentStep = 0;
	let isSubmitting = false;

	// ── Données formulaire ───────────────────────────────────────────────────
	let studentId = '';
	let studentEmail = '';
	let studentSearchStatus: 'idle' | 'searching' | 'found' | 'notfound' = 'idle';
	let studentFoundName = '';

	async function searchStudentByEmail() {
		if (!studentEmail.trim()) return;
		const token = browser ? localStorage.getItem('token') : null;
		if (!token) return;
		studentSearchStatus = 'searching';
		try {
			const res = await fetch(
				`http://localhost:8080/api/v1/parent/supports/find-student?email=${encodeURIComponent(studentEmail.trim())}`,
				{ headers: { authorization: `Bearer ${token}` } }
			);
			if (!res.ok) throw new Error('Élève introuvable');
			const data = await res.json();
			studentId = data.id;
			studentFoundName = data.name;
			studentSearchStatus = 'found';
			localStorage.setItem('parent_student_id', data.id);
			localStorage.setItem('parent_student_name', data.name);
		} catch {
			studentSearchStatus = 'notfound';
			studentId = '';
		}
	}
	let studentName = '';
	let parentMessage = '';
	let supportTitle = '';
	let shortDescription = '';
	let selectedSubject = '';
	let customSubject = '';
	let uploadedFiles: File[] = [];
	let learningObjective = '';
	let selectedLearningType: string | null = null;
	let selectedLevel = '';
	let contentLanguage = 'Français';
	let estimatedDuration = '30min';
	let keywords: string[] = [];
	let keywordInput = '';
	let startDate = '';
	let endDate = '';
	let generatedPrompt = '';
	let tutorStyle = 'bienveillant';

	const learningTypes = [
		{ id: 'exam',  name: 'Je prépare un examen',              icon: '✏️' },
		{ id: 'cours', name: 'Je revois un cours',                icon: '📚' },
		{ id: 'skill', name: "J'acquiers une nouvelle compétence", icon: '🚀' },
	];

	const learningLevels = [
		{ id: 'primary',    name: 'École primaire', description: 'Apprentissage fondamental',          color: 'green'  },
		{ id: 'middle',     name: 'Collège',         description: 'Développement de la pensée critique', color: 'yellow' },
		{ id: 'high',       name: 'Lycée',           description: 'Préparation aux études avancées',     color: 'orange' },
		{ id: 'university', name: 'Université',      description: 'Accompagnement de niveau expert',     color: 'red'    },
	];

	const tutorStyles = [
		{ id: 'bienveillant', name: 'Bienveillant', desc: 'Encourageant, patient',   icon: '🤝' },
		{ id: 'socratique',   name: 'Socratique',   desc: 'Questionne, guide',        icon: '🎓' },
		{ id: 'direct',       name: 'Direct',        desc: 'Efficace, structuré',      icon: '⚡' },
	];

	const defaultSubjects = [
		{ id: 'mathematiques', name: 'Mathématiques', icon: '📊' },
		{ id: 'sciences',      name: 'Sciences',       icon: '🔬' },
		{ id: 'histoire',      name: 'Histoire',       icon: '🏛️' },
		{ id: 'informatique',  name: 'Informatique',   icon: '💻' },
		{ id: 'francais',      name: 'Français',       icon: '📚' },
		{ id: 'geographie',    name: 'Géographie',     icon: '🌍' },
		{ id: 'chimie',        name: 'Chimie',         icon: '⚗️' },
		{ id: 'biologie',      name: 'Biologie',       icon: '🌿' },
		{ id: 'physique',      name: 'Physique',       icon: '⚛️' },
		{ id: 'anglais',       name: 'Anglais',        icon: '🗣️' },
		{ id: 'svt',           name: 'SVT',            icon: '🧬' },
	];
	let subjects = [...defaultSubjects];
	let subjectPageIndex = 0;
	const subjectsPerPage = 4;
	$: totalSubjectPages = Math.ceil(subjects.length / subjectsPerPage);
	$: visibleSubjects = subjects.slice(subjectPageIndex * subjectsPerPage, (subjectPageIndex + 1) * subjectsPerPage);
	function prevSubjectPage() { if (subjectPageIndex > 0) subjectPageIndex--; }
	function nextSubjectPage() { if (subjectPageIndex < totalSubjectPages - 1) subjectPageIndex++; }

	const languages = ['Français', 'English', 'Arabic', 'Spanish', 'German'];
	const durations = ['15min', '30min', '45min', '1h', '1h30min', '2h'];

	// ── Génération prompt IA ─────────────────────────────────────────────────
	function generatePrompt() {
		const subjectLabel = selectedSubject
			? (subjects.find(s => s.id === selectedSubject)?.name ?? selectedSubject)
			: customSubject || 'la matière choisie';
		const levelLabel = selectedLevel
			? (learningLevels.find(l => l.id === selectedLevel)?.name ?? selectedLevel)
			: 'adapté';
		const name = studentName || "l'élève";
		const styleDesc = tutorStyle === 'bienveillant'
			? 'encourageant et patient, valorise les efforts avant de corriger, procède étape par étape'
			: tutorStyle === 'socratique'
			? 'socratique, guide par des questions plutôt que de donner les réponses directement'
			: 'direct et structuré, va à l\'essentiel, donne des explications claires et concises';

		generatedPrompt = `Tu es un tuteur IA ${tutorStyle}, spécialisé en ${subjectLabel} pour un élève de niveau ${levelLabel}.

Élève : ${name}
Objectif : ${learningObjective || `maîtriser ${subjectLabel}`}
${shortDescription ? `Contexte : ${shortDescription}` : ''}

Style pédagogique : ${styleDesc}.

Instructions :
- Adapte ton langage au niveau ${levelLabel}
- Si l'élève bloque, reformule différemment avec un exemple concret
- Encourage régulièrement et valorise les progrès
- Utilise les ressources fournies quand elles sont pertinentes`;
	}

	// Régénérer le prompt quand les données changent
	$: if (currentStep === 5) generatePrompt();

	// ── Fichiers ─────────────────────────────────────────────────────────────
	function handleFileChange(e: Event) {
		const files = (e.target as HTMLInputElement).files;
		if (files) uploadedFiles = Array.from(files);
	}
	function handleFileDrop(e: DragEvent) {
		e.preventDefault();
		if (e.dataTransfer?.files) uploadedFiles = Array.from(e.dataTransfer.files);
	}
	function preventDefaults(e: Event) { e.preventDefault(); e.stopPropagation(); }
	function removeFile(i: number) { uploadedFiles = uploadedFiles.filter((_, idx) => idx !== i); }

	// ── Mots-clés ────────────────────────────────────────────────────────────
	function addKeyword() {
		const kw = keywordInput.trim();
		if (kw && !keywords.includes(kw)) { keywords = [...keywords, kw]; keywordInput = ''; }
	}
	function removeKeyword(kw: string) { keywords = keywords.filter(k => k !== kw); }
	function handleKeyDown(e: KeyboardEvent) { if (e.key === 'Enter') { e.preventDefault(); addKeyword(); } }

	// ── Validation ────────────────────────────────────────────────────────────
	$: canProceed =
		currentStep === 0 ? true :
		currentStep === 1 ? supportTitle.trim().length > 0 && (!!selectedSubject || customSubject.trim().length > 0) :
		currentStep === 2 ? true :
		currentStep === 3 ? selectedLearningType !== null :
		currentStep === 4 ? selectedLevel.trim().length > 0 :
		true;

	// ── Navigation ────────────────────────────────────────────────────────────
	function nextStep() { if (currentStep < steps.length - 1) currentStep++; else saveSupportToDatabase(); }
	function prevStep() { if (currentStep > 0) currentStep--; }

	// ── Soumission ────────────────────────────────────────────────────────────
	async function saveSupportToDatabase() {
		const token = browser ? localStorage.getItem('token') : null;
		if (!token) { toast.error('Vous devez être connecté'); return; }
		isSubmitting = true;
		try {
			const support = await createParentSupport(token, {
				student_id: studentId.trim(),
				title: supportTitle,
				short_description: shortDescription || undefined,
				subject: selectedSubject || customSubject || undefined,
				custom_subject: customSubject || undefined,
				learning_objective: learningObjective || undefined,
				learning_type: selectedLearningType || undefined,
				level: selectedLevel || undefined,
				content_language: contentLanguage,
				estimated_duration: estimatedDuration,
				keywords: keywords.length > 0 ? keywords : undefined,
				start_date: startDate || undefined,
				end_date: endDate || undefined,
				parent_message: parentMessage || undefined,
			});

			if (uploadedFiles.length > 0) {
				for (const file of uploadedFiles) {
					await uploadParentSupportFile(token, support.id, studentId, file);
				}
			}
			toast.success('Soutien créé avec succès ! 🎉');
			goto('/student/supports');
		} catch (err: any) {
			toast.error(err?.message ?? 'Erreur lors de la création du soutien');
		} finally {
			isSubmitting = false;
		}
	}

	// Nom d'affichage de la matière sélectionnée
	$: userInitials = ($user?.name ?? 'MA').split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase();
	$: subjectLabel = selectedSubject
		? (subjects.find(s => s.id === selectedSubject)?.name ?? selectedSubject)
		: customSubject || '';
</script>




	<!-- STEPPER -->
	<div style="display:flex;align-items:center;margin-bottom:36px;padding:0 10px;">
		{#each steps as step, index}
			<div style="display:flex;flex-direction:column;align-items:center;position:relative;z-index:1;">
				<button
					on:click={() => { if (index <= currentStep) currentStep = index; }}
					style="width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;margin-bottom:6px;border:none;cursor:{index <= currentStep ? 'pointer' : 'default'};
					{currentStep > index ? 'background:#2563EB;color:white;' :
					 currentStep === index ? 'background:#2563EB;color:white;box-shadow:0 0 0 4px rgba(37,99,235,.15);' :
					 'background:#fff;color:#6B7280;border:2px solid #E5E7EB;'}"
				>
					{#if currentStep > index}✓{:else}{index + 1}{/if}
				</button>
				<span style="font-size:11px;font-weight:600;white-space:nowrap;color:{currentStep >= index ? '#2563EB' : '#9CA3AF'};">{step}</span>
			</div>
			{#if index < steps.length - 1}
				<div style="flex:1;height:2px;margin:0 4px;margin-bottom:18px;position:relative;background:#E5E7EB;">
					{#if currentStep > index}
						<div style="position:absolute;top:0;left:0;height:100%;width:100%;background:#2563EB;transition:width .5s;"></div>
					{/if}
				</div>
			{/if}
		{/each}
	</div>

	<!-- FORM CARD -->
	<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;overflow:hidden;">
		<div style="padding:28px;min-height:380px;">

			<!-- ══ ÉTAPE 0 : Enfant ══ -->
			{#if currentStep === 0}
			<h3 style="font-size:18px;font-weight:700;margin-bottom:6px;">Pour quel enfant créez-vous ce soutien ?</h3>
			<p style="font-size:13px;color:#6B7280;margin-bottom:24px;">Entrez l'email de l'enfant pour lier le soutien à son compte. Vous pouvez aussi continuer sans liaison.</p>

			<!-- RECHERCHE PAR EMAIL -->
			<div style="margin-bottom:20px;">
				<label for="semail" style="display:block;font-size:13px;font-weight:600;margin-bottom:6px;">Email de l'enfant <span style="color:#6B7280;font-weight:400;">(facultatif)</span></label>
				<div style="display:flex;gap:8px;">
					<input id="semail" type="email" bind:value={studentEmail}
						on:keydown={(e) => e.key === 'Enter' && searchStudentByEmail()}
						placeholder="ex : wissal@gmail.fr"
						style="flex:1;padding:10px 14px;border:1px solid {studentSearchStatus === 'found' ? '#16A34A' : studentSearchStatus === 'notfound' ? '#DC2626' : '#E5E7EB'};border-radius:8px;font-size:13px;outline:none;"/>
					<button on:click={searchStudentByEmail} disabled={!studentEmail.trim() || studentSearchStatus === 'searching'}
						style="padding:10px 16px;background:#2563EB;color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;font-family:inherit;">
						{studentSearchStatus === 'searching' ? '⏳' : '🔍 Rechercher'}
					</button>
				</div>
				<!-- Résultat de la recherche -->
				{#if studentSearchStatus === 'found'}
					<div style="margin-top:8px;padding:10px 14px;background:#D1FAE5;border:1px solid #6EE7B7;border-radius:8px;display:flex;align-items:center;gap:8px;">
						<span style="font-size:18px;">✅</span>
						<div>
							<div style="font-size:13px;font-weight:600;color:#065F46;">Élève trouvé : {studentFoundName}</div>
							<div style="font-size:12px;color:#065F46;">Le soutien sera lié à son compte automatiquement.</div>
						</div>
					</div>
				{:else if studentSearchStatus === 'notfound'}
					<div style="margin-top:8px;padding:10px 14px;background:#FEE2E2;border:1px solid #FECACA;border-radius:8px;font-size:13px;color:#991B1B;">
						❌ Aucun élève trouvé avec cet email. Vérifiez l'adresse ou continuez sans liaison.
					</div>
				{/if}
			</div>
			<div style="margin-bottom:20px;">
				<label for="sname" style="display:block;font-size:13px;font-weight:600;margin-bottom:6px;">Prénom de l'enfant</label>
				<input id="sname" type="text" bind:value={studentName} placeholder="ex : Yassine" style="width:100%;padding:10px 14px;border:1px solid #E5E7EB;border-radius:8px;font-size:13px;outline:none;"/>
			</div>
			<div>
				<label for="pmsg" style="display:block;font-size:13px;font-weight:600;margin-bottom:6px;">Message personnel <span style="color:#6B7280;font-weight:400;">(facultatif)</span></label>
				<textarea id="pmsg" bind:value={parentMessage} placeholder="Mon enfant, j'ai préparé ce soutien pour t'aider. Courage ! 💪" style="width:100%;padding:10px 14px;border:1px solid #E5E7EB;border-radius:8px;font-size:13px;outline:none;min-height:80px;resize:vertical;line-height:1.6;"></textarea>
			</div>

			<!-- ══ ÉTAPE 1 : Sujet ══ -->
			{:else if currentStep === 1}
			<h3 style="font-size:18px;font-weight:700;margin-bottom:6px;">Expliquez les besoins d'apprentissage</h3>
			<p style="font-size:13px;color:#6B7280;margin-bottom:24px;">Décrivez la difficulté rencontrée par {studentName || "votre enfant"}.</p>
			<div style="margin-bottom:20px;">
				<label for="title" style="display:block;font-size:13px;font-weight:600;margin-bottom:6px;">Titre <span style="color:#2563EB;">*</span></label>
				<input id="title" type="text" bind:value={supportTitle} placeholder="ex : Maîtriser les fractions — Maths 3ème" style="width:100%;padding:10px 14px;border:1px solid #E5E7EB;border-radius:8px;font-size:13px;outline:none;"/>
			</div>
			<div style="margin-bottom:24px;">
				<label for="desc" style="display:block;font-size:13px;font-weight:600;margin-bottom:6px;">Description courte</label>
				<textarea id="desc" bind:value={shortDescription} placeholder="Résumez la difficulté..." style="width:100%;padding:10px 14px;border:1px solid #E5E7EB;border-radius:8px;font-size:13px;outline:none;min-height:80px;resize:vertical;line-height:1.6;"></textarea>
			</div>
			<div style="background:#F9FAFB;padding:20px;border-radius:8px;border:1px solid #E5E7EB;">
				<label style="display:block;font-size:13px;font-weight:600;margin-bottom:12px;">Choisissez un sujet <span style="color:#2563EB;">*</span></label>
				<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;">
					{#each visibleSubjects as subject}
						<button on:click={() => selectedSubject = subject.id}
							style="display:flex;flex-direction:column;align-items:center;padding:16px 10px;border-radius:8px;cursor:pointer;font-family:inherit;
							border:{selectedSubject === subject.id ? '2px solid #2563EB' : '1.5px solid #E5E7EB'};
							background:{selectedSubject === subject.id ? '#EFF6FF' : '#fff'};">
							<span style="font-size:28px;margin-bottom:8px;">{subject.icon}</span>
							<span style="font-size:12px;font-weight:600;color:#111827;text-align:center;">{subject.name}</span>
						</button>
					{/each}
				</div>
				<div style="display:flex;justify-content:center;gap:10px;margin-top:14px;align-items:center;">
					<button on:click={prevSubjectPage} disabled={subjectPageIndex === 0} style="padding:6px 12px;border-radius:6px;border:1px solid #E5E7EB;background:#fff;cursor:pointer;">←</button>
					<span style="font-size:12px;color:#6B7280;">{subjectPageIndex + 1} / {totalSubjectPages}</span>
					<button on:click={nextSubjectPage} disabled={subjectPageIndex >= totalSubjectPages - 1} style="padding:6px 12px;border-radius:6px;border:1px solid #E5E7EB;background:#fff;cursor:pointer;">→</button>
				</div>
				<div style="margin-top:16px;">
					<p style="font-size:12px;color:#6B7280;margin-bottom:6px;">Matière non listée ? Créez la vôtre :</p>
					<input type="text" bind:value={customSubject} placeholder="Votre matière personnalisée" style="width:100%;padding:10px 14px;border:1px solid #E5E7EB;border-radius:8px;font-size:13px;outline:none;"/>
				</div>
			</div>

			<!-- ══ ÉTAPE 2 : Fichiers ══ -->
			{:else if currentStep === 2}
			<h3 style="font-size:18px;font-weight:700;margin-bottom:6px;">Ressources pédagogiques</h3>
			<p style="font-size:13px;color:#6B7280;margin-bottom:20px;">Joignez le cours, les fiches ou tout document utile pour le tuteur IA.</p>
			<div role="button" tabindex="0" aria-label="Zone de dépôt de fichiers"
				style="border:2px dashed #D1D5DB;border-radius:8px;padding:40px 20px;text-align:center;cursor:pointer;background:#FAFAFA;"
				on:click={() => document.getElementById('pfile')?.click()}
				on:keypress={(e) => e.key === 'Enter' && document.getElementById('pfile')?.click()}
				on:dragover={preventDefaults} on:dragenter={preventDefaults} on:drop={handleFileDrop}>
				<input type="file" id="pfile" style="display:none;" multiple accept=".pdf,.doc,.docx,.pptx,.mp4" on:change={handleFileChange}/>
				<div style="font-size:40px;margin-bottom:12px;color:#2563EB;">☁</div>
				<p style="color:#374151;margin-bottom:4px;">Cliquez pour télécharger ou glissez-déposez</p>
				<p style="font-size:12px;color:#9CA3AF;">PDF, DOCX, PPTX, MP4 (max 50Mo)</p>
			</div>
			{#if uploadedFiles.length > 0}
				<div style="margin-top:14px;display:flex;flex-direction:column;gap:8px;">
					{#each uploadedFiles as file, i}
						<div style="display:flex;align-items:center;gap:10px;padding:9px 12px;border:1px solid #E5E7EB;border-radius:8px;background:#F9FAFB;font-size:13px;">
							<span>📄</span>
							<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{file.name}</span>
							<button on:click={() => removeFile(i)} style="background:none;border:none;color:#9CA3AF;cursor:pointer;">✕</button>
						</div>
					{/each}
				</div>
			{/if}

			<!-- ══ ÉTAPE 3 : Objectifs ══ -->
			{:else if currentStep === 3}
			<h3 style="font-size:18px;font-weight:700;margin-bottom:6px;">Définissez l'objectif pédagogique</h3>
			<div style="background:#F9FAFB;padding:20px;border-radius:8px;border:1px solid #E5E7EB;margin-bottom:20px;">
				<label for="obj" style="display:block;font-size:13px;font-weight:600;margin-bottom:8px;">Que voulez-vous que {studentName || "l'enfant"} maîtrise ?</label>
				<textarea id="obj" bind:value={learningObjective} placeholder="À la fin de ce soutien, l'élève devrait être capable de..."
					style="width:100%;padding:10px 14px;border:1px solid #E5E7EB;border-radius:8px;font-size:13px;outline:none;min-height:100px;resize:vertical;line-height:1.6;background:#fff;"></textarea>
			</div>
			<div style="background:#F9FAFB;padding:20px;border-radius:8px;border:1px solid #E5E7EB;">
				<label style="display:block;font-size:13px;font-weight:600;margin-bottom:14px;">Comment puis-je vous aider ? <span style="color:#2563EB;">*</span></label>
				<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
					{#each learningTypes as type}
						<button on:click={() => selectedLearningType = selectedLearningType === type.id ? null : type.id}
							style="display:flex;align-items:center;gap:10px;padding:14px;border-radius:8px;cursor:pointer;font-family:inherit;text-align:left;
							border:{selectedLearningType === type.id ? '2px solid #2563EB' : '1.5px solid #E5E7EB'};
							background:{selectedLearningType === type.id ? '#EFF6FF' : '#fff'};">
							<span style="font-size:22px;">{type.icon}</span>
							<span style="font-size:12px;font-weight:600;color:#111827;">{type.name}</span>
						</button>
					{/each}
				</div>
			</div>

			<!-- ══ ÉTAPE 4 : Niveau ══ -->
			{:else if currentStep === 4}
			<h3 style="font-size:18px;font-weight:700;margin-bottom:6px;">Choisissez le niveau scolaire</h3>
			<p style="font-size:13px;color:#6B7280;margin-bottom:24px;">Sélectionnez le niveau approprié. <span style="color:#2563EB;">*</span></p>
			<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
				{#each learningLevels as level}
					<button on:click={() => selectedLevel = level.id}
						style="display:flex;align-items:center;padding:18px;border-radius:8px;cursor:pointer;text-align:left;font-family:inherit;
						border:{selectedLevel === level.id ? '2px solid #2563EB' : '1.5px solid #E5E7EB'};
						background:{selectedLevel === level.id ? '#EFF6FF' : '#fff'};">
						<div style="width:46px;height:46px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-right:14px;flex-shrink:0;
							background:{level.color === 'green' ? '#D1FAE5' : level.color === 'yellow' ? '#FEF3C7' : level.color === 'orange' ? '#FED7AA' : '#FEE2E2'};
							color:{level.color === 'green' ? '#065F46' : level.color === 'yellow' ? '#92400E' : level.color === 'orange' ? '#9A3412' : '#991B1B'};">📖</div>
						<div>
							<div style="font-size:15px;font-weight:600;color:#111827;margin-bottom:3px;">{level.name}</div>
							<div style="font-size:12px;color:#6B7280;">{level.description}</div>
						</div>
					</button>
				{/each}
			</div>

			<!-- ══ ÉTAPE 5 : Révision ══ -->
			{:else if currentStep === 5}
			<h3 style="font-size:18px;font-weight:700;margin-bottom:6px;">Vérifiez le soutien avant de créer</h3>
			<div style="background:#fff;border-radius:8px;border:1px solid #E5E7EB;overflow:hidden;margin-bottom:16px;">
				<div style="background:linear-gradient(135deg,#1E3A8A,#2563EB);padding:18px 22px;color:#fff;">
					<h4 style="font-size:16px;font-weight:700;margin-bottom:6px;">{supportTitle}</h4>
					<div style="display:flex;gap:8px;flex-wrap:wrap;">
						{#if studentName}<span style="background:rgba(255,255,255,.2);padding:2px 10px;border-radius:20px;font-size:12px;">Pour : {studentName}</span>{/if}
						{#if subjectLabel}<span style="background:rgba(255,255,255,.2);padding:2px 10px;border-radius:20px;font-size:12px;">{subjectLabel}</span>{/if}
						{#if selectedLevel}<span style="background:rgba(255,255,255,.2);padding:2px 10px;border-radius:20px;font-size:12px;">{learningLevels.find(l => l.id === selectedLevel)?.name}</span>{/if}
					</div>
				</div>
				<div style="padding:16px 22px;display:grid;grid-template-columns:1fr 1fr;gap:14px;border-bottom:1px solid #E5E7EB;">
					<div>
						{#if shortDescription}<div style="margin-bottom:10px;"><div style="font-size:11px;font-weight:600;color:#6B7280;text-transform:uppercase;margin-bottom:3px;">Description</div><div style="font-size:13px;">{shortDescription}</div></div>{/if}
						{#if learningObjective}<div style="margin-bottom:10px;"><div style="font-size:11px;font-weight:600;color:#6B7280;text-transform:uppercase;margin-bottom:3px;">Objectif</div><div style="font-size:13px;">{learningObjective}</div></div>{/if}
						{#if parentMessage}<div><div style="font-size:11px;font-weight:600;color:#6B7280;text-transform:uppercase;margin-bottom:3px;">Message</div><div style="font-size:13px;font-style:italic;">"{parentMessage}"</div></div>{/if}
					</div>
					<div>
						{#if selectedLearningType}<div style="margin-bottom:10px;"><div style="font-size:11px;font-weight:600;color:#6B7280;text-transform:uppercase;margin-bottom:3px;">Type</div><span style="background:#F3E8FF;color:#6B21A8;padding:3px 10px;border-radius:6px;font-size:12px;font-weight:600;">{learningTypes.find(t => t.id === selectedLearningType)?.name}</span></div>{/if}
						<div><div style="font-size:11px;font-weight:600;color:#6B7280;text-transform:uppercase;margin-bottom:3px;">Détails</div><div style="font-size:13px;">🌍 {contentLanguage} &nbsp; ⏱ {estimatedDuration}</div></div>
						{#if uploadedFiles.length > 0}<div style="margin-top:10px;"><div style="font-size:11px;font-weight:600;color:#6B7280;text-transform:uppercase;margin-bottom:3px;">Fichiers</div>{#each uploadedFiles as f}<div style="font-size:12px;">📎 {f.name}</div>{/each}</div>{/if}
					</div>
				</div>
				<div style="padding:16px 22px;display:grid;grid-template-columns:1fr 1fr;gap:12px;border-bottom:1px solid #E5E7EB;">
					<div>
						<label style="display:block;font-size:12px;font-weight:600;color:#6B7280;margin-bottom:6px;">Langue</label>
						<select bind:value={contentLanguage} style="width:100%;padding:8px 12px;border:1px solid #E5E7EB;border-radius:8px;font-size:13px;background:#fff;outline:none;">
							{#each languages as l}<option value={l}>{l}</option>{/each}
						</select>
					</div>
					<div>
						<label style="display:block;font-size:12px;font-weight:600;color:#6B7280;margin-bottom:6px;">Durée estimée</label>
						<select bind:value={estimatedDuration} style="width:100%;padding:8px 12px;border:1px solid #E5E7EB;border-radius:8px;font-size:13px;background:#fff;outline:none;">
							{#each durations as d}<option value={d}>{d}</option>{/each}
						</select>
					</div>
					<div style="grid-column:1/-1;">
						<label style="display:block;font-size:12px;font-weight:600;color:#6B7280;margin-bottom:6px;">Mots-clés</label>
						<div style="display:flex;gap:8px;">
							<input type="text" bind:value={keywordInput} on:keydown={handleKeyDown} placeholder="Ajouter..." style="flex:1;padding:8px 12px;border:1px solid #E5E7EB;border-radius:8px;font-size:13px;outline:none;"/>
							<button on:click={addKeyword} style="padding:8px 16px;background:#2563EB;color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;">Ajouter</button>
						</div>
						{#if keywords.length > 0}
							<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;">
								{#each keywords as kw}
									<span style="display:inline-flex;align-items:center;gap:4px;background:#DBEAFE;color:#1E40AF;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;">
										{kw}<button on:click={() => removeKeyword(kw)} style="background:none;border:none;cursor:pointer;color:#1E40AF;font-size:12px;">✕</button>
									</span>
								{/each}
							</div>
						{/if}
					</div>
					<div>
						<label style="display:block;font-size:12px;font-weight:600;color:#6B7280;margin-bottom:6px;">Date de début</label>
						<input type="date" bind:value={startDate} style="width:100%;padding:8px 12px;border:1px solid #E5E7EB;border-radius:8px;font-size:13px;outline:none;"/>
					</div>
					<div>
						<label style="display:block;font-size:12px;font-weight:600;color:#6B7280;margin-bottom:6px;">Date de fin</label>
						<input type="date" bind:value={endDate} style="width:100%;padding:8px 12px;border:1px solid #E5E7EB;border-radius:8px;font-size:13px;outline:none;"/>
					</div>
				</div>
				<!-- PROMPT IA -->
				<div style="padding:16px 22px;">
					<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
						<span style="font-size:13px;font-weight:600;">🤖 Prompt IA personnalisé</span>
						<span style="font-size:11px;font-weight:600;background:#EFF6FF;color:#2563EB;padding:2px 8px;border-radius:4px;">Auto-généré</span>
						<button on:click={generatePrompt} style="margin-left:auto;font-size:11px;background:none;border:1px solid #E5E7EB;border-radius:6px;padding:3px 10px;cursor:pointer;color:#6B7280;">✨ Régénérer</button>
					</div>
					<div style="background:#1E293B;border-radius:8px;padding:14px 16px;">
						<textarea bind:value={generatedPrompt} style="background:transparent;border:none;color:#94A3B8;font-family:monospace;font-size:12px;line-height:1.7;min-height:120px;width:100%;resize:vertical;outline:none;padding:0;"></textarea>
					</div>
					<div style="margin-top:16px;">
						<label style="display:block;font-size:12px;font-weight:600;color:#6B7280;margin-bottom:8px;">Style de tuteur</label>
						<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
							{#each tutorStyles as ts}
								<button on:click={() => { tutorStyle = ts.id; generatePrompt(); }}
									style="padding:12px;border-radius:8px;text-align:center;cursor:pointer;font-family:inherit;
									border:{tutorStyle === ts.id ? '2px solid #2563EB' : '1.5px solid #E5E7EB'};
									background:{tutorStyle === ts.id ? '#EFF6FF' : '#fff'};">
									<div style="font-size:20px;margin-bottom:4px;">{ts.icon}</div>
									<div style="font-size:12px;font-weight:700;color:#111827;">{ts.name}</div>
									<div style="font-size:11px;color:#6B7280;margin-top:2px;">{ts.desc}</div>
								</button>
							{/each}
						</div>
					</div>
				</div>
				<div style="padding:12px 22px;background:#F9FAFB;display:flex;align-items:center;gap:8px;">
					<span style="color:#2563EB;">ℹ</span>
					<span style="font-size:12px;color:#374151;">Le soutien sera visible dans l'espace de {studentName || "l'enfant"} dès sa création.</span>
				</div>
			</div>
			{/if}
		</div>

		<!-- BOUTONS NAVIGATION -->
		<div style="display:flex;align-items:center;justify-content:space-between;padding:16px 28px;border-top:1px solid #E5E7EB;">
			<button on:click={() => { if (currentStep === 0) goto('/parent/dashboard'); else prevStep(); }} disabled={isSubmitting}
				style="display:flex;align-items:center;gap:6px;padding:9px 20px;border-radius:20px;border:1px solid #E5E7EB;background:#fff;color:#111827;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;">
				← {currentStep === 0 ? 'Annuler' : 'Retour en arrière'}
			</button>
			<button on:click={nextStep} disabled={!canProceed || isSubmitting}
				style="display:flex;align-items:center;gap:6px;padding:9px 22px;border-radius:20px;border:none;background:{(!canProceed || isSubmitting) ? '#93C5FD' : '#2563EB'};color:#fff;font-size:13px;font-weight:700;cursor:{(!canProceed || isSubmitting) ? 'not-allowed' : 'pointer'};font-family:inherit;">
				{#if isSubmitting}⏳ Création en cours...{:else if currentStep === steps.length - 1}🚀 Créer le soutien{:else}Continue →{/if}
			</button>
		</div>
	</div>