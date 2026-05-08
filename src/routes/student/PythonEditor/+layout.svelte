<!-- student/PythonEditor/+layout.svelte -->
<script lang="ts">
    import { onMount } from 'svelte';
    
    onMount(() => {
        document.body.style.overflow = 'hidden';
    });
</script>

<div class="python-layout-container h-full w-full flex flex-col overflow-hidden">
    <slot />
</div>

<style>
    .python-layout-container {
        height: 100%;
        width: 100%;
        position: relative;
    }
</style>