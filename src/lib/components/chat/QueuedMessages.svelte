<script lang="ts">
	import { getContext } from 'svelte';
	import { messageQueue, type QueuedMessage } from '$lib/stores';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	
	const i18n = getContext('i18n');
	
	export let onSendNow: (message: QueuedMessage) => void = () => {};
	
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
</script>

{#if $messageQueue.length > 0}
	<div class="queued-messages-container mb-3">
		<div class="queued-header flex items-center gap-2 px-4 py-2 bg-black/10 backdrop-blur-sm border-b border-white/10">
			<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-white/70">
				<path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			<span class="text-xs font-medium text-white/70">
				{$messageQueue.length} {$messageQueue.length === 1 ? 'Queued' : 'Queued'}
			</span>
		</div>
		
		<div class="queued-list max-h-48 overflow-y-auto">
			{#each $messageQueue as message, index (message.id)}
				<div class="queued-item group relative px-4 py-3 bg-black/5 hover:bg-black/10 border-b border-white/5 transition-colors">
					{#if editingId === message.id}
						<!-- Edit Mode -->
						<div class="flex flex-col gap-2">
							<textarea
								bind:value={editContent}
								class="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm resize-none focus:outline-none focus:border-blue-400/50"
								rows="2"
								placeholder="Edit message..."
							/>
							<div class="flex items-center gap-2">
								<button
									on:click={() => saveEdit(message.id)}
									class="px-3 py-1.5 bg-blue-500/80 hover:bg-blue-500 text-white text-xs rounded-md transition-colors"
								>
									Save
								</button>
								<button
									on:click={cancelEdit}
									class="px-3 py-1.5 bg-gray-500/80 hover:bg-gray-500 text-white text-xs rounded-md transition-colors"
								>
									Cancel
								</button>
							</div>
						</div>
					{:else}
						<!-- Display Mode -->
						<div class="flex items-start gap-3">
							<div class="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-white/10 rounded-full text-white/60 text-xs font-medium">
								{index + 1}
							</div>
							<div class="flex-1 min-w-0">
								<p class="text-sm text-white/80 line-clamp-2">{message.content}</p>
								{#if message.files && message.files.length > 0}
									<div class="mt-1 flex items-center gap-1 text-xs text-white/50">
										<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
											<path stroke-linecap="round" stroke-linejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
										</svg>
										{message.files.length} file{message.files.length > 1 ? 's' : ''}
									</div>
								{/if}
							</div>
							<div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
								<Tooltip content="Send now" placement="top">
									<button
										on:click={() => sendNow(message)}
										class="p-1.5 hover:bg-white/10 rounded-md transition-colors"
										aria-label="Send now"
									>
										<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-green-400">
											<path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
										</svg>
									</button>
								</Tooltip>
								<Tooltip content="Edit" placement="top">
									<button
										on:click={() => startEdit(message)}
										class="p-1.5 hover:bg-white/10 rounded-md transition-colors"
										aria-label="Edit"
									>
										<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-blue-400">
											<path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
										</svg>
									</button>
								</Tooltip>
								<Tooltip content="Delete" placement="top">
									<button
										on:click={() => deleteMessage(message.id)}
										class="p-1.5 hover:bg-white/10 rounded-md transition-colors"
										aria-label="Delete"
									>
										<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-red-400">
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
	</div>
{/if}

<style>
	.queued-messages-container {
		animation: slideDown 0.3s ease-out;
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border-radius: 0.75rem;
		overflow: hidden;
		border: 1px solid rgba(255, 255, 255, 0.1);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}
	
	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	
	.queued-list {
		scrollbar-width: thin;
		scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
	}
	
	.queued-list::-webkit-scrollbar {
		width: 6px;
	}
	
	.queued-list::-webkit-scrollbar-track {
		background: transparent;
	}
	
	.queued-list::-webkit-scrollbar-thumb {
		background-color: rgba(255, 255, 255, 0.2);
		border-radius: 3px;
	}
	
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>

