import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface Conversation {
	id: string;
	other_user_id: string | null;
	other_name: string | null;
	other_email: string | null;
	last_message: string | null;
	last_message_at: string | null;
	unread: number;
}

export interface Message {
	id: string;
	conversation_id: string;
	sender_id: string;
	body: string | null;
	attachment_id?: string | null;
	attachment_name?: string | null;
	created_at: string | null;
}

export interface ConversationThread {
	conversation: Conversation;
	messages: Message[];
}

const jsonHeaders = (token: string) => ({
	Accept: 'application/json',
	'Content-Type': 'application/json',
	authorization: `Bearer ${token}`
});

const _send = async (url: string, method: string, token: string, body?: any) => {
	let error = null;
	const res = await fetch(url, {
		method,
		headers: jsonHeaders(token),
		...(body !== undefined ? { body: JSON.stringify(body) } : {})
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? err;
			return null;
		});
	if (error) throw error;
	return res;
};

export const getConversations = (token: string): Promise<Conversation[]> =>
	_send(`${TUTOR_API_BASE_URL}/conversations`, 'GET', token);

export const startConversation = (token: string, recipientId: string): Promise<Conversation> =>
	_send(`${TUTOR_API_BASE_URL}/conversations`, 'POST', token, { recipient_id: recipientId });

export const getMessages = (token: string, conversationId: string): Promise<ConversationThread> =>
	_send(`${TUTOR_API_BASE_URL}/conversations/${conversationId}/messages`, 'GET', token);

export const sendMessage = (
	token: string,
	conversationId: string,
	body: string,
	attachmentId?: string
): Promise<Message> =>
	_send(`${TUTOR_API_BASE_URL}/conversations/${conversationId}/messages`, 'POST', token, {
		body,
		attachment_id: attachmentId
	});

export const downloadMessageAttachment = async (
	token: string,
	conversationId: string,
	messageId: string
): Promise<Blob> => {
	const res = await fetch(
		`${TUTOR_API_BASE_URL}/conversations/${conversationId}/messages/${messageId}/attachment`,
		{ method: 'GET', headers: { authorization: `Bearer ${token}` } }
	);
	if (!res.ok) throw await res.json().catch(() => 'Download failed');
	return res.blob();
};
