<script lang="ts">
	import { getContext } from 'svelte';
	import { messageQueue, type QueuedMessage } from '$lib/stores';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	
	const i18n = getContext('i18n');
	
	export let onSendNow: (message: QueuedMessage) => void = () => {};
	
	let expanded = false;
	let editingId: string | null = null;
	let editContent: string = '';
	
	function startEdit(message: QueuedMessage) {
		editingId = message.id;
		editContent = message.content;
	}
	
	function saveEdit(id: string) {
		messageQueue.update(queue => 
			queue.map(msg => 
				msg.id === id ? { ...msg, content: editContent } : msg
			)
		);
		editingId = null;
		editContent = '';
	}
	
	function cancelEdit() {
		editingId = null;
		editContent = '';
	}
	
	function deleteMessage(id: string) {
		messageQueue.update(queue => queue.filter(msg => msg.id !== id));
	}
	
	function sendNow(message: QueuedMessage) {
		messageQueue.update(queue => queue.filter(msg => msg.id !== message.id));
		onSendNow(message);
	}
	
	function toggleExpanded() {
		expanded = !expanded;
	}
</script>

{#if $messageQueue.length > 0}
	<div class="queue-compact mb-2">
		<!-- Collapsed View -->
		<button
			on:click={toggleExpanded}
			class="w-full flex items-center justify-between px-3 py-1.5 bg-black/15 backdrop-blur-sm 
			       border border-white/10 rounded-t-lg hover:bg-black/20 transition-colors group
			       {expanded ? 'rounded-b-none' : 'rounded-lg'}"
		>
			<div class="flex items-center gap-2">
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3.5 h-3.5 text-white/60">
					<path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				<span class="text-xs text-white/70">{$messageQueue.length} queued</span>
			</div>
			<svg 
				xmlns="http://www.w3.org/2000/svg" 
				fill="none" 
				viewBox="0 0 24 24" 
				stroke-width="2" 
				stroke="currentColor" 
				class="w-3.5 h-3.5 text-white/50 transition-transform {expanded ? 'rotate-180' : ''}"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
			</svg>
		</button>
		
		<!-- Expanded View -->
		{#if expanded}
			<div class="max-h-40 overflow-y-auto bg-black/10 backdrop-blur-sm border border-white/10 border-t-0 rounded-b-lg">
				{#each $messageQueue as message, index (message.id)}
					<div class="group relative px-3 py-2 border-b border-white/5 last:border-b-0 hover:bg-black/10 transition-colors">
						{#if editingId === message.id}
							<!-- Edit Mode -->
							<div class="flex flex-col gap-1.5">
								<textarea
									bind:value={editContent}
									class="w-full px-2 py-1.5 bg-white/10 border border-white/20 rounded text-white text-xs resize-none focus:outline-none focus:border-blue-400/50"
									rows="2"
									placeholder="Edit..."
								/>
								<div class="flex items-center gap-1.5">
									<button
										on:click={() => saveEdit(message.id)}
										class="px-2 py-1 bg-blue-500/80 hover:bg-blue-500 text-white text-xs rounded transition-colors"
									>
										Save
									</button>
									<button
										on:click={cancelEdit}
										class="px-2 py-1 bg-gray-500/80 hover:bg-gray-500 text-white text-xs rounded transition-colors"
									>
										Cancel
									</button>
								</div>
							</div>
						{:else}
							<!-- Display Mode -->
							<div class="flex items-start gap-2">
								<span class="flex-shrink-0 w-4 h-4 flex items-center justify-center bg-white/10 rounded-full text-white/50 text-[10px] font-medium">
									{index + 1}
								</span>
								<p class="flex-1 text-xs text-white/70 line-clamp-1">{message.content}</p>
								<div class="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
									<Tooltip content="Send" placement="top">
										<button
											on:click={() => sendNow(message)}
											class="p-1 hover:bg-white/10 rounded transition-colors"
										>
											<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3 text-green-400">
												<path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
											</svg>
										</button>
									</Tooltip>
									<Tooltip content="Edit" placement="top">
										<button
											on:click={() => startEdit(message)}
											class="p-1 hover:bg-white/10 rounded transition-colors"
										>
											<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3 text-blue-400">
												<path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
											</svg>
										</button>
									</Tooltip>
									<Tooltip content="Delete" placement="top">
										<button
											on:click={() => deleteMessage(message.id)}
											class="p-1 hover:bg-white/10 rounded transition-colors"
										>
											<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3 text-red-400">
												<path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
											</svg>
										</button>
									</Tooltip>
								</div>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</div>
{/if}

<style>
	.queue-compact {
		animation: fadeIn 0.3s ease-out;
	}
	
	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
	
	.line-clamp-1 {
		display: -webkit-box;
		-webkit-line-clamp: 1;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>

