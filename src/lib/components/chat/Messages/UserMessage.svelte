<script lang="ts">
	import dayjs from 'dayjs';
	import { toast } from 'svelte-sonner';
	import { tick, getContext, onMount } from 'svelte';

	import { models, settings } from '$lib/stores';
	import { user as _user } from '$lib/stores';
	import { copyToClipboard as _copyToClipboard, formatDate } from '$lib/utils';

	import Name from './Name.svelte';
	import ProfileImage from './ProfileImage.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import FileItem from '$lib/components/common/FileItem.svelte';
	import Markdown from './Markdown.svelte';
	import Image from '$lib/components/common/Image.svelte';
	import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';

	import localizedFormat from 'dayjs/plugin/localizedFormat';

	const i18n = getContext('i18n');
	dayjs.extend(localizedFormat);

	export let user;

	export let history;
	export let messageId;

	export let siblings;

	export let showPreviousMessage: Function;
	export let showNextMessage: Function;

	export let editMessage: Function;
	export let deleteMessage: Function;

	export let isFirstMessage: boolean;
	export let readOnly: boolean;

	let showDeleteConfirm = false;

	let edit = false;
	let editedContent = '';
	let messageEditTextAreaElement: HTMLTextAreaElement;

	let message = JSON.parse(JSON.stringify(history.messages[messageId]));
	$: if (history.messages) {
		if (JSON.stringify(message) !== JSON.stringify(history.messages[messageId])) {
			message = JSON.parse(JSON.stringify(history.messages[messageId]));
		}
	}

	const copyToClipboard = async (text) => {
		const res = await _copyToClipboard(text);
		if (res) {
			toast.success($i18n.t('Copying to clipboard was successful!'));
		}
	};

	const editMessageHandler = async () => {
		edit = true;
		editedContent = message.content;

		await tick();

		messageEditTextAreaElement.style.height = '';
		messageEditTextAreaElement.style.height = `${messageEditTextAreaElement.scrollHeight}px`;

		messageEditTextAreaElement?.focus();
	};

	const editMessageConfirmHandler = async (submit = true) => {
		editMessage(message.id, editedContent, submit);

		edit = false;
		editedContent = '';
	};

	const cancelEditMessage = () => {
		edit = false;
		editedContent = '';
	};

	const deleteMessageHandler = async () => {
		deleteMessage(message.id);
	};

	onMount(() => {
		// console.log('UserMessage mounted');
	});
</script>

<DeleteConfirmDialog
	bind:show={showDeleteConfirm}
	title={$i18n.t('Delete message?')}
	on:confirm={() => {
		deleteMessageHandler();
	}}
/>

<!-- Removed from the code after redesigning the chat ui -->

<!-- <div class=" flex w-full user-message" dir={$settings.chatDirection} id="message-{message.id}">
    {#if !($settings?.chatBubble ?? true)}
        <div class={`shrink-0 ${($settings?.chatDirection ?? 'LTR') === 'LTR' ? 'mr-3' : 'ml-3'}`}>
            <ProfileImage
                src={message.user
                    ? ($models.find((m) => m.id === message.user)?.info?.meta?.profile_image_url ??
                        '/user.png')
                    : (user?.profile_image_url ?? '/user.png')}
                className={'size-8'}
            />
        </div>
    {/if}
    <div class="flex-auto w-0 max-w-full pl-1">
        {#if !($settings?.chatBubble ?? true)}
            <div>
                <Name>
                    {#if message.user}
                        {$i18n.t('You')}
                        <span class=" text-gray-500 text-sm font-medium">{message?.user ?? ''}</span>
                    {:else if $settings.showUsername || $_user.name !== user.name}
                        {user.name}
                    {:else}
                        {$i18n.t('You')}
                    {/if}

                    {#if message.timestamp}
                        <div
                            class=" self-center text-xs invisible group-hover:visible text-gray-400 font-medium first-letter:capitalize ml-0.5 translate-y-[1px]"
                        >
                            <Tooltip content={dayjs(message.timestamp * 1000).format('LLLL')}>
                                <span class="line-clamp-1">{formatDate(message.timestamp * 1000)}</span>
                            </Tooltip>
                        </div>
                    {/if}
                </Name>-->
<div
	class="flex w-full user-message justify-end"
	dir={$settings.chatDirection}
	id="message-{message.id}"
>
	<div class="flex-auto w-0 max-w-full pl-1 pt-2">
		<div class="w-full">
			<div class="flex justify-end items-start gap-3">
				<div
					class="flex items-start max-w-full bg-white dark:bg-gray-900 rounded-lg shadow-md py-2 px-4"
				>
					{#if !readOnly}
						<button
							class="p-1.5 text-gray-400 hover:text-gray-600 transition edit-user-message-button"
							on:click={() => {
								editMessageHandler();
							}}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke-width="2.3"
								stroke="currentColor"
								class="w-4 h-4"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125"
								/>
							</svg>
						</button>
					{/if}

					<div class="flex-1 px-2 p-4">
						{#if message.content}
							<Markdown id={message.id} content={message.content} />
						{/if}
					</div>
				</div>

				<div class="shrink-0">
					<ProfileImage
						src={message.user
							? ($models.find((m) => m.id === message.user)?.info?.meta?.profile_image_url ??
								'/user.png')
							: (user?.profile_image_url ?? '/user.png')}
						className={'size-8'}
					/>
				</div>
			</div>

			{#if message.files}
				<div class="mt-2.5 mb-1 w-full flex flex-col justify-end overflow-x-auto gap-1 flex-wrap">
					{#each message.files as file}
						<div class="self-end">
							{#if file.type === 'image'}
								<Image src={file.url} imageClassName=" max-h-96 rounded-lg" />
							{:else}
								<FileItem
									item={file}
									url={file.url}
									name={file.name}
									type={file.type}
									size={file?.size}
									colorClassName="bg-white dark:bg-gray-850 "
								/>
							{/if}
						</div>
					{/each}
				</div>
			{/if}

			{#if edit === true}
				<div class="w-full bg-white dark:bg-gray-800 rounded-lg shadow-md px-5 py-3 mb-2">
					<div class="max-h-96 overflow-auto">
						<textarea
							id="message-edit-{message.id}"
							bind:this={messageEditTextAreaElement}
							class="bg-transparent outline-hidden w-full resize-none"
							bind:value={editedContent}
							on:input={(e) => {
								e.target.style.height = '';
								e.target.style.height = `${e.target.scrollHeight}px`;
							}}
							on:keydown={(e) => {
								if (e.key === 'Escape') {
									document.getElementById('close-edit-message-button')?.click();
								}

								const isCmdOrCtrlPressed = e.metaKey || e.ctrlKey;
								const isEnterPressed = e.key === 'Enter';

								if (isCmdOrCtrlPressed && isEnterPressed) {
									document.getElementById('confirm-edit-message-button')?.click();
								}
							}}
						/>
					</div>

					<div class="mt-2 mb-1 flex justify-between text-sm font-medium">
						<div>
							<button
								id="save-edit-message-button"
								class="px-4 py-2 bg-gray-50 hover:bg-gray-100 border text-gray-700 transition rounded-3xl"
								on:click={() => {
									editMessageConfirmHandler(false);
								}}
							>
								{$i18n.t('Save')}
							</button>
						</div>

						<div class="flex space-x-1.5">
							<button
								id="close-edit-message-button"
								class="px-4 py-2 bg-white hover:bg-gray-100 text-gray-800 transition rounded-3xl"
								on:click={() => {
									cancelEditMessage();
								}}
							>
								{$i18n.t('Cancel')}
							</button>

							<button
								id="confirm-edit-message-button"
								class="px-4 py-2 bg-gray-900 hover:bg-gray-850 text-gray-100 transition rounded-3xl"
								on:click={() => {
									editMessageConfirmHandler();
								}}
							>
								{$i18n.t('Send')}
							</button>
						</div>
					</div>
				</div>
			{/if}

			<div class="flex justify-end mt-1 space-x-2 text-gray-600">
				{#if siblings.length > 1}
					<div class="flex self-center" dir="ltr">
						<button
							class="self-center p-1 hover:bg-black/5 hover:text-black rounded-md transition"
							on:click={() => {
								showPreviousMessage(message);
							}}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
								stroke-width="2.5"
								class="size-3.5"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M15.75 19.5 8.25 12l7.5-7.5"
								/>
							</svg>
						</button>

						<div class="text-sm tracking-widest font-semibold self-center">
							{siblings.indexOf(message.id) + 1}/{siblings.length}
						</div>

						<button
							class="self-center p-1 hover:bg-black/5 hover:text-black rounded-md transition"
							on:click={() => {
								showNextMessage(message);
							}}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
								stroke-width="2.5"
								class="size-3.5"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="m8.25 4.5 7.5 7.5-7.5 7.5"
								/>
							</svg>
						</button>
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>
