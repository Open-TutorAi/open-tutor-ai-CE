<!-- chat page - Version complète avec instructions pédagogiques CALIBRÉES (longueur adaptée) + CORRECTION DES LANGUES + CORRECTION TABLEAUX RTL + CORRECTION LISTES NUMÉROTÉES -->

<script lang="ts">
	import { v4 as uuidv4 } from 'uuid';
	import { toast } from 'svelte-sonner';
	import mermaid from 'mermaid';
	import { PaneGroup, Pane, PaneResizer } from 'paneforge';

	import { getContext, onDestroy, onMount, tick } from 'svelte';
	const i18n: Writable<i18nType> = getContext('i18n');

	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	import { get, type Unsubscriber, type Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { TUTOR_BASE_URL } from '$lib/constants';
	import promptData  from './prompt.json';
	import { selectedLanguage } from '$lib/common/languageStore';

	import {
		chatId,
		chats,
		config,
		type Model,
		models,
		tags as allTags,
		settings,
		showSidebar,
		TUTOR_NAME,
		banners,
		user,
		socket,
		showControls,
		showCallOverlay,
		currentChatPage,
		temporaryChatEnabled,
		mobile,
		showOverview,
		chatTitle,
		showArtifacts,
		tools
	} from '$lib/stores';
	import {
		convertMessagesToHistory,
		copyToClipboard,
		getMessageContentParts,
		createMessagesList,
		extractSentencesForAudio,
		promptTemplate,
		splitStream,
		sleep,
		removeDetails,
		getPromptVariables
	} from '$lib/utils';

	import { generateChatCompletion } from '$lib/apis/ollama';
	import {
		addTagById,
		createNewChat,
		deleteTagById,
		deleteTagsById,
		getAllTags,
		getChatById,
		getChatList,
		getTagsById,
		updateChatById
	} from '$lib/apis/chats';
	import { generateOpenAIChatCompletion } from '$lib/apis/openai';
	import { processWeb, processWebSearch, processYoutubeVideo } from '$lib/apis/retrieval';
	import { createOpenAITextStream } from '$lib/apis/streaming';
	import { queryMemory } from '$lib/apis/memories';
	import { getAndUpdateUserLocation, getUserSettings } from '$lib/apis/users';
	import {
		chatCompleted,
		generateQueries,
		chatAction,
		generateMoACompletion,
		stopTask
	} from '$lib/apis';
	import { getTools } from '$lib/apis/tools';
	import { getSupportById } from '$lib/apis/supports';

	import Banner from '$lib/components/common/Banner.svelte';
	import MessageInput from '$lib/components/chat/MessageInput.svelte';
	import Messages from '$lib/components/chat/Messages.svelte';
	import Navbar from '$lib/components/student/tutor/ChatNavbar.svelte';
	import ChatControls from '$lib/components/chat/ChatControls.svelte';
	import EventConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Placeholder from '$lib/components/chat/Placeholder.svelte';
	import NotificationToast from '$lib/components/NotificationToast.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import AvatarChat from '$lib/components/chat/AvatarChat.svelte';

	$: if ($user) {
		console.log('User Permissions:', {
			role: $user.role,
			workspace: $user?.permissions?.workspace,
			chat: $user?.permissions?.chat,
			features: $user?.permissions?.features
		});
	}

	export let chatIdProp = '';

	let loading = false;
	const eventTarget = new EventTarget();
	let controlPane;
	let controlPaneComponent;
	let autoScroll = true;
	let processing = '';
	let messagesContainerElement: HTMLDivElement;
	let navbarElement;
	let showEventConfirmation = false;
	let eventConfirmationTitle = '';
	let eventConfirmationMessage = '';
	let eventConfirmationInput = false;
	let eventConfirmationInputPlaceholder = '';
	let eventConfirmationInputValue = '';
	let eventCallback = null;
	let chatIdUnsubscriber: Unsubscriber | undefined;
	let selectedModels = [''];
	let atSelectedModel: Model | undefined;
	let selectedModelIds = [];
	$: selectedModelIds = atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;
	let selectedToolIds = [];
	let imageGenerationEnabled = false;
	let webSearchEnabled = false;
	let codeInterpreterEnabled = false;
	let chat = null;
	let tags = [];
	let history = {
		messages: {},
		currentId: null
	};
	let taskId = null;
	let prompt = '';
	let chatFiles = [];
	let files = [];
	let params = {};

	// ─── CORRECTION RTL : variable réactive pour la direction ───────────────────
	$: currentDir = $selectedLanguage === 'ar' ? 'rtl' : 'ltr';
	// ────────────────────────────────────────────────────────────────────────────

	$: avatarActive = ($settings as any)?.avatarEnabled !== undefined ? ($settings as any).avatarEnabled : true;
	let avatarSpeaking = false;
	let currentAvatarMessage = '';

	const toggleAvatar = () => {
		settings.update((s) => {
			const updatedSettings = { ...s };
			(updatedSettings as any).avatarEnabled = !(($settings as any)?.avatarEnabled);
			return updatedSettings;
		});
		localStorage.setItem('settings', JSON.stringify($settings));
	};

	$: if (chatIdProp) {
		(async () => {
			loading = true;
			console.log(chatIdProp);
			prompt = '';
			files = [];
			selectedToolIds = [];
			webSearchEnabled = false;
			imageGenerationEnabled = false;

			if (chatIdProp && (await loadChat())) {
				await tick();
				loading = false;

				if (localStorage.getItem(`chat-input-${chatIdProp}`)) {
					try {
						const input = JSON.parse(localStorage.getItem(`chat-input-${chatIdProp}`));
						prompt = input.prompt;
						files = input.files;
						selectedToolIds = input.selectedToolIds;
						webSearchEnabled = input.webSearchEnabled;
						imageGenerationEnabled = input.imageGenerationEnabled;
					} catch (e) {}
				}
				window.setTimeout(() => scrollToBottom(), 0);
				const chatInput = document.getElementById('chat-input');
				chatInput?.focus();
			} else {
				await goto('/');
			}
		})();
	}

	$: if (selectedModels && chatIdProp !== '') {
		saveSessionSelectedModels();
	}

	const saveSessionSelectedModels = () => {
		if (selectedModels.length === 0 || (selectedModels.length === 1 && selectedModels[0] === '')) {
			return;
		}
		sessionStorage.selectedModels = JSON.stringify(selectedModels);
		console.log('saveSessionSelectedModels', selectedModels, sessionStorage.selectedModels);
	};

	$: if (selectedModels) {
		setToolIds();
	}

	$: if (atSelectedModel || selectedModels) {
		setToolIds();
	}

	const setToolIds = async () => {
		if (!$tools) {
			tools.set(await getTools(localStorage.token));
		}
		if (selectedModels.length !== 1 && !atSelectedModel) {
			return;
		}
		const model = atSelectedModel ?? $models.find((m) => m.id === selectedModels[0]);
		if (model) {
			selectedToolIds = (model?.info?.meta?.toolIds ?? []).filter((id) =>
				$tools.find((t) => t.id === id)
			);
		}
	};

	const showMessage = async (message) => {
		const _chatId = JSON.parse(JSON.stringify($chatId));
		let _messageId = JSON.parse(JSON.stringify(message.id));
		let messageChildrenIds = history.messages[_messageId].childrenIds;
		while (messageChildrenIds.length !== 0) {
			_messageId = messageChildrenIds.at(-1);
			messageChildrenIds = history.messages[_messageId].childrenIds;
		}
		history.currentId = _messageId;
		await tick();
		await tick();
		await tick();
		const messageElement = document.getElementById(`message-${message.id}`);
		if (messageElement) {
			messageElement.scrollIntoView({ behavior: 'smooth' });
		}
		await tick();
		saveChatHandler(_chatId, history);
	};

	const chatEventHandler = async (event, cb) => {
		console.log(event);
		if (event.chat_id === $chatId) {
			await tick();
			let message = history.messages[event.message_id];
			if (message) {
				const type = event?.data?.type ?? null;
				const data = event?.data?.data ?? null;
				if (type === 'status') {
					if (message?.statusHistory) {
						message.statusHistory.push(data);
					} else {
						message.statusHistory = [data];
					}
				} else if (type === 'source' || type === 'citation') {
					if (data?.type === 'code_execution') {
						if (!message?.code_executions) {
							message.code_executions = [];
						}
						const existingCodeExecutionIndex = message.code_executions.findIndex(
							(execution) => execution.id === data.id
						);
						if (existingCodeExecutionIndex !== -1) {
							message.code_executions[existingCodeExecutionIndex] = data;
						} else {
							message.code_executions.push(data);
						}
						message.code_executions = message.code_executions;
					} else {
						if (message?.sources) {
							message.sources.push(data);
						} else {
							message.sources = [data];
						}
					}
				} else if (type === 'chat:completion') {
					chatCompletionEventHandler(data, message, event.chat_id);
				} else if (type === 'chat:title') {
					chatTitle.set(data);
					currentChatPage.set(1);
					await chats.set(await getChatList(localStorage.token, $currentChatPage));
				} else if (type === 'chat:tags') {
					chat = await getChatById(localStorage.token, $chatId);
					allTags.set(await getAllTags(localStorage.token));
				} else if (type === 'message') {
					message.content += data.content;
				} else if (type === 'replace') {
					message.content = data.content;
				} else if (type === 'action') {
					if (data.action === 'continue') {
						const continueButton = document.getElementById('continue-response-button');
						if (continueButton) {
							continueButton.click();
						}
					}
				} else if (type === 'confirmation') {
					eventCallback = cb;
					eventConfirmationInput = false;
					showEventConfirmation = true;
					eventConfirmationTitle = data.title;
					eventConfirmationMessage = data.message;
				} else if (type === 'execute') {
					eventCallback = cb;
					try {
						const asyncFunction = new Function(`return (async () => { ${data.code} })()`);
						const result = await asyncFunction();
						if (cb) {
							cb(result);
						}
					} catch (error) {
						console.error('Error executing code:', error);
					}
				} else if (type === 'input') {
					eventCallback = cb;
					eventConfirmationInput = true;
					showEventConfirmation = true;
					eventConfirmationTitle = data.title;
					eventConfirmationMessage = data.message;
					eventConfirmationInputPlaceholder = data.placeholder;
					eventConfirmationInputValue = data?.value ?? '';
				} else if (type === 'notification') {
					const toastType = data?.type ?? 'info';
					const toastContent = data?.content ?? '';
					if (toastType === 'success') {
						toast.success(toastContent);
					} else if (toastType === 'error') {
						toast.error(toastContent);
					} else if (toastType === 'warning') {
						toast.warning(toastContent);
					} else {
						toast.info(toastContent);
					}
				} else {
					console.log('Unknown message type', data);
				}
				history.messages[event.message_id] = message;
			}
		}
	};

	const onMessageHandler = async (event: {
		origin: string;
		data: { type: string; text: string };
	}) => {
		if (event.origin !== window.origin) {
			return;
		}
		if (event.data.type === 'input:prompt') {
			console.debug(event.data.text);
			const inputElement = document.getElementById('chat-input');
			if (inputElement) {
				prompt = event.data.text;
				inputElement.focus();
			}
		}
		if (event.data.type === 'action:submit') {
			console.debug(event.data.text);
			if (prompt !== '') {
				await tick();
				submitPrompt(prompt);
			}
		}
		if (event.data.type === 'input:prompt:submit') {
			console.debug(event.data.text);
			if (prompt !== '') {
				await tick();
				submitPrompt(event.data.text);
			}
		}
	};

	onMount(async () => {
		console.log('mounted');
		if (typeof window !== 'undefined' && !window.openTutorEvents) {
			console.log('Creating global openTutorEvents EventTarget');
			window.openTutorEvents = new EventTarget();
		}
		window.openTutorEvents.addEventListener('chatCreated', (event: CustomEvent) => {
			if (event.detail && event.detail.success === false) {
				console.log('Detected failed chat creation, cleaning up');
				if (window.localStorage.getItem('pendingSupportData')) {
					window.localStorage.removeItem('pendingSupportData');
					toast.error($i18n.t('Support linking canceled due to chat creation failure'));
				}
			}
		});
		window.addEventListener('message', onMessageHandler);
		$socket?.on('chat-events', chatEventHandler);
		if (!$chatId) {
			chatIdUnsubscriber = chatId.subscribe(async (value) => {
				if (!value) {
					await initNewChat();
				}
			});
		} else {
			if ($temporaryChatEnabled) {
				await goto('/');
			}
		}
		if (localStorage.getItem(`chat-input-${chatIdProp}`)) {
			try {
				const input = JSON.parse(localStorage.getItem(`chat-input-${chatIdProp}`));
				prompt = input.prompt;
				files = input.files;
				selectedToolIds = input.selectedToolIds;
				webSearchEnabled = input.webSearchEnabled;
				imageGenerationEnabled = input.imageGenerationEnabled;
			} catch (e) {
				prompt = '';
				files = [];
				selectedToolIds = [];
				webSearchEnabled = false;
				imageGenerationEnabled = false;
			}
		}
		showControls.subscribe(async (value) => {
			if (controlPane && !$mobile) {
				try {
					if (value) {
						controlPaneComponent.openPane();
					} else {
						controlPane.collapse();
					}
				} catch (e) {}
			}
			if (!value) {
				showCallOverlay.set(false);
				showOverview.set(false);
				showArtifacts.set(false);
			}
		});
		const chatInput = document.getElementById('chat-input');
		chatInput?.focus();
		chats.subscribe(() => {});
	});

	onDestroy(() => {
		chatIdUnsubscriber?.();
		window.removeEventListener('message', onMessageHandler);
		$socket?.off('chat-events', chatEventHandler);
	});

	const uploadWeb = async (url) => {
		console.log(url);
		const fileItem = {
			type: 'doc',
			name: url,
			collection_name: '',
			status: 'uploading',
			url: url,
			error: ''
		};
		try {
			files = [...files, fileItem];
			const res = await processWeb(localStorage.token, '', url);
			if (res) {
				fileItem.status = 'uploaded';
				fileItem.collection_name = res.collection_name;
				fileItem.file = {
					...res.file,
					...fileItem.file
				};
				files = files;
			}
		} catch (e) {
			files = files.filter((f) => f.name !== url);
			toast.error(JSON.stringify(e));
		}
	};

	const uploadYoutubeTranscription = async (url) => {
		console.log(url);
		const fileItem = {
			type: 'doc',
			name: url,
			collection_name: '',
			status: 'uploading',
			context: 'full',
			url: url,
			error: ''
		};
		try {
			files = [...files, fileItem];
			const res = await processYoutubeVideo(localStorage.token, url);
			if (res) {
				fileItem.status = 'uploaded';
				fileItem.collection_name = res.collection_name;
				fileItem.file = {
					...res.file,
					...fileItem.file
				};
				files = files;
			}
		} catch (e) {
			files = files.filter((f) => f.name !== url);
			toast.error(`${e}`);
		}
	};

	// ============================================
	// INSTRUCTIONS PÉDAGOGIQUES — LONGUEUR ADAPTÉE (CORRECTION PRINCIPALE)
	// ============================================

	const getPedagogicalInstruction = (currentLang: string, isBeginner: boolean = true) => {

		// ════════════════════════════════════════════════════════════════
		// RÈGLE DE LANGUE STRICTE (inchangée)
		// ════════════════════════════════════════════════════════════════
		const strictLanguageRule = currentLang === 'fr' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    ⚠️ RÈGLE DE LANGUE ABSOLUE ⚠️                                  ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  TU DOIS RÉPONDRE UNIQUEMENT EN FRANÇAIS.                                        ║
║  AUCUN mot en anglais, arabe ou espagnol.                                        ║
║  Même si l'élève écrit en arabe, tu réponds en FRANÇAIS.                         ║
║  MÉLANGE DE LANGUES = RÉPONSE INCORRECTE                                         ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : currentLang === 'ar' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    ⚠️ قاعدة اللغة المطلقة ⚠️                                      ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  يجب عليك الإجابة بالعربية فقط. لا كلمات إنجليزية أو فرنسية.                     ║
║  📊 قواعد الجدول: عناوين بالعربية، أول عمود على اليمين، Markdown فقط.             ║
║  مثال صحيح: | القيمة | الوصف | العنوان |                                          ║
║  خلط اللغات = إجابة خاطئة                                                        ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : currentLang === 'en' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    ⚠️ ABSOLUTE LANGUAGE RULE ⚠️                                   ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  YOU MUST ANSWER ONLY IN ENGLISH. NO words in French, Arabic or Spanish.         ║
║  MIXING LANGUAGES = INCORRECT RESPONSE                                           ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    ⚠️ REGLA DE IDIOMA ABSOLUTA ⚠️                                 ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  DEBES RESPONDER SOLO EN ESPAÑOL. NO palabras en inglés, árabe o francés.        ║
║  MEZCLAR IDIOMAS = RESPUESTA INCORRECTA                                          ║
╚══════════════════════════════════════════════════════════════════════════════════╝
`;

		// ════════════════════════════════════════════════════════════════
		// RÈGLE POUR LES LISTES NUMÉROTÉES EN ARABE (VERSION CORRECTE)
		// ════════════════════════════════════════════════════════════════
		const listsRule = currentLang === 'ar' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    📋 قاعدة القوائم المرقّمة 📋                                    ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  استخدم دائماً الترتيب التصاعدي: 1، 2، 3...                                      ║
║                                                                                  ║
║  ✅ صحيح:                                                                        ║
║     1. أولاً                                                                     ║
║     2. ثانياً                                                                    ║
║     3. ثالثاً                                                                    ║
║                                                                                  ║
║  ❌ خطأ:                                                                         ║
║     3. ثالثاً                                                                    ║
║     2. ثانياً                                                                    ║
║     1. أولاً                                                                     ║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : '';

		// ════════════════════════════════════════════════════════════════
		// CORRECTION PRINCIPALE : LONGUEUR ADAPTÉE À LA QUESTION
		// ════════════════════════════════════════════════════════════════
		const richResponseRules = currentLang === 'fr' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║              📚 RÈGLES DE QUALITÉ DES RÉPONSES 📚                                 ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  ✅ LONGUEUR ADAPTÉE : Réponds en proportion de la question.                      ║
║     → Question simple ou courte → 2-3 paragraphes clairs et bien développés.     ║
║     → Question complexe ou détaillée → structure en sections avec exemples.      ║
║     → Ne résume pas brutalement. Ne rembourre pas inutilement.                   ║
║     → Une seule phrase sans développement = réponse incomplète = INTERDIT.       ║
║                                                                                  ║
║  ✅ EXEMPLES OBLIGATOIRES : Toujours au moins 1 exemple concret.                  ║
║     → Tiré de la vie réelle ou du cours, adapté au niveau de l'élève.            ║
║     → Utilise un tableau ou une liste si c'est plus clair.                       ║
║                                                                                  ║
║  ✅ STRUCTURE CLAIRE (selon la complexité) :                                      ║
║     → Définis les termes difficiles dès qu'ils apparaissent.                     ║
║     → Explique le POURQUOI et le COMMENT, pas seulement le QUOI.                 ║
║     → Pour les questions complexes, utilise des titres :                         ║
║       "📌 Définition", "💡 Exemple", "🔎 Explication", "📝 Résumé"                 ║
║     → Termine toujours par un résumé court et une question de vérification.      ║
║                                                                                  ║
║  ❌ INTERDIT :                                                                    ║
║     → Réponse d'une seule phrase sans aucun développement.                       ║
║     → Répétitions inutiles pour faire du volume.                                 ║
║     → Ignorer des parties de la question.                                        ║
║     → Mélanger les langues.                                                      ║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : currentLang === 'ar' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║              📚 قواعد جودة الإجابات 📚                                             ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  ✅ طول متناسب: أجب بما يتناسب مع حجم السؤال وتعقيده.                              ║
║     → سؤال بسيط أو قصير → فقرتان أو ثلاث واضحة ومطورة.                            ║
║     → سؤال معقد أو مفصل → هيكل بأقسام وأمثلة مفصلة.                               ║
║     → لا تلخص بشكل مفرط. لا تحشو بمعلومات غير مفيدة.                              ║
║     → جملة واحدة دون شرح = إجابة ناقصة = ممنوع.                                    ║
║                                                                                  ║
║  ✅ مثال إلزامي: دائماً مثال ملموس واحد على الأقل.                                   ║
║     → من الحياة الواقعية أو من الدرس، مناسب لمستوى الطالب.                         ║
║     → استخدم جدولاً أو قائمة إذا كان ذلك أوضح.                                     ║
║                                                                                  ║
║  ✅ هيكل واضح (حسب التعقيد):                                                      ║
║     → عرّف المصطلحات الصعبة فور ظهورها.                                            ║
║     → اشرح لماذا وكيف، ليس فقط ماذا.                                               ║
║     → للأسئلة المعقدة استخدم عناوين:                                               ║
║       "📌 التعريف"، "💡 مثال"، "🔎 شرح"، "📝 ملخص"                                  ║
║     → أنهِ دائماً بملخص قصير وسؤال للتحقق من الفهم.                                ║
║                                                                                  ║
║  ❌ ممنوع:                                                                        ║
║     → جملة واحدة دون أي شرح.                                                      ║
║     → تكرار غير مفيد لزيادة الحجم.                                                ║
║     → تجاهل أجزاء من السؤال. خلط اللغات.                                          ║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : currentLang === 'en' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║              📚 RESPONSE QUALITY RULES 📚                                         ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  ✅ PROPORTIONAL LENGTH: Answer in proportion to the question's complexity.       ║
║     → Simple or short question → 2-3 clear, well-developed paragraphs.           ║
║     → Complex or detailed question → structured sections with examples.           ║
║     → Don't over-summarize. Don't pad with unnecessary repetition.               ║
║     → One sentence with no development = incomplete answer = FORBIDDEN.          ║
║                                                                                  ║
║  ✅ MANDATORY EXAMPLE: Always give at least 1 concrete example.                   ║
║     → From real life or from the lesson, adapted to the student's level.         ║
║     → Use a table or list if it makes things clearer.                            ║
║                                                                                  ║
║  ✅ CLEAR STRUCTURE (based on complexity):                                        ║
║     → Define difficult terms as soon as they appear.                             ║
║     → Explain WHY and HOW, not just WHAT.                                        ║
║     → For complex questions, use titles:                                         ║
║       "📌 Definition", "💡 Example", "🔎 Explanation", "📝 Summary"                ║
║     → Always end with a short summary and a comprehension check question.        ║
║                                                                                  ║
║  ❌ FORBIDDEN:                                                                    ║
║     → One sentence with no development.                                          ║
║     → Unnecessary repetition to increase volume.                                 ║
║     → Ignoring parts of the question. Mixing languages.                          ║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : `
╔══════════════════════════════════════════════════════════════════════════════════╗
║              📚 REGLAS DE CALIDAD DE RESPUESTAS 📚                                ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  ✅ LONGITUD PROPORCIONAL: Responde según la complejidad de la pregunta.           ║
║     → Pregunta simple o corta → 2-3 párrafos claros y bien desarrollados.        ║
║     → Pregunta compleja → estructura en secciones con ejemplos.                  ║
║     → No resumas en exceso. No rellenes con repeticiones innecesarias.           ║
║     → Una sola frase sin desarrollo = respuesta incompleta = PROHIBIDO.          ║
║                                                                                  ║
║  ✅ EJEMPLO OBLIGATORIO: Siempre al menos 1 ejemplo concreto.                     ║
║     → De la vida real o del curso, adaptado al nivel del alumno.                 ║
║     → Usa una tabla o lista si resulta más claro.                                ║
║                                                                                  ║
║  ✅ ESTRUCTURA CLARA (según la complejidad):                                      ║
║     → Define los términos difíciles en cuanto aparezcan.                         ║
║     → Explica el POR QUÉ y el CÓMO, no solo el QUÉ.                              ║
║     → Para preguntas complejas usa títulos:                                      ║
║       "📌 Definición", "💡 Ejemplo", "🔎 Explicación", "📝 Resumen"                ║
║     → Termina siempre con un resumen corto y una pregunta de verificación.       ║
║                                                                                  ║
║  ❌ PROHIBIDO: una sola frase sin desarrollo, repeticiones innecesarias,          ║
║     ignorar partes de la pregunta, mezclar idiomas.                              ║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
`;

		// ════════════════════════════════════════════════════════════════
		// ADAPTATION AU NIVEAU (débutant vs avancé)
		// ════════════════════════════════════════════════════════════════
		const levelRules = isBeginner ? (currentLang === 'fr' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    🎯 ADAPTATION NIVEAU DÉBUTANT 🎯                               ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  • Vocabulaire simple, phrases claires.                                          ║
║  • Commence par un exemple concret de la vie quotidienne.                        ║
║  • Définis chaque mot difficile dès qu'il apparaît.                              ║
║  • Répète les idées importantes sous 2 formes différentes si nécessaire.         ║
║  • Utilise des schémas textuels (→, •, 1️⃣ 2️⃣ 3️⃣) pour guider.                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : currentLang === 'ar' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    🎯 تكيّف مستوى المبتدئين 🎯                                     ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  • مفردات بسيطة، جمل واضحة.                                                      ║
║  • ابدأ بمثال ملموس من الحياة اليومية.                                            ║
║  • عرّف كل كلمة صعبة فور ظهورها.                                                  ║
║  • كرر الأفكار المهمة بطريقة مختلفة إذا لزم الأمر.                                ║
║  • استخدم رموزاً توجيهية (→، •، 1️⃣ 2️⃣ 3️⃣) لتوجيه الطالب.                        ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : currentLang === 'en' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    🎯 BEGINNER LEVEL ADAPTATION 🎯                                ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  • Simple vocabulary, clear sentences.                                           ║
║  • Start with a concrete example from everyday life.                             ║
║  • Define every difficult word as soon as it appears.                            ║
║  • Repeat important ideas in a different way if needed.                          ║
║  • Use guiding symbols (→, •, 1️⃣ 2️⃣ 3️⃣) to structure.                           ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    🎯 ADAPTACIÓN NIVEL PRINCIPIANTE 🎯                            ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  • Vocabulario simple, frases claras.                                            ║
║  • Empieza con un ejemplo concreto de la vida cotidiana.                         ║
║  • Define cada palabra difícil en cuanto aparezca.                               ║
║  • Repite las ideas importantes de otra manera si es necesario.                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
`) : (currentLang === 'fr' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    🎯 ADAPTATION NIVEAU AVANCÉ 🎯                                 ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  • Utilise le vocabulaire technique approprié au niveau.                         ║
║  • Approfondis les concepts avec rigueur scientifique.                           ║
║  • Donne des exemples avancés, des contre-exemples et des cas limites.           ║
║  • Propose des liens avec d'autres notions du programme.                         ║
║  • N'hésite pas à introduire des formules, des schémas ou des démonstrations.    ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : currentLang === 'ar' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    🎯 تكيّف المستوى المتقدم 🎯                                     ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  • استخدم المفردات التقنية المناسبة للمستوى.                                      ║
║  • عمّق المفاهيم بدقة علمية.                                                      ║
║  • أعطِ أمثلة متقدمة وأمثلة مضادة وحالات حدية.                                    ║
║  • اقترح روابط مع مفاهيم أخرى في البرنامج.                                        ║
║  • لا تتردد في تقديم صيغ أو مخططات أو براهين.                                     ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : currentLang === 'en' ? `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    🎯 ADVANCED LEVEL ADAPTATION 🎯                                ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  • Use technical vocabulary appropriate to the level.                            ║
║  • Deepen concepts with scientific rigor.                                        ║
║  • Give advanced examples, counter-examples, and edge cases.                     ║
║  • Suggest links with other concepts in the curriculum.                          ║
║  • Don't hesitate to introduce formulas, diagrams, or proofs.                    ║
╚══════════════════════════════════════════════════════════════════════════════════╝
` : `
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    🎯 ADAPTACIÓN NIVEL AVANZADO 🎯                                ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  • Usa vocabulario técnico apropiado al nivel.                                   ║
║  • Profundiza los conceptos con rigor científico.                                ║
║  • Da ejemplos avanzados, contraejemplos y casos límite.                         ║
║  • Propón vínculos con otros conceptos del programa.                             ║
╚══════════════════════════════════════════════════════════════════════════════════╝
`);

		// Combinaison : règles de langue + règles de listes (si arabe) + qualité + niveau
		return strictLanguageRule + listsRule + richResponseRules + levelRules;
	};

	const generateSupportSystemPrompt = async (supportId) => {
		try {
			console.log(`Fetching support details for ID: ${supportId}`);
			const token = localStorage.getItem('token');
			if (!token) {
				console.error('No token found');
				return null;
			}

			const supportDetails = await getSupportById(token, supportId);
			if (!supportDetails) {
				console.error('Failed to fetch support details');
				return null;
			}

			const currentLang = get(selectedLanguage);
			const targetLangName = currentLang === 'fr' ? 'Français' :
								  currentLang === 'en' ? 'English' :
								  currentLang === 'es' ? 'Español' : 'العربية';

			const isBeginner = !supportDetails?.level ||
							   supportDetails?.level === 'primary' ||
							   supportDetails?.level === 'tronc_commun';

			let prompt = `Tu es un professeur patient et pédagogue.

🌍 LANGUE OBLIGATOIRE: Tu dois répondre UNIQUEMENT en ${targetLangName}.

${getPedagogicalInstruction(currentLang, isBeginner)}

📚 INFORMATIONS DU COURS:
`;
			if (supportDetails.subject) prompt += `Sujet: ${supportDetails.subject}\n`;
			if (supportDetails.title) prompt += `Titre: ${supportDetails.title}\n`;
			if (supportDetails.learning_objective) prompt += `Objectif: ${supportDetails.learning_objective}\n`;
			if (supportDetails.level) prompt += `Niveau: ${supportDetails.level}\n`;

			prompt += `
🎯 MISSION: Aide l'élève à comprendre, pas à mémoriser.
📌 RAPPEL: Adapte la longueur de ta réponse à la complexité de la question.
⚠️ RAPPEL IMPORTANT: Ne mélange JAMAIS les langues. Une seule langue par réponse.
`;

			console.log('System prompt generated');
			return prompt;
		} catch (error) {
			console.error('Error:', error);
			return null;
		}
	};

	const initNewChat = async () => {
		if ($page.url.searchParams.get('models')) {
			selectedModels = $page.url.searchParams.get('models')?.split(',');
		} else if ($page.url.searchParams.get('model')) {
			const urlModels = $page.url.searchParams.get('model')?.split(',');
			if (urlModels.length === 1) {
				const m = $models.find((m) => m.id === urlModels[0]);
				if (!m) {
					const modelSelectorButton = document.getElementById('model-selector-0-button');
					if (modelSelectorButton) {
						modelSelectorButton.click();
						await tick();
						const modelSelectorInput = document.getElementById('model-search-input');
						if (modelSelectorInput) {
							modelSelectorInput.focus();
							modelSelectorInput.value = urlModels[0];
							modelSelectorInput.dispatchEvent(new Event('input'));
						}
					}
				} else {
					selectedModels = urlModels;
				}
			} else {
				selectedModels = urlModels;
			}
		} else {
			if (sessionStorage.selectedModels) {
				selectedModels = JSON.parse(sessionStorage.selectedModels);
				sessionStorage.removeItem('selectedModels');
			} else {
				if ($settings?.models) {
					selectedModels = $settings?.models;
				} else if ($config?.default_models) {
					selectedModels = $config?.default_models.split(',');
				}
			}
		}

		selectedModels = selectedModels.filter((modelId) => $models.map((m) => m.id).includes(modelId));
		if (selectedModels.length === 0 || (selectedModels.length === 1 && selectedModels[0] === '')) {
			if ($models.length > 0) {
				selectedModels = [$models[0].id];
			} else {
				selectedModels = [''];
			}
		}

		await showControls.set(false);
		await showCallOverlay.set(false);
		await showOverview.set(false);
		await showArtifacts.set(false);

		if ($page.url.pathname.includes('/c/')) {
			window.history.replaceState(history.state, '', `/student/c/`);
		}

		autoScroll = true;
		await chatId.set('');
		await chatTitle.set('');
		history = {
			messages: {},
			currentId: null
		};
		chatFiles = [];
		params = {};

		if ($page.url.searchParams.get('youtube')) {
			uploadYoutubeTranscription(`https://www.youtube.com/watch?v=${$page.url.searchParams.get('youtube')}`);
		}
		if ($page.url.searchParams.get('web-search') === 'true') {
			webSearchEnabled = true;
		}
		if ($page.url.searchParams.get('image-generation') === 'true') {
			imageGenerationEnabled = true;
		}
		if ($page.url.searchParams.get('tools')) {
			selectedToolIds = $page.url.searchParams.get('tools')?.split(',').map((id) => id.trim()).filter((id) => id);
		} else if ($page.url.searchParams.get('tool-ids')) {
			selectedToolIds = $page.url.searchParams.get('tool-ids')?.split(',').map((id) => id.trim()).filter((id) => id);
		}
		if ($page.url.searchParams.get('call') === 'true') {
			showCallOverlay.set(true);
			showControls.set(true);
		}
		if ($page.url.searchParams.get('q')) {
			prompt = $page.url.searchParams.get('q') ?? '';
			if (prompt) {
				await tick();
				submitPrompt(prompt);
			}
		}

		selectedModels = selectedModels.map((modelId) =>
			$models.map((m) => m.id).includes(modelId) ? modelId : ''
		);

		const currentAvatarEnabled = ($settings as any)?.avatarEnabled;
		const userSettings = await getUserSettings(localStorage.token);
		if (userSettings) {
			const mergedSettings = { ...userSettings.ui };
			(mergedSettings as any).avatarEnabled = currentAvatarEnabled;
			await settings.set(mergedSettings);
		} else {
			const storedSettings = JSON.parse(localStorage.getItem('settings') ?? '{}');
			storedSettings.avatarEnabled = currentAvatarEnabled;
			await settings.set(storedSettings);
		}

		const chatInput = document.getElementById('chat-input');
		setTimeout(() => chatInput?.focus(), 0);

		const pendingSupportData = localStorage.getItem('pendingSupportData');
		if (pendingSupportData) {
			try {
				const supportData = JSON.parse(pendingSupportData);
				if (supportData && supportData.id) {
					console.log('Found pending support data:', supportData);
					const systemPrompt = await generateSupportSystemPrompt(supportData.id);
					if (systemPrompt) {
						const systemMessageId = uuidv4();
						history.messages[systemMessageId] = {
							id: systemMessageId,
							role: 'system',
							content: systemPrompt,
							done: true,
							timestamp: Date.now()
						};
						console.log('Added pedagogical system prompt');
					}
					try {
						const token = localStorage.getItem('token');
						const supportDetails = await getSupportById(token, supportData.id);
						if (supportDetails && supportDetails.files && supportDetails.files.length > 0) {
							for (const file of supportDetails.files) {
								chatFiles.push({
									id: file.id,
									name: file.filename,
									type: file.file_type || 'application/octet-stream',
									size: file.file_size || 0,
									url: `${TUTOR_BASE_URL}/files/${file.id}`,
									from_support: true
								});
							}
						}
					} catch (fileError) {
						console.error('Error fetching support files:', fileError);
					}
				}
			} catch (error) {
				console.error('Error processing pendingSupportData:', error);
			}
		}
	};

	const loadChat = async () => {
		chatId.set(chatIdProp);
		chat = await getChatById(localStorage.token, $chatId).catch(async (error) => {
			await goto('/');
			return null;
		});
		if (chat) {
			tags = await getTagsById(localStorage.token, $chatId).catch(async (error) => {
				return [];
			});
			const chatContent = chat.chat;
			if (chatContent) {
				console.log(chatContent);
				selectedModels = (chatContent?.models ?? undefined) !== undefined ? chatContent.models : [chatContent.models ?? ''];
				history = (chatContent?.history ?? undefined) !== undefined ? chatContent.history : convertMessagesToHistory(chatContent.messages);
				chatTitle.set(chatContent.title);
				const userSettings = await getUserSettings(localStorage.token);
				if (userSettings) {
					await settings.set(userSettings.ui);
				} else {
					await settings.set(JSON.parse(localStorage.getItem('settings') ?? '{}'));
				}
				params = chatContent?.params ?? {};
				chatFiles = chatContent?.files ?? [];
				autoScroll = true;
				await tick();
				if (history.currentId) {
					history.messages[history.currentId].done = true;
				}
				await tick();
				return true;
			} else {
				return null;
			}
		}
	};

	const scrollToBottom = async () => {
		await tick();
		if (messagesContainerElement) {
			messagesContainerElement.scrollTop = messagesContainerElement.scrollHeight;
		}
	};

	const chatCompletedHandler = async (chatId, modelId, responseMessageId, messages) => {
		const res = await chatCompleted(localStorage.token, {
			model: modelId,
			messages: messages.map((m) => ({
				id: m.id,
				role: m.role,
				content: m.content,
				info: m.info ? m.info : undefined,
				timestamp: m.timestamp,
				...(m.usage ? { usage: m.usage } : {}),
				...(m.sources ? { sources: m.sources } : {})
			})),
			model_item: $models.find((m) => m.id === modelId),
			chat_id: chatId,
			session_id: $socket?.id,
			id: responseMessageId
		}).catch((error) => {
			toast.error(`${error}`);
			messages.at(-1).error = { content: error };
			return null;
		});
		if (res !== null && res.messages) {
			for (const message of res.messages) {
				if (message?.id) {
					history.messages[message.id] = {
						...history.messages[message.id],
						...(history.messages[message.id].content !== message.content ? { originalContent: history.messages[message.id].content } : {}),
						...message
					};
				}
			}
		}
		await tick();
		if ($chatId == chatId) {
			if (!$temporaryChatEnabled) {
				chat = await updateChatById(localStorage.token, chatId, {
					models: selectedModels,
					messages: messages,
					history: history,
					params: params,
					files: chatFiles
				});
				currentChatPage.set(1);
				await chats.set(await getChatList(localStorage.token, $currentChatPage));
			}
		}
	};

	const chatActionHandler = async (chatId, actionId, modelId, responseMessageId, event = null) => {
		const messages = createMessagesList(history, responseMessageId);
		const res = await chatAction(localStorage.token, actionId, {
			model: modelId,
			messages: messages.map((m) => ({
				id: m.id,
				role: m.role,
				content: m.content,
				info: m.info ? m.info : undefined,
				timestamp: m.timestamp,
				...(m.sources ? { sources: m.sources } : {})
			})),
			...(event ? { event: event } : {}),
			model_item: $models.find((m) => m.id === modelId),
			chat_id: chatId,
			session_id: $socket?.id,
			id: responseMessageId
		}).catch((error) => {
			toast.error(`${error}`);
			messages.at(-1).error = { content: error };
			return null;
		});
		if (res !== null && res.messages) {
			for (const message of res.messages) {
				history.messages[message.id] = {
					...history.messages[message.id],
					...(history.messages[message.id].content !== message.content ? { originalContent: history.messages[message.id].content } : {}),
					...message
				};
			}
		}
		if ($chatId == chatId) {
			if (!$temporaryChatEnabled) {
				chat = await updateChatById(localStorage.token, chatId, {
					models: selectedModels,
					messages: messages,
					history: history,
					params: params,
					files: chatFiles
				});
				currentChatPage.set(1);
				await chats.set(await getChatList(localStorage.token, $currentChatPage));
			}
		}
	};

	const getChatEventEmitter = async (modelId: string, chatId: string = '') => {
		return setInterval(() => {
			$socket?.emit('usage', {
				action: 'chat',
				model: modelId,
				chat_id: chatId
			});
		}, 1000);
	};

	const createMessagePair = async (userPrompt) => {
		prompt = '';
		if (selectedModels.length === 0) {
			toast.error($i18n.t('Model not selected'));
		} else {
			const modelId = selectedModels[0];
			const model = $models.filter((m) => m.id === modelId).at(0);
			const messages = createMessagesList(history, history.currentId);
			const parentMessage = messages.length !== 0 ? messages.at(-1) : null;
			const userMessageId = uuidv4();
			const responseMessageId = uuidv4();
			const userMessage = {
				id: userMessageId,
				parentId: parentMessage ? parentMessage.id : null,
				childrenIds: [responseMessageId],
				role: 'user',
				content: userPrompt ? userPrompt : `[PROMPT] ${userMessageId}`,
				timestamp: Math.floor(Date.now() / 1000)
			};
			const responseMessage = {
				id: responseMessageId,
				parentId: userMessageId,
				childrenIds: [],
				role: 'assistant',
				content: `[RESPONSE] ${responseMessageId}`,
				done: true,
				model: modelId,
				modelName: model.name ?? model.id,
				modelIdx: 0,
				timestamp: Math.floor(Date.now() / 1000)
			};
			if (parentMessage) {
				parentMessage.childrenIds.push(userMessageId);
				history.messages[parentMessage.id] = parentMessage;
			}
			history.messages[userMessageId] = userMessage;
			history.messages[responseMessageId] = responseMessage;
			history.currentId = responseMessageId;
			await tick();
			if (autoScroll) {
				scrollToBottom();
			}
			if (messages.length === 0) {
				await initChatHandler(history);
			} else {
				await saveChatHandler($chatId, history);
			}
		}
	};

	const addMessages = async ({ modelId, parentId, messages }) => {
		const model = $models.filter((m) => m.id === modelId).at(0);
		let parentMessage = history.messages[parentId];
		let currentParentId = parentMessage ? parentMessage.id : null;
		for (const message of messages) {
			let messageId = uuidv4();
			if (message.role === 'user') {
				const userMessage = {
					id: messageId,
					parentId: currentParentId,
					childrenIds: [],
					timestamp: Math.floor(Date.now() / 1000),
					...message
				};
				if (parentMessage) {
					parentMessage.childrenIds.push(messageId);
					history.messages[parentMessage.id] = parentMessage;
				}
				history.messages[messageId] = userMessage;
				parentMessage = userMessage;
				currentParentId = messageId;
			} else {
				const responseMessage = {
					id: messageId,
					parentId: currentParentId,
					childrenIds: [],
					done: true,
					model: model.id,
					modelName: model.name ?? model.id,
					modelIdx: 0,
					timestamp: Math.floor(Date.now() / 1000),
					...message
				};
				if (parentMessage) {
					parentMessage.childrenIds.push(messageId);
					history.messages[parentMessage.id] = parentMessage;
				}
				history.messages[messageId] = responseMessage;
				parentMessage = responseMessage;
				currentParentId = messageId;
			}
		}
		history.currentId = currentParentId;
		await tick();
		if (autoScroll) {
			scrollToBottom();
		}
		if (messages.length === 0) {
			await initChatHandler(history);
		} else {
			await saveChatHandler($chatId, history);
		}
	};

	const chatCompletionEventHandler = async (data, message, chatId) => {
		const { id, done, choices, content, sources, selected_model_id, error, usage } = data;
		if (error) {
			await handleOpenAIError(error, message);
		}
		if (sources) {
			message.sources = sources;
		}
		if (choices) {
			if (choices[0]?.message?.content) {
				message.content += choices[0]?.message?.content;
			} else {
				let value = choices[0]?.delta?.content ?? '';
				if (message.content == '' && value == '\n') {
					console.log('Empty response');
				} else {
					message.content += value;
					if (navigator.vibrate && ($settings?.hapticFeedback ?? false)) {
						navigator.vibrate(5);
					}
					const messageContentParts = getMessageContentParts(
						message.content,
						$config?.audio?.tts?.split_on ?? 'punctuation'
					);
					messageContentParts.pop();
					if (
						messageContentParts.length > 0 &&
						messageContentParts[messageContentParts.length - 1] !== message.lastSentence
					) {
						message.lastSentence = messageContentParts[messageContentParts.length - 1];
						eventTarget.dispatchEvent(
							new CustomEvent('chat', {
								detail: {
									id: message.id,
									content: messageContentParts[messageContentParts.length - 1]
								}
							})
						);
					}
				}
			}
		}
		if (content) {
			message.content = content;
			if (navigator.vibrate && ($settings?.hapticFeedback ?? false)) {
				navigator.vibrate(5);
			}
			const messageContentParts = getMessageContentParts(
				message.content,
				$config?.audio?.tts?.split_on ?? 'punctuation'
			);
			messageContentParts.pop();
			if (
				messageContentParts.length > 0 &&
				messageContentParts[messageContentParts.length - 1] !== message.lastSentence
			) {
				message.lastSentence = messageContentParts[messageContentParts.length - 1];
				eventTarget.dispatchEvent(
					new CustomEvent('chat', {
						detail: {
							id: message.id,
							content: messageContentParts[messageContentParts.length - 1]
						}
					})
				);
			}
		}
		if (selected_model_id) {
			message.selectedModelId = selected_model_id;
			message.arena = true;
		}
		if (usage) {
			message.usage = usage;
		}
		history.messages[message.id] = message;
		if (done) {
			message.done = true;
			if ($settings.responseAutoCopy) {
				copyToClipboard(message.content);
			}
			if ($settings.responseAutoPlayback && !$showCallOverlay) {
				await tick();
				document.getElementById(`speak-button-${message.id}`)?.click();
			}
			let lastMessageContentPart =
				getMessageContentParts(message.content, $config?.audio?.tts?.split_on ?? 'punctuation')?.at(-1) ?? '';
			if (lastMessageContentPart) {
				eventTarget.dispatchEvent(
					new CustomEvent('chat', {
						detail: { id: message.id, content: lastMessageContentPart }
					})
				);
			}
			eventTarget.dispatchEvent(
				new CustomEvent('chat:finish', {
					detail: {
						id: message.id,
						content: message.content
					}
				})
			);
			history.messages[message.id] = message;
			await chatCompletedHandler(
				chatId,
				message.model,
				message.id,
				createMessagesList(history, message.id)
			);
		}
		console.log(data);
		if (autoScroll) {
			scrollToBottom();
		}
		if (message.content && avatarActive) {
			currentAvatarMessage = message.content;
			avatarSpeaking = true;
		}
	};

	const submitPrompt = async (userPrompt, { _raw = false } = {}) => {
		console.log('submitPrompt', userPrompt, $chatId);
		const messages = createMessagesList(history, history.currentId);
		const _selectedModels = selectedModels.map((modelId) =>
			$models.map((m) => m.id).includes(modelId) ? modelId : ''
		);
		if (JSON.stringify(selectedModels) !== JSON.stringify(_selectedModels)) {
			selectedModels = _selectedModels;
		}
		if (userPrompt === '' && files.length === 0) {
			toast.error($i18n.t('Please enter a prompt'));
			return;
		}
		if (selectedModels.includes('')) {
			toast.error($i18n.t('Model not selected'));
			return;
		}
		if (messages.length != 0 && messages.at(-1).done != true) {
			return;
		}
		if (messages.length != 0 && messages.at(-1).error && !messages.at(-1).content) {
			toast.error($i18n.t(`Oops! There was an error in the previous response.`));
			return;
		}
		if (
			files.length > 0 &&
			files.filter((file) => file.type !== 'image' && file.status === 'uploading').length > 0
		) {
			toast.error($i18n.t(`Oops! There are files still uploading. Please wait for the upload to complete.`));
			return;
		}
		if (
			($config?.file?.max_count ?? null) !== null &&
			files.length + chatFiles.length > $config?.file?.max_count
		) {
			toast.error(
				$i18n.t(`You can only chat with a maximum of {{maxCount}} file(s) at a time.`, {
					maxCount: $config?.file?.max_count
				})
			);
			return;
		}
		prompt = '';
		const chatInputElement = document.getElementById('chat-input');
		if (chatInputElement) {
			await tick();
			chatInputElement.style.height = '';
			chatInputElement.style.height = Math.min(chatInputElement.scrollHeight, 320) + 'px';
		}
		const _files = JSON.parse(JSON.stringify(files));
		chatFiles.push(..._files.filter((item) => ['doc', 'file', 'collection'].includes(item.type)));
		chatFiles = chatFiles.filter(
			(item, index, array) =>
				array.findIndex((i) => JSON.stringify(i) === JSON.stringify(item)) === index
		);
		files = [];
		prompt = '';
		let userMessageId = uuidv4();
		let userMessage = {
			id: userMessageId,
			parentId: messages.length !== 0 ? messages.at(-1).id : null,
			childrenIds: [],
			role: 'user',
			content: userPrompt,
			files: _files.length > 0 ? _files : undefined,
			timestamp: Math.floor(Date.now() / 1000),
			models: selectedModels
		};
		history.messages[userMessageId] = userMessage;
		history.currentId = userMessageId;
		if (messages.length !== 0) {
			history.messages[messages.at(-1).id].childrenIds.push(userMessageId);
		}
		const chatInput = document.getElementById('chat-input');
		chatInput?.focus();
		saveSessionSelectedModels();
		await sendPrompt(history, userPrompt, userMessageId, { newChat: true });
	};

	const sendPrompt = async (
		_history,
		prompt: string,
		parentId: string,
		{ modelId = null, modelIdx = null, newChat = false } = {}
	) => {
		let _chatId = JSON.parse(JSON.stringify($chatId));
		_history = JSON.parse(JSON.stringify(_history));
		const responseMessageIds: Record<PropertyKey, string> = {};
		let selectedModelIds = modelId ? [modelId] : atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;
		for (const [_modelIdx, modelId] of selectedModelIds.entries()) {
			const model = $models.filter((m) => m.id === modelId).at(0);
			if (model) {
				let responseMessageId = uuidv4();
				let responseMessage = {
					parentId: parentId,
					id: responseMessageId,
					childrenIds: [],
					role: 'assistant',
					content: '',
					model: model.id,
					modelName: model.name ?? model.id,
					modelIdx: modelIdx ? modelIdx : _modelIdx,
					userContext: null,
					timestamp: Math.floor(Date.now() / 1000)
				};
				history.messages[responseMessageId] = responseMessage;
				history.currentId = responseMessageId;
				if (parentId !== null && history.messages[parentId]) {
					history.messages[parentId].childrenIds = [
						...history.messages[parentId].childrenIds,
						responseMessageId
					];
				}
				responseMessageIds[`${modelId}-${modelIdx ? modelIdx : _modelIdx}`] = responseMessageId;
			}
		}
		history = history;
		if (newChat && _history.messages[_history.currentId].parentId === null) {
			_chatId = await initChatHandler(_history);
		}
		await tick();
		_history = JSON.parse(JSON.stringify(history));
		await saveChatHandler(_chatId, _history);
		await Promise.all(
			selectedModelIds.map(async (modelId, _modelIdx) => {
				console.log('modelId', modelId);
				const model = $models.filter((m) => m.id === modelId).at(0);
				if (model) {
					const messages = createMessagesList(_history, parentId);
					const hasImages = messages.some((message) =>
						message.files?.some((file) => file.type === 'image')
					);
					if (hasImages && !(model.info?.meta?.capabilities?.vision ?? true)) {
						toast.error(
							$i18n.t('Model {{modelName}} is not vision capable', {
								modelName: model.name ?? model.id
							})
						);
					}
					let responseMessageId = responseMessageIds[`${modelId}-${modelIdx ? modelIdx : _modelIdx}`];
					let responseMessage = _history.messages[responseMessageId];
					let userContext = null;
					if ($settings?.memory ?? false) {
						if (userContext === null) {
							const res = await queryMemory(localStorage.token, prompt).catch((error) => {
								toast.error(`${error}`);
								return null;
							});
							if (res) {
								if (res.documents[0].length > 0) {
									userContext = res.documents[0].reduce((acc, doc, index) => {
										const createdAtTimestamp = res.metadatas[0][index].created_at;
										const createdAtDate = new Date(createdAtTimestamp * 1000)
											.toISOString()
											.split('T')[0];
										return `${acc}${index + 1}. [${createdAtDate}]. ${doc}\n`;
									}, '');
								}
								console.log(userContext);
							}
						}
					}
					responseMessage.userContext = userContext;
					const chatEventEmitter = await getChatEventEmitter(model.id, _chatId);
					scrollToBottom();
					await sendPromptSocket(_history, model, responseMessageId, _chatId);
					if (chatEventEmitter) clearInterval(chatEventEmitter);
				} else {
					toast.error($i18n.t(`Model {{modelId}} not found`, { modelId }));
				}
			})
		);
		currentChatPage.set(1);
		chats.set(await getChatList(localStorage.token, $currentChatPage));
	};

	const sendPromptSocket = async (_history, model, responseMessageId, _chatId) => {
		const responseMessage = _history.messages[responseMessageId];
		const userMessage = _history.messages[responseMessage.parentId];
		let files = JSON.parse(JSON.stringify(chatFiles));
		files.push(
			...(userMessage?.files ?? []).filter((item) => ['doc', 'file', 'collection'].includes(item.type)),
			...(responseMessage?.files ?? []).filter((item) => ['web_search_results'].includes(item.type))
		);
		files = files.filter(
			(item, index, array) =>
				array.findIndex((i) => JSON.stringify(i) === JSON.stringify(item)) === index
		);
		scrollToBottom();
		eventTarget.dispatchEvent(
			new CustomEvent('chat:start', {
				detail: {
					id: responseMessageId
				}
			})
		);
		await tick();

		const stream =
			model?.info?.params?.stream_response ??
			$settings?.params?.stream_response ??
			params?.stream_response ??
			true;
		let avatarPersonality = '';
		if (avatarActive && ($settings as any)?.selectedAvatarId) {
			const selectedAvatarId = ($settings as any).selectedAvatarId;
			const avatarPersonalities = {
				'The Scholar': 'You are The Scholar: analytical, detail-oriented, methodical, and patient.',
				'The Mentor': 'You are The Mentor: encouraging, warm, supportive, and insightful.',
				'The Coach': 'You are The Coach: energetic, motivational, direct, and goal-oriented.',
				'The Innovator': 'You are The Innovator: creative, adaptable, curious, and thought-provoking.'
			};
			avatarPersonality = avatarPersonalities[selectedAvatarId] || '';
		}
		let systemMessages = [];
		let conversationMessages = [];
		for (const messageId in _history.messages) {
			const message = _history.messages[messageId];
			if (message.role === 'system') {
				systemMessages.push(message);
			} else {
				conversationMessages.push(message);
			}
		}
		if (systemMessages.length > 0) {
			systemMessages.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
		}
		let combinedSystemPrompt = '';
		if (systemMessages.length > 0) {
			combinedSystemPrompt = systemMessages.map(msg => msg.content).join('\n\n');
		}
		const currentLang = get(selectedLanguage);
		let isBeginner = true;
		try {
			const pendingSupportData = localStorage.getItem('pendingSupportData');
			if (pendingSupportData) {
				const supportData = JSON.parse(pendingSupportData);
				if (supportData && supportData.id) {
					const supportDetails = await getSupportById(localStorage.token, supportData.id);
					isBeginner = !supportDetails?.level || supportDetails?.level === 'tronc_commun';
				}
			}
		} catch(e) {
			console.error('Error checking beginner level:', e);
		}

		// ============ INSTRUCTION PÉDAGOGIQUE CALIBRÉE (longueur adaptée) ============
		const languageInstruction = getPedagogicalInstruction(currentLang, isBeginner);

		const baseSystemContent = (avatarActive && avatarPersonality
			? `${avatarPersonality}\n\n${params?.system || $settings.system ? `Additional instructions: ${promptTemplate(params?.system ?? $settings?.system ?? '', $user.name, $settings?.userLocation ? await getAndUpdateUserLocation(localStorage.token).catch((err) => { console.error(err); return undefined; }) : undefined)}` : ''}${(responseMessage?.userContext ?? null) ? `\n\nUser Context:\n${responseMessage?.userContext ?? ''}` : ''}`
			: `${promptTemplate(params?.system ?? $settings?.system ?? '', $user.name, $settings?.userLocation ? await getAndUpdateUserLocation(localStorage.token).catch((err) => { console.error(err); return undefined; }) : undefined)}${(responseMessage?.userContext ?? null) ? `\n\nUser Context:\n${responseMessage?.userContext ?? ''}` : ''}`);

		let messages = [
			{
				role: 'system',
				content: (combinedSystemPrompt || baseSystemContent) + languageInstruction
			},
			...createMessagesList(_history, responseMessageId)
				.filter(message => message.role !== 'system')
				.map((message) => ({
					...message,
					content: removeDetails(message.content, ['reasoning', 'code_interpreter'])
				}))
		].filter((message) => message && message.content && message.content.trim() !== '');
		messages = messages
			.map((message, idx, arr) => ({
				role: message.role,
				...((message.files?.filter((file) => file.type === 'image').length > 0 ?? false) && message.role === 'user' ? {
					content: [
						{
							type: 'text',
							text: message?.merged?.content ?? message.content
						},
						...message.files
							.filter((file) => file.type === 'image')
							.map((file) => ({
								type: 'image_url',
								image_url: {
									url: file.url
								}
							}))
					]
				} : {
					content: message?.merged?.content ?? message.content
				})
			}))
			.filter((message) => message?.role === 'user' || message?.content?.trim());
		const res = await generateOpenAIChatCompletion(
			localStorage.token,
			{
				stream: stream,
				model: model.id,
				messages: messages,
				params: {
					...$settings?.params,
					...params,
					format: $settings.requestFormat ?? undefined,
					keep_alive: $settings.keepAlive ?? undefined,
					stop: (params?.stop ?? $settings?.params?.stop ?? undefined) ? (params?.stop.split(',').map((token) => token.trim()) ?? $settings.params.stop).map((str) => decodeURIComponent(JSON.parse('"' + str.replace(/\"/g, '\\"') + '"'))) : undefined
				},
				files: (files?.length ?? 0) > 0 ? files : undefined,
				tool_ids: selectedToolIds.length > 0 ? selectedToolIds : undefined,
				...(avatarActive && ($settings as any)?.selectedAvatarId ? { avatar_type: ($settings as any).selectedAvatarId.toLowerCase().replace(/^the\s+/i, '') } : {}),
				features: {
					image_generation: $config?.features?.enable_image_generation && ($user.role === 'admin' || $user?.permissions?.features?.image_generation) ? imageGenerationEnabled : false,
					code_interpreter: $config?.features?.enable_code_interpreter && ($user.role === 'admin' || $user?.permissions?.features?.code_interpreter) ? codeInterpreterEnabled : false,
					web_search: $config?.features?.enable_web_search && ($user.role === 'admin' || $user?.permissions?.features?.web_search) ? webSearchEnabled || ($settings?.webSearch ?? false) === 'always' : false
				},
				variables: {
					...getPromptVariables($user.name, $settings?.userLocation ? await getAndUpdateUserLocation(localStorage.token).catch((err) => { console.error(err); return undefined; }) : undefined)
				},
				model_item: $models.find((m) => m.id === model.id),
				session_id: $socket?.id,
				chat_id: $chatId,
				id: responseMessageId,
				...(!$temporaryChatEnabled && (messages.length == 1 || (messages.length == 2 && messages.at(0)?.role === 'system' && messages.at(1)?.role === 'user')) && (selectedModels[0] === model.id || atSelectedModel !== undefined) ? { background_tasks: { title_generation: $settings?.title?.auto ?? true, tags_generation: $settings?.autoTags ?? true } } : {}),
				...(stream && (model.info?.meta?.capabilities?.usage ?? false) ? { stream_options: { include_usage: true } } : {})
			},
			`${TUTOR_BASE_URL}/api`
		).catch((error) => {
			toast.error(`${error}`);
			responseMessage.error = { content: error };
			responseMessage.done = true;
			history.messages[responseMessageId] = responseMessage;
			history.currentId = responseMessageId;
			return null;
		});
		console.log(res);
		if (res) {
			taskId = res.task_id;
		}
		await tick();
		scrollToBottom();
	};

	const handleOpenAIError = async (error, responseMessage) => {
		let errorMessage = '';
		let innerError;
		if (error) {
			innerError = error;
		}
		console.error(innerError);
		if ('detail' in innerError) {
			toast.error(innerError.detail);
			errorMessage = innerError.detail;
		} else if ('error' in innerError) {
			if ('message' in innerError.error) {
				toast.error(innerError.error.message);
				errorMessage = innerError.error.message;
			} else {
				toast.error(innerError.error);
				errorMessage = innerError.error;
			}
		} else if ('message' in innerError) {
			toast.error(innerError.message);
			errorMessage = innerError.message;
		}
		responseMessage.error = {
			content: $i18n.t(`Uh-oh! There was an issue with the response.`) + '\n' + errorMessage
		};
		responseMessage.done = true;
		if (responseMessage.statusHistory) {
			responseMessage.statusHistory = responseMessage.statusHistory.filter(
				(status) => status.action !== 'knowledge_search'
			);
		}
		history.messages[responseMessage.id] = responseMessage;
	};

	const stopResponse = () => {
		if (taskId) {
			const res = stopTask(localStorage.token, taskId).catch((error) => { return null; });
			if (res) {
				taskId = null;
				const responseMessage = history.messages[history.currentId];
				responseMessage.done = true;
				history.messages[history.currentId] = responseMessage;
				if (autoScroll) {
					scrollToBottom();
				}
			}
		}
	};

	const submitMessage = async (parentId, prompt) => {
		let userPrompt = prompt;
		let userMessageId = uuidv4();
		let userMessage = {
			id: userMessageId,
			parentId: parentId,
			childrenIds: [],
			role: 'user',
			content: userPrompt,
			models: selectedModels
		};
		if (parentId !== null) {
			history.messages[parentId].childrenIds = [...history.messages[parentId].childrenIds, userMessageId];
		}
		history.messages[userMessageId] = userMessage;
		history.currentId = userMessageId;
		await tick();
		await sendPrompt(history, userPrompt, userMessageId);
	};

	const regenerateResponse = async (message) => {
		console.log('regenerateResponse');
		if (history.currentId) {
			let userMessage = history.messages[message.parentId];
			let userPrompt = userMessage.content;
			if ((userMessage?.models ?? [...selectedModels]).length == 1) {
				await sendPrompt(history, userPrompt, userMessage.id);
			} else {
				await sendPrompt(history, userPrompt, userMessage.id, { modelId: message.model, modelIdx: message.modelIdx });
			}
		}
	};

	const continueResponse = async () => {
		console.log('continueResponse');
		const _chatId = JSON.parse(JSON.stringify($chatId));
		if (history.currentId && history.messages[history.currentId].done == true) {
			const responseMessage = history.messages[history.currentId];
			responseMessage.done = false;
			await tick();
			const model = $models.filter((m) => m.id === (responseMessage?.selectedModelId ?? responseMessage.model)).at(0);
			if (model) {
				await sendPromptSocket(history, model, responseMessage.id, _chatId);
			}
		}
	};

	const mergeResponses = async (messageId, responses, _chatId) => {
		console.log('mergeResponses', messageId, responses);
		const message = history.messages[messageId];
		const mergedResponse = { status: true, content: '' };
		message.merged = mergedResponse;
		history.messages[messageId] = message;
		try {
			const [res, controller] = await generateMoACompletion(
				localStorage.token,
				message.model,
				history.messages[message.parentId].content,
				responses
			);
			if (res && res.ok && res.body) {
				const textStream = await createOpenAITextStream(res.body, $settings.splitLargeChunks);
				for await (const update of textStream) {
					const { value, done, sources, error, usage } = update;
					if (error || done) { break; }
					if (mergedResponse.content == '' && value == '\n') { continue; }
					else { mergedResponse.content += value; history.messages[messageId] = message; }
					if (autoScroll) { scrollToBottom(); }
				}
				await saveChatHandler(_chatId, history);
			} else { console.error(res); }
		} catch (e) { console.error(e); }
	};

	const initChatHandler = async (history) => {
		let _chatId = $chatId;
		try {
			if (selectedModels.length === 0 || selectedModels.some(model => !model)) {
				console.error('Invalid model selection. Setting default model...');
				if ($models.length > 0) {
					selectedModels = [$models[0].id];
				} else {
					throw new Error('No models available');
				}
			}
			if (!$temporaryChatEnabled) {
				let supportId = null;
				let supportTitle = null;
				try {
					const pendingSupportData = localStorage.getItem('pendingSupportData');
					if (pendingSupportData) {
						const supportData = JSON.parse(pendingSupportData);
						supportId = supportData?.id || null;
						if (supportId) {
							try {
								const token = localStorage.getItem('token');
								const supportDetails = await getSupportById(token, supportId);
								if (supportDetails && supportDetails.title) {
									supportTitle = supportDetails.title;
									console.log(`Using support title for chat: ${supportTitle}`);
								}
							} catch (titleError) { console.error('Error getting support title:', titleError); }
						}
					}
				} catch (error) { console.error('Error parsing pendingSupportData:', error); }
				chat = await createNewChat(localStorage.token, {
					id: _chatId,
					title: supportTitle || $i18n.t('New Chat'),
					models: selectedModels,
					system: $settings.system ?? undefined,
					params: params,
					history: history,
					messages: createMessagesList(history, history.currentId),
					tags: [],
					files: chatFiles,
					support_id: supportId,
					timestamp: Date.now()
				});
				_chatId = chat.id;
				await chatId.set(_chatId);
				await chats.set(await getChatList(localStorage.token, $currentChatPage));
				currentChatPage.set(1);
				if (supportId) { console.log('Successfully created chat with support ID'); }
				window.history.replaceState(history.state, '', `/student/c/${_chatId}`);
				if (typeof window !== 'undefined' && window.openTutorEvents) {
					console.log('Dispatching chatCreated event with ID:', _chatId);
					window.openTutorEvents.dispatchEvent(
						new CustomEvent('chatCreated', { detail: { chatId: _chatId, timestamp: Date.now(), success: true } })
					);
				}
			} else {
				_chatId = 'local';
				await chatId.set('local');
			}
			await tick();
			return _chatId;
		} catch (error) {
			console.error('Error in initChatHandler:', error);
			if (typeof window !== 'undefined' && window.localStorage) { window.localStorage.removeItem('pendingSupportData'); }
			if (typeof window !== 'undefined' && window.openTutorEvents) {
				window.openTutorEvents.dispatchEvent(
					new CustomEvent('chatCreated', { detail: { chatId: null, timestamp: Date.now(), success: false, error: error?.message || 'Chat initialization failed' } })
				);
			}
			toast.error($i18n.t('Failed to initialize chat'));
			return null;
		}
	};

	const saveChatHandler = async (_chatId, history) => {
		if ($chatId == _chatId) {
			if (!$temporaryChatEnabled) {
				chat = await updateChatById(localStorage.token, _chatId, {
					models: selectedModels,
					history: history,
					messages: createMessagesList(history, history.currentId),
					params: params,
					files: chatFiles
				});
				currentChatPage.set(1);
				await chats.set(await getChatList(localStorage.token, $currentChatPage));
			}
		}
	};
</script>

<svelte:head>
	<title>
		{$chatTitle ? `${$chatTitle.length > 30 ? `${$chatTitle.slice(0, 30)}...` : $chatTitle} | ${$TUTOR_NAME}` : `${$TUTOR_NAME}`}
	</title>
</svelte:head>

<style>
	/* ═══════════════════════════════════════════════════════════════════════
	   CORRECTION RTL — TABLEAUX EN ARABE
	   ═══════════════════════════════════════════════════════════════════════ */

	:global([dir="rtl"] table) {
		direction: rtl !important;
		width: 100%;
		border-collapse: collapse;
	}

	:global([dir="rtl"] .prose table),
	:global([dir="rtl"] .message table),
	:global([dir="rtl"] .markdown table),
	:global([dir="rtl"] .chat-message table) {
		direction: rtl !important;
		width: 100%;
		border-collapse: collapse;
	}

	:global([dir="rtl"] th),
	:global([dir="rtl"] td) {
		text-align: right !important;
		padding: 8px 12px !important;
		border: 1px solid #ccc !important;
		unicode-bidi: embed;
	}

	:global([dir="rtl"] thead tr) {
		background-color: #f5f5f5 !important;
	}

	:global([dir="rtl"] tr) {
		direction: rtl;
	}

	:global(.rtl-content table),
	:global(.rtl-content .prose table),
	:global(.rtl-content .message table),
	:global(.rtl-content .markdown table) {
		direction: rtl !important;
		width: 100%;
		border-collapse: collapse;
	}

	:global(.rtl-content th),
	:global(.rtl-content td) {
		text-align: right !important;
		padding: 8px 12px !important;
		border: 1px solid #ccc !important;
		unicode-bidi: embed;
	}

	:global(.rtl-content thead tr) {
		background-color: #f5f5f5 !important;
	}

	:global(.rtl-content tr) {
		direction: rtl;
	}

	:global(.dark [dir="rtl"] thead tr),
	:global(.dark .rtl-content thead tr) {
		background-color: #2d2d2d !important;
	}

	/* ═══════════════════════════════════════════════════════════════════════
	   CORRECTION LISTES RTL — VERSION CORRECTE (sans suppression des numéros)
	   ═══════════════════════════════════════════════════════════════════════ */

	:global([dir="rtl"] ol),
	:global(.rtl-content ol) {
		direction: rtl;
		padding-right: 1.5rem;
		padding-left: 0;
		/* NE PAS toucher list-style-type : le navigateur 
		   gère déjà l'ordre 1, 2, 3... correctement en RTL */
	}

	:global([dir="rtl"] ol li),
	:global(.rtl-content ol li) {
		text-align: right;
	}

	:global([dir="rtl"] ul),
	:global(.rtl-content ul) {
		direction: rtl;
		padding-right: 1.5rem;
		padding-left: 0;
	}

	:global([dir="rtl"] ul li),
	:global(.rtl-content ul li) {
		text-align: right;
	}
	/* Supprimer complètement les ::before personnalisés */
</style>

<audio id="audioElement" src="" style="display: none;" />

<EventConfirmDialog
	bind:show={showEventConfirmation}
	title={eventConfirmationTitle}
	message={eventConfirmationMessage}
	input={eventConfirmationInput}
	inputPlaceholder={eventConfirmationInputPlaceholder}
	inputValue={eventConfirmationInputValue}
	on:confirm={(e) => {
		if (e.detail) {
			eventCallback(e.detail);
		} else {
			eventCallback(true);
		}
	}}
	on:cancel={() => {
		eventCallback(false);
	}}
/>

<div
	class="h-screen max-h-[100dvh] transition-width duration-200 ease-in-out bg-[#F5F7F9] dark:bg-inherit {$showSidebar ? 'md:max-w-[calc(100%-260px)]' : ''} w-full max-w-full flex flex-col shadow-md"
	id="chat-container"
>
	{#if chatIdProp === '' || (!loading && chatIdProp)}
		{#if $settings?.backgroundImageUrl ?? null}
			<div
				class="absolute {$showSidebar ? 'md:max-w-[calc(100%-260px)] md:translate-x-[260px]' : ''} top-0 left-0 w-full h-full bg-cover bg-center bg-no-repeat"
				style="background-image: url({$settings.backgroundImageUrl})"
			/>
			<div
				class="absolute top-0 left-0 w-full h-full bg-linear-to-t from-white to-white/85 dark:from-gray-900 dark:to-gray-900/90 z-0"
			/>
		{/if}

		<Navbar
			bind:this={navbarElement}
			chat={{
				id: $chatId,
				chat: {
					title: $chatTitle,
					models: selectedModels,
					system: $settings.system ?? undefined,
					params: params,
					history: history,
					timestamp: Date.now()
				}
			}}
			title={$chatTitle}
			bind:selectedModels
			shareEnabled={!!history.currentId}
			{initNewChat}
			{avatarActive}
			{toggleAvatar}
		/>

		<PaneGroup direction="horizontal" class="w-full h-full">
			<Pane defaultSize={50} class="h-full flex w-full relative shadow-md">
				{#if !history.currentId && !$chatId && selectedModels.length <= 1 && ($banners.length > 0 || ($config?.license_metadata?.type ?? null) === 'trial' || (($config?.license_metadata?.seats ?? null) !== null && $config?.user_count > $config?.license_metadata?.seats))}
					<div class="absolute top-12 left-0 right-0 w-full z-30">
						<div class="flex flex-col gap-1 w-full">
							{#if ($config?.license_metadata?.type ?? null) === 'trial'}
								<Banner banner={{ type: 'info', title: 'Trial License', content: $i18n.t('You are currently using a trial license. Please contact support to upgrade your license.') }} />
							{/if}
							{#if ($config?.license_metadata?.seats ?? null) !== null && $config?.user_count > $config?.license_metadata?.seats}
								<Banner banner={{ type: 'error', title: 'License Error', content: $i18n.t('Exceeded the number of seats in your license. Please contact support to increase the number of seats.') }} />
							{/if}
							{#each $banners.filter((b) => (b.dismissible ? !JSON.parse(localStorage.getItem('dismissedBannerIds') ?? '[]').includes(b.id) : true)) as banner}
								<Banner {banner} on:dismiss={(e) => { const bannerId = e.detail; localStorage.setItem('dismissedBannerIds', JSON.stringify([bannerId, ...JSON.parse(localStorage.getItem('dismissedBannerIds') ?? '[]')].filter((id) => $banners.find((b) => b.id === id)))); }} />
							{/each}
						</div>
					</div>
				{/if}

				<div class="flex flex-col flex-auto z-10 w-full @container">
					{#if $settings?.landingPageMode === 'chat' || createMessagesList(history, history.currentId).length > 0}
						{#if avatarActive}
							<div class="flex flex-col w-full h-full flex-auto relative">
								<div class="flex-1 overflow-hidden bg-transparent">
									<AvatarChat
										className="h-full flex"
										{history}
										currentMessage={currentAvatarMessage}
										speaking={avatarSpeaking}
										on:speechend={() => (avatarSpeaking = false)}
									/>
								</div>
								<div class="absolute bottom-0 left-0 right-0 z-20 animate-float">
									<MessageInput
										{history}
										{selectedModels}
										bind:files
										bind:prompt
										bind:autoScroll
										bind:selectedToolIds
										bind:imageGenerationEnabled
										bind:codeInterpreterEnabled
										bind:webSearchEnabled
										bind:atSelectedModel
										transparentBackground={true}
										{stopResponse}
										on:submit={async (e) => {
											if (e.detail || files.length > 0) {
												await tick();
												submitPrompt(($settings?.richTextInput ?? true) ? e.detail.replaceAll('\n\n', '\n') : e.detail);
											}
										}}
									/>
								</div>
							</div>
						{:else}
							<div
								class="flex flex-col w-full h-full flex-auto relative bg-[#F5F7F9] dark:bg-gray-900"
								dir={currentDir}
							>
								<div
									class="pb-2.5 flex-1 flex flex-col w-full overflow-auto max-w-full z-10 scrollbar-hidden {currentDir === 'rtl' ? 'rtl-content' : ''}"
									id="messages-container"
									bind:this={messagesContainerElement}
									on:scroll={(e) => { autoScroll = messagesContainerElement.scrollHeight - messagesContainerElement.scrollTop <= messagesContainerElement.clientHeight + 5; }}
								>
									<div
										class="h-full w-full flex flex-col"
										dir={currentDir}
									>
										<Messages
											chatId={$chatId}
											bind:history
											bind:autoScroll
											bind:prompt
											{selectedModels}
											{atSelectedModel}
											{sendPrompt}
											{showMessage}
											{submitMessage}
											{continueResponse}
											{regenerateResponse}
											{mergeResponses}
											{chatActionHandler}
											{addMessages}
											bottomPadding={files.length > 0}
											dir={currentDir}
										/>
									</div>
								</div>
								<div class="w-full pt-2 relative z-20">
									<MessageInput
										{history}
										{selectedModels}
										bind:files
										bind:prompt
										bind:autoScroll
										bind:selectedToolIds
										bind:imageGenerationEnabled
										bind:codeInterpreterEnabled
										bind:webSearchEnabled
										bind:atSelectedModel
										transparentBackground={$settings?.backgroundImageUrl ?? false}
										{stopResponse}
										on:submit={async (e) => {
											if (e.detail || files.length > 0) {
												await tick();
												submitPrompt(($settings?.richTextInput ?? true) ? e.detail.replaceAll('\n\n', '\n') : e.detail);
											}
										}}
									/>
								</div>
							</div>
						{/if}
					{:else}
						<div class="overflow-auto w-full h-full flex items-center">
							<Placeholder
								{history}
								{selectedModels}
								bind:files
								bind:prompt
								bind:autoScroll
								bind:selectedToolIds
								bind:imageGenerationEnabled
								bind:codeInterpreterEnabled
								bind:webSearchEnabled
								bind:atSelectedModel
								transparentBackground={$settings?.backgroundImageUrl ?? false}
								{stopResponse}
								{createMessagePair}
								on:upload={async (e) => {
									const { type, data } = e.detail;
									if (type === 'web') { await uploadWeb(data); }
									else if (type === 'youtube') { await uploadYoutubeTranscription(data); }
								}}
								on:submit={async (e) => {
									if (e.detail || files.length > 0) {
										await tick();
										submitPrompt(($settings?.richTextInput ?? true) ? e.detail.replaceAll('\n\n', '\n') : e.detail);
									} else {
										await initNewChat();
										setTimeout(() => {
											const initialMessage = 'Hello';
											prompt = initialMessage;
											submitPrompt(initialMessage);
										}, 300);
									}
								}}
							/>
						</div>
					{/if}
				</div>
			</Pane>

			<ChatControls
				bind:this={controlPaneComponent}
				bind:history
				bind:chatFiles
				bind:params
				bind:files
				bind:pane={controlPane}
				chatId={$chatId}
				modelId={selectedModelIds?.at(0) ?? null}
				models={selectedModelIds.reduce((a, e, i, arr) => { const model = $models.find((m) => m.id === e); if (model) { return [...a, model]; } return a; }, [])}
				{submitPrompt}
				{stopResponse}
				{showMessage}
				{eventTarget}
				{avatarActive}
				onAvatarToggle={toggleAvatar}
				class="shadow-lg"
			/>
		</PaneGroup>
	{:else if loading}
		<div class="flex items-center justify-center h-full w-full">
			<div class="m-auto">
				<Spinner />
			</div>
		</div>
	{/if}
</div>