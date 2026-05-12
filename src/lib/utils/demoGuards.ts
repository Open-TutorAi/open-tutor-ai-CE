import { get } from 'svelte/store';
import { isDemo } from '$lib/stores';
import { toast } from 'svelte-sonner';

export function isDemoMode(): boolean {
	return get(isDemo);
}

export function useMockData<T>(realData: T, mockData: T): T {
	return isDemoMode() ? mockData : realData;
}

export function preventMutation(action: string = 'This action'): boolean {
	if (isDemoMode()) {
		showDemoToast(`${action} is disabled in demo mode`);
		return true;
	}
	return false;
}

export function showDemoToast(message: string) {
	toast.info(message, {
		duration: 3000
	});
}

export function getDemoModeMessage(context: 'save' | 'delete' | 'upload' | 'submit' | 'general'): string {
	const messages = {
		save: 'Saving is disabled in demo mode',
		delete: 'Deleting is disabled in demo mode',
		upload: 'File uploads are disabled in demo mode',
		submit: 'Submissions are disabled in demo mode',
		general: 'This action is disabled in demo mode'
	};
	
	return messages[context];
}

