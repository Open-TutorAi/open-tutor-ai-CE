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

		// 1. Fetch course details to get the latest chat_id from backend
		let courseDetail: any = null;
		try {
			courseDetail = await getCourseById(token, courseId);
			console.log('[Learn Page] Course details loaded:', {
				courseId,
				hasChatId: !!courseDetail?.chat_id,
				chatId: courseDetail?.chat_id
			});

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
				console.log('[Learn Page] Found resumeCourseChat:', { rCourseId, rChatId, currentCourseId: courseId });

				if (rCourseId === courseId && rChatId) {
					resumeChatId = rChatId;
					console.log('[Learn Page] Using resumed chat ID:', resumeChatId);
				}
			} catch (e) {
				console.error('[Learn Page] Error parsing resumeCourseChat:', e);
			}

			// Always clean up after reading
			localStorage.removeItem('resumeCourseChat');
		}

		// Fallback to backend saved chat_id
		if (!resumeChatId && courseDetail?.chat_id) {
			resumeChatId = courseDetail.chat_id;
			console.log('[Learn Page] Using backend chat_id:', resumeChatId);
		}

		if (resumeChatId) {
			// Existing chat: pass chatId directly to Chat component
			console.log('[Learn Page] Resuming existing chat:', resumeChatId);
			localStorage.removeItem('pendingCourseData');

			resolvedChatId = resumeChatId;

			// Store course-chat mapping so Chat.svelte can identify courseId
			localStorage.setItem(`course-chat-${resumeChatId}`, courseId);
		} else {
			// New chat flow
			console.log('[Learn Page] Starting new chat for course:', courseId);
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
				const success = event.detail?.success;

				console.log('[Learn Page] chatCreated event received:', {
					newChatId,
					success,
					chatSaved,
					shouldSave: newChatId && success && !chatSaved
				});

				if (newChatId && success && !chatSaved) {
					chatSaved = true;

					console.log('[Learn Page] Saving chat_id to backend:', {
						courseId,
						newChatId,
						token: token ? 'present' : 'missing'
					});

					saveCourseChatId(token, courseId, newChatId)
						.then(() => {
							console.log('[Learn Page] Successfully saved chat_id:', newChatId);
						})
						.catch((err) => {
							console.error('[Learn Page] Failed to save course chat_id:', err);
							// Try again after a short delay
							setTimeout(() => {
								saveCourseChatId(token, courseId, newChatId)
									.then(() => {
										console.log('[Learn Page] Retry: Successfully saved chat_id:', newChatId);
									})
									.catch((retryErr) => {
										console.error('[Learn Page] Retry failed for chat_id:', retryErr);
									});
							}, 2000);
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