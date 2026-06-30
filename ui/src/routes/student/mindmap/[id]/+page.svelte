<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { getMindmapContext, verifyMindmap, exportMindmapPDF } from '$lib/apis/mindmap';
	import { getMindmapContext, verifyMindmap, exportMindmapPDF } from '$lib/apis/mindmap';
	const sessionId = $page.params.id;

	// STATE
	let nodes: any[] = [];
	let edges: any[] = [];
	let selectedId: string | null = null;
	let tool = 'select';
	let currentColor = '#6366f1';
	let nodeCounter = 0;
	let connectFrom: string | null = null;
	let canvasEl: HTMLDivElement;

	// CONTEXT STATE
	let courseTitle = 'Mon cours';
	let suggestedConcepts: string[] = [];
	let loadingContext = true;
	let showSuggestions = true;

	// VERIFY STATE
	let verifying = false;
	let verifyResult: any = null;

	const COLORS = [
		'#6366f1',
		'#22c55e',
		'#f97316',
		'#ec4899',
		'#0ea5e9',
		'#eab308',
		'#ef4444',
		'#8b5cf6'
	];

	onMount(async () => {
		await loadContext();
	});

	async function loadContext() {
		loadingContext = true;
		try {
			const token = localStorage.getItem('token') || '';
			const ctx = await getMindmapContext(token, sessionId);
			courseTitle = ctx.title || 'Mon cours';
			suggestedConcepts = ctx.concepts || [];
		} catch (e) {
			console.warn('Context load failed, using defaults', e);
			courseTitle = 'Mon cours';
			suggestedConcepts = [];
		} finally {
			loadingContext = false;
			addCentralNode();
		}
	}

	function uid() {
		return 'n' + ++nodeCounter + '_' + Math.random().toString(36).slice(2, 6);
	}

	function addCentralNode() {
		const n = {
			id: uid(),
			label: courseTitle,
			x: 480,
			y: 300,
			type: 'central',
			color: '#6366f1'
		};
		nodes = [n];
	}

	function addNode() {
		const n = {
			id: uid(),
			label: 'Nouveau concept',
			x: 200 + Math.random() * 400,
			y: 150 + Math.random() * 300,
			type: 'child',
			color: currentColor
		};
		nodes = [...nodes, n];
		selectedId = n.id;
	}

	function addSuggestedConcept(label: string) {
		const central = nodes[0];
		const n = {
			id: uid(),
			label,
			x: 200 + Math.random() * 400,
			y: 150 + Math.random() * 300,
			type: 'child',
			color: '#6366f1'
		};
		nodes = [...nodes, n];
		if (central) {
			edges = [...edges, { from: central.id, to: n.id }];
		}
	}

	function deleteSelected() {
		if (!selectedId || nodes.find((n) => n.id === selectedId)?.type === 'central') return;
		edges = edges.filter((e) => e.from !== selectedId && e.to !== selectedId);
		nodes = nodes.filter((n) => n.id !== selectedId);
		selectedId = null;
	}

	function setTool(t: string) {
		tool = t;
		if (t !== 'connect') connectFrom = null;
	}

	function handleNodeClick(id: string) {
		if (tool === 'connect') {
			if (!connectFrom) {
				connectFrom = id;
			} else if (connectFrom !== id) {
				const exists = edges.find(
					(e) => (e.from === connectFrom && e.to === id) || (e.from === id && e.to === connectFrom)
				);
				if (!exists) edges = [...edges, { from: connectFrom, to: id }];
				connectFrom = null;
				setTool('select');
			}
		} else {
			selectedId = id;
		}
	}

	let dragging: string | null = null;
	let dragOffset = { x: 0, y: 0 };

	function startDrag(e: PointerEvent, id: string) {
		if (tool === 'connect') return;
		e.stopPropagation();
		dragging = id;
		const node = nodes.find((n) => n.id === id)!;
		const rect = canvasEl.getBoundingClientRect();
		dragOffset = {
			x: e.clientX - rect.left - node.x,
			y: e.clientY - rect.top - node.y
		};
		(e.target as HTMLElement).setPointerCapture(e.pointerId);
	}

	function onDrag(e: PointerEvent) {
		if (!dragging) return;
		const rect = canvasEl.getBoundingClientRect();
		nodes = nodes.map((n) =>
			n.id === dragging
				? { ...n, x: e.clientX - rect.left - dragOffset.x, y: e.clientY - rect.top - dragOffset.y }
				: n
		);
	}

	function stopDrag() {
		dragging = null;
	}

	let editingId: string | null = null;
	let editValue = '';

	function startEdit(id: string) {
		editingId = id;
		editValue = nodes.find((n) => n.id === id)?.label ?? '';
	}

	function finishEdit() {
		if (!editingId) return;
		nodes = nodes.map((n) => (n.id === editingId ? { ...n, label: editValue } : n));
		editingId = null;
	}

	function nodeCenter(id: string) {
		const n = nodes.find((x) => x.id === id);
		return n ? { x: n.x, y: n.y } : { x: 0, y: 0 };
	}

	async function verify() {
		if (nodes.length < 2) {
			alert('Ajoutez au moins 2 noeuds avant de verifier !');
			return;
		}
		verifying = true;
		verifyResult = null;
		try {
			const token = localStorage.getItem('token') || '';
			const result = await verifyMindmap(token, sessionId, nodes, edges);
			verifyResult = result;
		} catch (e) {
			console.warn('Verify API failed, using fallback', e);
			verifyResult = {
				status: nodes.length >= 4 ? 'success' : 'improve',
				score: nodes.length * 15,
				feedback:
					nodes.length >= 4 ? 'Bonne carte mentale !' : "Essaie d'ajouter plus de concepts.",
				covered_concepts: nodes.filter((n) => n.type !== 'central').map((n) => n.label),
				missing_concepts: []
			};
		} finally {
			verifying = false;
		}
	}

	function resetVerify() {
		verifyResult = null;
	}

	let downloading = false;

async function downloadPDF() {
    downloading = true;
    try {
        const token = localStorage.getItem('token') || '';
        await exportMindmapPDF(token, courseTitle, nodes, edges);
    } catch (e) {
        console.error('PDF export failed', e);
        alert('Erreur lors du téléchargement du PDF');
    } finally {
        downloading = false;
    }
}
</script>

<svelte:head>
	<title>Carte Mentale — OpenTutorAI</title>
</svelte:head>

<!-- TOPBAR -->
<div class="topbar">
	<div class="brand">
		<div class="logo">🧠</div>
		<span class="logo-text">Open<span>TutorAI</span></span>
		<span class="session-badge">🗺️ Carte Mentale</span>
	</div>
	<div class="topbar-right">
		<span class="node-count">Noeuds : <b>{nodes.length}</b></span>
		<button class="btn btn-ghost" on:click={() => goto(`/student/c/${sessionId}`)}>
			← Retour au chat
		</button>
		<button class="btn btn-primary" on:click={verify} disabled={verifying}>
			{verifying ? '⏳ Analyse en cours...' : '✓ Verifier ma carte'}
		</button>
	</div>
</div>

<!-- EDITOR LAYOUT -->
<div class="editor-layout">
	<!-- TOOLBAR -->
	<div class="toolbar">
		<button
			class="tool-btn {tool === 'select' ? 'active' : ''}"
			title="Selectionner"
			on:click={() => setTool('select')}>⬆️</button
		>
		<button class="tool-btn" title="Ajouter noeud" on:click={addNode}>➕</button>
		<button
			class="tool-btn {tool === 'connect' ? 'active' : ''}"
			title="Connecter"
			on:click={() => setTool('connect')}>🔗</button
		>
		<div class="tool-sep"></div>
		<button class="tool-btn" title="Supprimer" on:click={deleteSelected}>🗑️</button>
	</div>

	<!-- CANVAS -->
	<div
		class="canvas-wrap"
		bind:this={canvasEl}
		on:pointermove={onDrag}
		on:pointerup={stopDrag}
		on:dblclick={(e) => {
			if (e.target?.closest?.('.mm-node')) return;
			const rect = canvasEl.getBoundingClientRect();
			const n = {
				id: uid(),
				label: 'Concept',
				x: e.clientX - rect.left,
				y: e.clientY - rect.top,
				type: 'child',
				color: currentColor
			};
			nodes = [...nodes, n];
			selectedId = n.id;
			setTimeout(() => startEdit(n.id), 50);
		}}
	>
		<!-- SVG EDGES -->
		<svg class="edges-svg">
			{#each edges as edge}
				{@const a = nodeCenter(edge.from)}
				{@const b = nodeCenter(edge.to)}
				{@const mx = (a.x + b.x) / 2}
				<path
					d="M{a.x},{a.y} Q{mx},{a.y} {mx},{(a.y + b.y) / 2} Q{mx},{b.y} {b.x},{b.y}"
					fill="none"
					stroke="rgba(99,102,241,0.5)"
					stroke-width="2.5"
					stroke-linecap="round"
				/>
			{/each}
		</svg>

		<!-- NODES -->
		{#each nodes as node (node.id)}
			<div
				class="mm-node {node.type} {selectedId === node.id ? 'selected' : ''} {connectFrom ===
				node.id
					? 'connecting'
					: ''}"
				style="left:{node.x}px; top:{node.y}px; --nc:{node.color}"
				on:pointerdown={(e) => {
					startDrag(e, node.id);
					handleNodeClick(node.id);
				}}
				on:dblclick|stopPropagation={() => startEdit(node.id)}
				role="button"
				tabindex="0"
			>
				{#if editingId === node.id}
					<input
						class="node-input"
						bind:value={editValue}
						on:blur={finishEdit}
						on:keydown={(e) => {
							if (e.key === 'Enter' || e.key === 'Escape') finishEdit();
						}}
						autofocus
					/>
				{:else}
					<span class="node-label">{node.label}</span>
				{/if}
			</div>
		{/each}

		<!-- HINTS & SUGGESTIONS -->
		{#if loadingContext}
			<div class="hint">
				<p>⏳ Chargement du contexte de ta session...</p>
			</div>
		{:else if nodes.length === 1 && suggestedConcepts.length > 0 && showSuggestions}
			<div class="suggestions-panel">
				<div class="suggestions-title">
					💡 Concepts abordés dans ta session — clique pour ajouter :
				</div>
				<div class="suggestions-chips">
					{#each suggestedConcepts as concept}
						<button class="suggestion-chip" on:click={() => addSuggestedConcept(concept)}>
							+ {concept}
						</button>
					{/each}
				</div>
				<button class="btn-skip" on:click={() => (showSuggestions = false)}>
					Créer ma carte librement →
				</button>
			</div>
		{:else if nodes.length === 1}
			<div class="hint">
				<p>💡 Double-clic sur le canvas pour ajouter un noeud</p>
				<p>Ou utilise le bouton <b>➕</b> dans la barre d'outils</p>
			</div>
		{/if}
	</div>

	<!-- RIGHT PANEL -->
	<div class="right-panel">
		<div class="panel-title">Couleur du noeud</div>
		<div class="swatches">
			{#each COLORS as c}
				<button
					class="swatch {currentColor === c ? 'active' : ''}"
					style="background:{c}"
					on:click={() => {
						currentColor = c;
						if (selectedId) {
							nodes = nodes.map((n) =>
								n.id === selectedId && n.type !== 'central' ? { ...n, color: c } : n
							);
						}
					}}
				/>
			{/each}
		</div>
		<div class="tool-sep" style="margin:12px 0; width:100%"></div>
		<div class="panel-title">Conseils</div>
		<div class="panel-hint">
			• <b>Drag</b> pour deplacer<br />
			• <b>Double-clic</b> pour editer<br />
			• 🔗 puis 2 noeuds pour connecter<br />
			• Selectionne + couleur pour changer
		</div>
		<div style="margin-top:auto; display:flex; flex-direction:column; gap:8px">
			<button class="btn btn-ghost btn-sm" on:click={addNode}>➕ Ajouter noeud</button>
			<button class="btn btn-ghost btn-sm" on:click={deleteSelected}>🗑️ Supprimer</button>
		</div>
	</div>
</div>

<!-- VERIFY RESULT OVERLAY -->
{#if verifyResult}
	<div class="overlay">
		{#if verifyResult.status === 'success'}
			<div class="result-card success">
				<div class="result-badge badge-success">✅ Carte validée par l'agent IA</div>
				<h2>Bravo, excellente carte mentale !</h2>
				<p>{verifyResult.feedback || 'Tu as bien structuré les concepts clés de cette session.'}</p>
				<div class="chips">
					{#each verifyResult.covered_concepts || [] as concept}
						<span class="chip">✓ {concept}</span>
					{/each}
				</div>
				<div class="result-actions">
					<button class="btn btn-green" on:click={downloadPDF} disabled={downloading}>
    {downloading ? '⏳ Génération...' : '⬇️ Télécharger PDF'}
</button>
					<button class="btn btn-ghost" on:click={resetVerify}>Modifier ma carte</button>
				</div>
			</div>
		{:else}
			<div class="result-card improve">
				<div class="result-badge badge-warn">⚠️ Quelques concepts manquants</div>
				<h2>Ta carte est bien démarrée !</h2>
				<p>{verifyResult.feedback || "L'agent IA a détecté des concepts manquants."}</p>
				{#if verifyResult.missing_concepts?.length > 0}
					<ul class="missing-list">
						{#each verifyResult.missing_concepts as concept}
							<li>📦 <strong>{concept}</strong></li>
						{/each}
					</ul>
				{:else}
					<ul class="missing-list">
						<li>📦 <strong>Ajoute plus de concepts</strong> — essaie d'en avoir au moins 4</li>
					</ul>
				{/if}
				<div class="result-actions">
					<button class="btn btn-primary" on:click={resetVerify}>✏️ Améliorer moi-même</button>
					<button class="btn btn-orange">🤖 Laisser l'agent compléter</button>
				</div>
			</div>
		{/if}
	</div>
{/if}

<style>
	:global(body) {
		margin: 0;
		font-family: 'Inter', sans-serif;
		background: #0b0e1a;
		color: #e8eaf6;
		overflow: hidden;
	}

	.topbar {
		height: 56px;
		background: #141828;
		border-bottom: 1px solid #262d44;
		display: flex;
		align-items: center;
		gap: 14px;
		padding: 0 20px;
		flex-shrink: 0;
	}
	.brand {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.logo {
		width: 32px;
		height: 32px;
		border-radius: 9px;
		background: linear-gradient(135deg, #6366f1, #7c3aed);
		display: grid;
		place-items: center;
		font-size: 16px;
	}
	.logo-text {
		font-weight: 700;
		font-size: 15px;
	}
	.logo-text span {
		color: #818cf8;
	}
	.session-badge {
		background: #1c2236;
		border: 1px solid #262d44;
		border-radius: 8px;
		padding: 3px 10px;
		font-size: 12px;
		color: #8892b0;
	}
	.topbar-right {
		margin-left: auto;
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.node-count {
		font-size: 13px;
		color: #8892b0;
	}
	.node-count b {
		color: #818cf8;
	}

	.btn {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 0 16px;
		height: 38px;
		border-radius: 10px;
		font-weight: 600;
		font-size: 13px;
		cursor: pointer;
		border: none;
		transition: all 0.18s;
	}
	.btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.btn-primary {
		background: linear-gradient(135deg, #6366f1, #7c3aed);
		color: #fff;
	}
	.btn-primary:hover:not(:disabled) {
		filter: brightness(1.1);
	}
	.btn-ghost {
		background: transparent;
		color: #8892b0;
		border: 1px solid #262d44;
	}
	.btn-ghost:hover {
		background: #1c2236;
		color: #e8eaf6;
	}
	.btn-green {
		background: linear-gradient(135deg, #16a34a, #22c55e);
		color: #fff;
	}
	.btn-orange {
		background: linear-gradient(135deg, #c2410c, #f97316);
		color: #fff;
	}
	.btn-sm {
		height: 32px;
		padding: 0 12px;
		font-size: 12px;
	}

	.editor-layout {
		display: flex;
		height: calc(100vh - 56px);
		overflow: hidden;
	}

	.toolbar {
		width: 58px;
		background: #141828;
		border-right: 1px solid #262d44;
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 12px 0;
		gap: 6px;
		flex-shrink: 0;
	}
	.tool-btn {
		width: 42px;
		height: 42px;
		border-radius: 10px;
		background: transparent;
		border: 1px solid transparent;
		display: grid;
		place-items: center;
		font-size: 18px;
		cursor: pointer;
		transition: 0.15s;
		color: #8892b0;
	}
	.tool-btn:hover {
		background: #1c2236;
		border-color: #262d44;
		color: #e8eaf6;
	}
	.tool-btn.active {
		background: rgba(99, 102, 241, 0.15);
		border-color: #6366f1;
		color: #818cf8;
	}
	.tool-sep {
		width: 32px;
		height: 1px;
		background: #262d44;
		margin: 4px 0;
	}

	.canvas-wrap {
		flex: 1;
		position: relative;
		overflow: hidden;
		background: radial-gradient(ellipse at 20% 20%, rgba(99, 102, 241, 0.06), transparent 55%),
			radial-gradient(ellipse at 80% 80%, rgba(124, 58, 237, 0.05), transparent 55%), #0b0e1a;
		cursor: crosshair;
	}
	.canvas-wrap::before {
		content: '';
		position: absolute;
		inset: 0;
		background-image: radial-gradient(circle, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
		background-size: 28px 28px;
		pointer-events: none;
	}
	.edges-svg {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: visible;
	}

	.mm-node {
		position: absolute;
		transform: translate(-50%, -50%);
		cursor: grab;
		user-select: none;
		z-index: 2;
	}
	.mm-node:active {
		cursor: grabbing;
	}
	.mm-node .node-label {
		display: block;
		padding: 10px 18px;
		border-radius: 12px;
		font-size: 13px;
		font-weight: 600;
		white-space: nowrap;
		border: 2px solid transparent;
		transition: 0.2s;
		background: #141828;
		border-color: var(--nc, #262d44);
		color: #e8eaf6;
	}
	.mm-node.central .node-label {
		background: linear-gradient(135deg, #6366f1, #7c3aed);
		color: #fff;
		font-size: 15px;
		padding: 14px 24px;
		border-radius: 16px;
		box-shadow: 0 8px 28px rgba(99, 102, 241, 0.4);
		border-color: transparent;
	}
	.mm-node.child:hover .node-label {
		border-color: var(--nc);
		box-shadow: 0 4px 16px rgba(99, 102, 241, 0.2);
	}
	.mm-node.selected .node-label {
		border-color: #818cf8 !important;
		box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25);
	}
	.mm-node.connecting .node-label {
		border-color: #22c55e !important;
		box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.25);
	}
	.node-input {
		background: #1c2236;
		border: 2px solid #6366f1;
		border-radius: 8px;
		padding: 8px 12px;
		font-size: 13px;
		font-weight: 600;
		color: #e8eaf6;
		outline: none;
		min-width: 120px;
		font-family: inherit;
	}

	.hint {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
		color: #4a5568;
		pointer-events: none;
	}
	.hint p {
		margin: 6px 0;
		font-size: 14px;
		line-height: 1.6;
	}

	.suggestions-panel {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		background: #141828;
		border: 1px solid #262d44;
		border-radius: 16px;
		padding: 24px 28px;
		max-width: 500px;
		width: 90%;
		text-align: center;
		z-index: 10;
	}
	.suggestions-title {
		font-size: 14px;
		color: #8892b0;
		margin-bottom: 16px;
		line-height: 1.5;
	}
	.suggestions-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		justify-content: center;
		margin-bottom: 20px;
	}
	.suggestion-chip {
		padding: 7px 14px;
		border-radius: 8px;
		background: rgba(99, 102, 241, 0.12);
		color: #818cf8;
		border: 1px solid rgba(99, 102, 241, 0.3);
		cursor: pointer;
		font-size: 13px;
		font-weight: 600;
		transition: 0.15s;
	}
	.suggestion-chip:hover {
		background: rgba(99, 102, 241, 0.25);
		border-color: #6366f1;
	}
	.btn-skip {
		background: transparent;
		border: none;
		color: #4a5568;
		font-size: 12px;
		cursor: pointer;
		text-decoration: underline;
	}

	.right-panel {
		width: 200px;
		background: #141828;
		border-left: 1px solid #262d44;
		padding: 16px;
		display: flex;
		flex-direction: column;
		gap: 10px;
		flex-shrink: 0;
	}
	.panel-title {
		font-size: 11px;
		font-weight: 600;
		color: #4a5568;
		text-transform: uppercase;
		letter-spacing: 0.07em;
	}
	.swatches {
		display: flex;
		gap: 7px;
		flex-wrap: wrap;
	}
	.swatch {
		width: 24px;
		height: 24px;
		border-radius: 6px;
		cursor: pointer;
		border: 2px solid transparent;
		transition: 0.15s;
	}
	.swatch:hover,
	.swatch.active {
		border-color: #fff;
		transform: scale(1.15);
	}
	.panel-hint {
		font-size: 12px;
		color: #4a5568;
		line-height: 1.6;
	}

	.overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.7);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 100;
		backdrop-filter: blur(4px);
	}
	.result-card {
		background: #141828;
		border: 1px solid #262d44;
		border-radius: 20px;
		padding: 40px 44px;
		max-width: 520px;
		width: 90%;
		text-align: center;
	}
	.result-card.success {
		border-color: rgba(34, 197, 94, 0.3);
	}
	.result-card.improve {
		border-color: rgba(249, 115, 22, 0.3);
	}
	.result-badge {
		display: inline-flex;
		align-items: center;
		padding: 8px 20px;
		border-radius: 50px;
		font-weight: 700;
		font-size: 13px;
		margin-bottom: 20px;
	}
	.badge-success {
		background: rgba(34, 197, 94, 0.12);
		color: #22c55e;
		border: 1px solid rgba(34, 197, 94, 0.3);
	}
	.badge-warn {
		background: rgba(249, 115, 22, 0.12);
		color: #f97316;
		border: 1px solid rgba(249, 115, 22, 0.3);
	}
	.result-card h2 {
		font-size: 22px;
		margin: 0 0 12px;
	}
	.result-card p {
		color: #8892b0;
		font-size: 14px;
		line-height: 1.6;
		margin-bottom: 20px;
	}
	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		justify-content: center;
		margin-bottom: 24px;
	}
	.chip {
		padding: 5px 14px;
		border-radius: 8px;
		font-size: 12px;
		font-weight: 600;
		background: rgba(99, 102, 241, 0.12);
		color: #818cf8;
		border: 1px solid rgba(99, 102, 241, 0.2);
	}
	.missing-list {
		list-style: none;
		text-align: left;
		padding: 0;
		margin: 0 0 24px;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	.missing-list li {
		padding: 10px 14px;
		background: #1c2236;
		border-radius: 10px;
		font-size: 13.5px;
		color: #8892b0;
	}
	.missing-list li strong {
		color: #e8eaf6;
		display: block;
	}
	.result-actions {
		display: flex;
		gap: 12px;
		justify-content: center;
		flex-wrap: wrap;
	}
</style>
