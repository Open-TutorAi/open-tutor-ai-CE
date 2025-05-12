<script lang="ts">
	import { TUTOR_FRONT_URL, TUTOR_BASE_URL } from '$lib/constants';

	export let className = 'size-8';
	export let src = `${TUTOR_FRONT_URL}/static/favicon.png`;
</script>

<img
	crossorigin="anonymous"
	src={src === ''
		? `${TUTOR_FRONT_URLL}/static/favicon.png`
		: src.startsWith(TUTOR_BASE_URL) ||
			  src.startsWith('https://www.gravatar.com/avatar/') ||
			  src.startsWith('data:') ||
			  src.startsWith('/')
			? src
			: `/user.png`}
	class=" {className} object-cover rounded-full -translate-y-[1px]"
	alt="profile"
	draggable="false"
/>
