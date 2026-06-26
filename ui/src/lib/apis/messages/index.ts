import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface Attachment {
	id: string;
	message_id: string | null;
	conversation_id: string | null;
	original_filename: string;
	mime_type: string;
	file_size: number;
	uploaded_at: string;
}

export interface Conversation {
	id: string;
	parent_id: string;
	teacher_id: string;
	student_id: string;
	parent_name: string;
	teacher_name: string;
	student_name: string;
	unread_count: number;
	created_at: string;
	updated_at: string;
}

export interface Message {
	id: string;
	conversation_id: string;
	sender_id: string;
	content: string;
	is_read: boolean;
	attachments: Attachment[];
	created_at: string;
}

export interface UserInfo {
	id: string;
	name: string;
	email: string;
	profile_image_url: string | null;
	role: string;
}

export interface ChildTeacher {
	student: UserInfo;
	teacher: UserInfo;
}

export const getConversations = async (token: string): Promise<Conversation[]> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/messages/conversations`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});
	if (error) throw error;
	return res;
};

export const getMessages = async (
	token: string,
	conversationId: string
): Promise<Message[]> => {
	let error = null;
	const res = await fetch(
		`${TUTOR_API_BASE_URL}/messages/conversations/${conversationId}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				authorization: `Bearer ${token}`
			}
		}
	)
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});
	if (error) throw error;
	return res;
};

export const sendMessage = async (
	token: string,
	receiverId: string,
	studentId: string,
	content: string,
	attachmentIds?: string[]
): Promise<{ message_id: string; status: string; message: Message }> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/messages/send`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			receiver_id: receiverId,
			student_id: studentId,
			content,
			attachment_ids: attachmentIds ?? null
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});
	if (error) throw error;
	return res;
};

export const uploadAttachment = async (
	token: string,
	conversationId: string,
	file: File,
	onProgress?: (pct: number) => void
): Promise<Attachment> => {
	return new Promise((resolve, reject) => {
		const xhr = new XMLHttpRequest();
		const formData = new FormData();
		formData.append('file', file);

		xhr.open('POST', `${TUTOR_API_BASE_URL}/messages/conversations/${conversationId}/attachments`);
		xhr.setRequestHeader('authorization', `Bearer ${token}`);

		if (onProgress) {
			xhr.upload.onprogress = (e) => {
				if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
			};
		}

		xhr.onload = () => {
			if (xhr.status >= 200 && xhr.status < 300) {
				resolve(JSON.parse(xhr.responseText));
			} else {
				try {
					reject(JSON.parse(xhr.responseText)?.detail ?? 'Upload failed');
				} catch {
					reject('Upload failed');
				}
			}
		};
		xhr.onerror = () => reject('Network error during upload');
		xhr.send(formData);
	});
};

export const getAttachmentDownloadUrl = (attachmentId: string): string => {
	return `${TUTOR_API_BASE_URL}/messages/attachments/${attachmentId}/download`;
};

export const getTeachersOfChild = async (
	token: string,
	studentId: string
): Promise<UserInfo[]> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/messages/teachers/${studentId}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});
	if (error) throw error;
	return res;
};

export const getAllChildrenTeachers = async (token: string): Promise<ChildTeacher[]> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/messages/my-children-teachers`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});
	if (error) throw error;
	return res;
};

export const markAsRead = async (token: string, messageId: string): Promise<Message> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/messages/${messageId}/read`, {
		method: 'PATCH',
		headers: {
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});
	if (error) throw error;
	return res;
};
