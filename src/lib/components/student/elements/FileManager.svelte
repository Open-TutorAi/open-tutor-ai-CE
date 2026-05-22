<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';

	interface I18n {
		t: (key: string) => string;
	}
	const i18n = getContext<Writable<I18n>>('i18n');