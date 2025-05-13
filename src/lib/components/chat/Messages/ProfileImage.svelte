<script lang="ts">
	import { TUTOR_BASE_URL, TUTOR_FRONT_URL } from '$lib/constants';

	export let className = 'size-8';
	export let src = `${TUTOR_FRONT_URL}/static/favicon.png`;
</script>

<img
	crossorigin="anonymous"
	src={src === ''
		? `${TUTOR_FRONT_URL}/static/favicon.png`
		: src.startsWith(TUTOR_BASE_URL) ||
			  src.startsWith('https://www.gravatar.com/avatar/') ||
			  src.startsWith('/')
	alt="profile"
	draggable="false"
/>
