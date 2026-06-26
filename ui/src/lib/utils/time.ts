/** Returns a human-readable relative timestamp in French. */
export function formatRelativeTime(isoString: string): string {
	const date = new Date(isoString);
	const now = new Date();
	const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

	const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
	const msgDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
	const diffDays = Math.round((today.getTime() - msgDate.getTime()) / 86400000);

	if (diffDays === 0) return `Aujourd'hui ${timeStr}`;
	if (diffDays === 1) return `Hier ${timeStr}`;
	if (diffDays < 7) {
		const days = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'];
		return `${days[date.getDay()]} ${timeStr}`;
	}
	const months = [
		'jan', 'fév', 'mar', 'avr', 'mai', 'juin',
		'juil', 'août', 'sep', 'oct', 'nov', 'déc'
	];
	return `${date.getDate()} ${months[date.getMonth()]} ${timeStr}`;
}

export function formatMessageTime(isoString: string): string {
	return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
