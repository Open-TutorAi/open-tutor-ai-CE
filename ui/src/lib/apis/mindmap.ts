import { TUTOR_API_BASE_URL } from '$lib/constants';

export async function getMindmapContext(token: string, chatId: string) {
	const response = await fetch(`${TUTOR_API_BASE_URL}/mindmap/context/${chatId}`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	});
	if (!response.ok) throw new Error('Failed to get mindmap context');
	return await response.json();
}

export async function verifyMindmap(token: string, chatId: string, nodes: any[], edges: any[]) {
	const response = await fetch(`${TUTOR_API_BASE_URL}/mindmap/verify`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			chat_id: chatId,
			nodes: nodes.map((n) => ({
				id: n.id,
				label: n.label,
				type: n.type,
				color: n.color
			})),
			edges: edges.map((e) => ({
				from_: e.from,
				to: e.to
			}))
		})
	});
	if (!response.ok) throw new Error('Failed to verify mindmap');
	return await response.json();
}
export async function exportMindmapPDF(token: string, title: string, nodes: any[], edges: any[]) {
	const response = await fetch(`${TUTOR_API_BASE_URL}/mindmap/export/pdf`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			title,
			nodes: nodes.map((n) => ({
				id: n.id,
				label: n.label,
				type: n.type,
				color: n.color
			})),
			edges: edges.map((e) => ({
				from_: e.from,
				to: e.to
			}))
		})
	});

	if (!response.ok) throw new Error('Failed to export PDF');

	// Télécharger le PDF
	const blob = await response.blob();
	const url = window.URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = `mindmap-${title}.pdf`;
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
	window.URL.revokeObjectURL(url);
}
