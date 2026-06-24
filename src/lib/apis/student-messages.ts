import { TUTOR_API_BASE_URL } from '$lib/constants';

export const getStudentChannels = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${TUTOR_API_BASE_URL}/channels`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail || err.message;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getStudentChannelMessages = async (token: string = '', channelId: string) => {
	let error = null;

	const res = await fetch(`${TUTOR_API_BASE_URL}/channels/${channelId}/messages`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail || err.message;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const postStudentMessage = async (token: string = '', channelId: string, content: string) => {
	let error = null;

	const res = await fetch(`${TUTOR_API_BASE_URL}/channels/${channelId}/messages`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ content, is_svg: false })
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail || err.message;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
