<script lang="ts">
    import { onMount } from 'svelte';
    import AvatarChat from '$lib/components/chat/AvatarChat.svelte';
    import { settings } from '$lib/stores';

    // State for classroom settings
    let useClassroom = true;
    let classroomModel: 'default' | 'alternative' = 'default';
    
    onMount(() => {
        // Set the selected avatar ID in settings if not already set
        if (!($settings as any)?.selectedAvatarId) {
            settings.update(s => {
                return { ...s, selectedAvatarId: 'The Scholar' };
            });
        }
    });

    // Toggle classroom visibility
    function toggleClassroom() {
        useClassroom = !useClassroom;
    }

    // Toggle classroom model
    function toggleClassroomModel() {
        classroomModel = classroomModel === 'default' ? 'alternative' : 'default';
    }
</script>

<div class="h-full flex flex-col">
    <div class="flex justify-between items-center p-4 bg-gray-800 text-white">
        <h1 class="text-xl font-bold">Virtual Classroom Experience</h1>
        <div class="flex gap-4">
            <button 
                class="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
                on:click={toggleClassroom}
            >
                {useClassroom ? 'Avatar Only View' : 'Classroom View'}
            </button>
            {#if useClassroom}
                <button 
                    class="px-4 py-2 bg-green-600 rounded hover:bg-green-700"
                    on:click={toggleClassroomModel}
                >
                    {classroomModel === 'default' ? 'Modern Classroom' : 'Traditional Classroom'}
                </button>
            {/if}
        </div>
    </div>
    
    <div class="flex-1 relative overflow-hidden bg-gray-900">
        <AvatarChat 
            className="w-full h-full" 
            {useClassroom}
            {classroomModel}
        />
    </div>
    
    {#if useClassroom}
    <div class="p-2 bg-gray-700 text-white text-sm text-center">
        You're experiencing a virtual classroom with your AI tutor standing at the board. The view is from a student sitting in the front-row desk.
    </div>
    {/if}
</div>

<style>
    :global(body) {
        background-color: #1a202c;
        color: white;
        margin: 0;
        padding: 0;
        height: 100vh;
        overflow: hidden;
    }
</style>
