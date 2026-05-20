<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import Chat from '$lib/components/student/tutor/Chat.svelte';
	import { getCourseById, saveCourseChatId } from '$lib/apis/courses';

	let courseId: string;
	let chatSaved = false;
	let ready = false;
	let resolvedChatId = ''; // Final resolved chat ID

	onMount(async () => {
		courseId = $page.params.id;

		if (!courseId) {
			goto('/student/classrooms');
			return;
		}

		const token = localStorage.getItem('token') ?? '';

		// 1. Fetch course details
		let courseDetail: any = null;
		try {
			courseDetail = await getCourseById(token, courseId);

			if (courseDetail) {
				localStorage.setItem(
					'activeCourseData',
					JSON.stringify({
						id: courseId,
						chapters: courseDetail.chapters ?? []
					})
				);
			}
		} catch (e) {
			console.warn('Could not fetch course chapters:', e);
		}

		// 2. Check if there is a chat to resume
		const resumeRaw = localStorage.getItem('resumeCourseChat');
		let resumeChatId: string | null = null;

		if (resumeRaw) {
			try {
				const { courseId: rCourseId, chatId: rChatId } = JSON.parse(resumeRaw);

				if (rCourseId === courseId && rChatId) {
					resumeChatId = rChatId;
				}
			} catch {}

			localStorage.removeItem('resumeCourseChat');
		}

		// Fallback to backend saved chat_id
		if (!resumeChatId && courseDetail?.chat_id) {
			resumeChatId = courseDetail.chat_id;
		}

		if (resumeChatId) {
			// Existing chat: pass chatId directly to Chat component
			localStorage.removeItem('pendingCourseData');

			resolvedChatId = resumeChatId;

			// Store course-chat mapping so Chat.svelte can identify courseId
			localStorage.setItem(`course-chat-${resumeChatId}`, courseId);
		} else {
			// New chat flow
			localStorage.setItem(
				'pendingCourseData',
				JSON.stringify({
					id: courseId,
					type: 'course'
				})
			);

			resolvedChatId = '';
		}

		ready = true;

		// Listen for newly created chats
		if (typeof window !== 'undefined') {
			if (!window.openTutorEvents) {
				window.openTutorEvents = new EventTarget();
			}

			const handler = (event: CustomEvent) => {
				const newChatId = event.detail?.chatId;

				if (newChatId && event.detail?.success && !chatSaved) {
					chatSaved = true;

					saveCourseChatId(token, courseId, newChatId).catch((err) => {
						console.error('Failed to save course chat_id:', err);
					});
				}
			};

			window.openTutorEvents.addEventListener(
				'chatCreated',
				handler as EventListener
			);

			return () => {
				window.openTutorEvents?.removeEventListener(
					'chatCreated',
					handler as EventListener
				);
			};
		}
	});

	onDestroy(() => {
		// Do not remove activeCourseData here
	});
</script>

{#if ready}
	<!-- chatIdProp allows Chat.svelte to load an existing chat without redirect -->
	<Chat
		chatIdProp={resolvedChatId}
		courseIdProp={courseId}
	/>
{/if}