<script>
	import { onDestroy, onMount, tick, getContext, createEventDispatcher } from 'svelte';
	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import Markdown from './Markdown.svelte';
	import QuizWidget from './QuizWidget.svelte';
	import { chatId, mobile, showArtifacts, showControls, showOverview } from '$lib/stores';
	import FloatingButtons from '../ContentRenderer/FloatingButtons.svelte';
	import { createMessagesList } from '$lib/utils';

	export let id;
	export let content;
	export let history;
	export let model = null;
	export let sources = null;
	export let save = false;
	export let floatingButtons = true;
	export let onSourceClick = () => {};
	export let onTaskClick = () => {};
	export let onAddMessages = () => {};

	let contentContainerElement;
	let floatingButtonsElement;

	function parseQuizJson(text) {
		if (!text) return null;
		try {
			const clean = text.replace(/```json|```/g, '').trim();
			const start = clean.indexOf('{');
			const end = clean.lastIndexOf('}');
			if (start === -1 || end === -1) return null;
			const parsed = JSON.parse(clean.substring(start, end + 1));
			if (parsed?.questions && Array.isArray(parsed.questions) && parsed.questions.length > 0) {
				return parsed;
			}
		} catch {}
		return null;
	}

	$: quizData = parseQuizJson(content);

	const updateButtonPosition = (event) => {
		const buttonsContainerElement = document.getElementById(`floating-buttons-${id}`);
		if (
			!contentContainerElement?.contains(event.target) &&
			!buttonsContainerElement?.contains(event.target)
		) {
			closeFloatingButtons();
			return;
		}

		setTimeout(async () => {
			await tick();
			if (!contentContainerElement?.contains(event.target)) return;
			let selection = window.getSelection();
			if (selection.toString().trim().length > 0) {
				const range = selection.getRangeAt(0);
				const rect = range.getBoundingClientRect();
				const parentRect = contentContainerElement.getBoundingClientRect();
				const top = rect.bottom - parentRect.top;
				const left = rect.left - parentRect.left;
				if (buttonsContainerElement) {
					buttonsContainerElement.style.display = 'block';
					const spaceOnRight = parentRect.width - left;
					let halfScreenWidth = $mobile ? window.innerWidth / 2 : window.innerWidth / 3;
					if (spaceOnRight < halfScreenWidth) {
						const right = parentRect.right - rect.right;
						buttonsContainerElement.style.right = `${right}px`;
						buttonsContainerElement.style.left = 'auto';
					} else {
						buttonsContainerElement.style.left = `${left}px`;
						buttonsContainerElement.style.right = 'auto';
					}
					buttonsContainerElement.style.top = `${top + 5}px`;
				}
			} else {
				closeFloatingButtons();
			}
		}, 0);
	};

	const closeFloatingButtons = () => {
		const buttonsContainerElement = document.getElementById(`floating-buttons-${id}`);
		if (buttonsContainerElement) {
			buttonsContainerElement.style.display = 'none';
		}
		if (floatingButtonsElement) {
			floatingButtonsElement.closeHandler();
		}
	};

	const keydownHandler = (e) => {
		if (e.key === 'Escape') {
			closeFloatingButtons();
		}
	};

	onMount(() => {
		if (floatingButtons) {
			contentContainerElement?.addEventListener('mouseup', updateButtonPosition);
			document.addEventListener('mouseup', updateButtonPosition);
			document.addEventListener('keydown', keydownHandler);
		}
	});

	onDestroy(() => {
		if (floatingButtons) {
			contentContainerElement?.removeEventListener('mouseup', updateButtonPosition);
			document.removeEventListener('mouseup', updateButtonPosition);
			document.removeEventListener('keydown', keydownHandler);
		}
	});
</script>

<div bind:this={contentContainerElement}>
	{#if quizData}
		<QuizWidget {quizData} />
	{:else}
		<Markdown
			{id}
			{content}
			{model}
			{save}
			sourceIds={(sources ?? []).reduce((acc, s) => {
				let ids = [];
				s.document.forEach((document, index) => {
					if (model?.info?.meta?.capabilities?.citations == false) {
						ids.push('N/A');
						return ids;
					}
					const metadata = s.metadata?.[index];
					const id = metadata?.source ?? 'N/A';
					if (metadata?.name) {
						ids.push(metadata.name);
						return ids;
					}
					if (id.startsWith('http://') || id.startsWith('https://')) {
						ids.push(id);
					} else {
						ids.push(s?.source?.name ?? id);
					}
					return ids;
				});
				acc = [...acc, ...ids];
				return acc.filter((item, index) => acc.indexOf(item) === index);
			}, [])}
			{onSourceClick}
			{onTaskClick}
			on:update={(e) => {
				dispatch('update', e.detail);
			}}
			on:code={(e) => {
				const { lang, code } = e.detail;
				if (
					(['html', 'svg'].includes(lang) || (lang === 'xml' && code.includes('svg'))) &&
					!$mobile &&
					$chatId
				) {
					showArtifacts.set(true);
					showControls.set(true);
				}
			}}
		/>
	{/if}
</div>

{#if floatingButtons && model}
	<FloatingButtons
		bind:this={floatingButtonsElement}
		{id}
		model={model?.id}
		messages={createMessagesList(history, id)}
		onAdd={({ modelId, parentId, messages }) => {
			onAddMessages({ modelId, parentId, messages });
			closeFloatingButtons();
		}}
	/>
{/if}