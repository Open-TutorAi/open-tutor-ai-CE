<script>
    import { getContext, onMount } from 'svelte';
    import { fade, fly } from 'svelte/transition';
    import { cubicOut } from 'svelte/easing';
    const i18n = getContext('i18n');

    import { WEBUI_BASE_URL } from '$lib/constants';

    import Marquee from './common/Marquee.svelte';
    import SlideShow from './common/SlideShow.svelte';
    import ArrowRightCircle from './icons/ArrowRightCircle.svelte';

    export let show = true;
    export let getStartedHandler = () => {};
    
    // Accessibility focus management
    let startButton;
    
    onMount(() => {
        // Set initial focus on start button for keyboard users
        if (show && startButton) {
            startButton.focus();
        }
        
        // Add escape key listener to trigger getStartedHandler
        const handleKeydown = (e) => {
            if (e.key === 'Escape' && show) {
                getStartedHandler();
            }
        };
        
        window.addEventListener('keydown', handleKeydown);
        return () => {
            window.removeEventListener('keydown', handleKeydown);
        };
    });
    
    // Track loading state
    let isLoaded = false;
    
    function handleImagesLoaded() {
        isLoaded = true;
    }
</script>

<svelte:head>
	<title>
		OpenTutorAI
	</title>
	  <link rel="icon" href="favicon/favicon.ico" type="image/x-icon">
	  <link rel="icon" href="favicon/favicon-96x96.png" type="image/png">
	  <link rel="apple-touch-icon" href="favicon/apple-touch-icon.png">
	  <link rel="manifest" href="favicon/site.webmanifest">

</svelte:head>

{#if show}
   <div 
    class="w-full h-screen max-h-[100dvh] text-white relative flex flex-col items-center justify-center overflow-hidden"
    role="dialog"
    aria-modal="true"
    aria-labelledby="onboarding-title"
>
    <!-- Loading Indicator -->
    {#if !isLoaded}
        <div class="absolute inset-0 flex items-center justify-center z-50 bg-black">
            <div class="w-16 h-16 border-t-4 border-blue-500 border-solid rounded-full animate-spin"></div>
        </div>
    {/if}
    
    <!-- Logo -->
    <div 
        class="fixed top-5 left-5 z-50 flex items-center space-x-3"
        in:fade={{ duration: 800, delay: 300 }}
    >
        <img 
            crossorigin="anonymous" 
            src="{WEBUI_BASE_URL}/static/favicon.png" 
            class="w-8 h-8 rounded-full" 
            alt="OpenTutorAI logo" 
            on:load={handleImagesLoaded}
        />
        <span class="text-lg font-semibold">{$i18n.t('Welcome to')} OpenTutorAI</span>
    </div>

    <!-- Skip to content button for screen readers -->
    <a 
        href="#main-content"
        class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:right-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-700 focus:text-white focus:rounded-md"
    >
        {$i18n.t('Skip to main content')}
    </a>

    <!-- Background Slideshow -->
    <SlideShow duration={5000} />

    <!-- Enhanced Overlay - Gradient + Blur for better readability -->
    <div 
        class="absolute inset-0 backdrop-blur-lg bg-gradient-to-b from-black/70 via-black/60 to-black/80"
        in:fade={{ duration: 1000 }}
    ></div>

    <!-- Main Content with animation -->
    <div 
        id="main-content"
        class="relative text-center px-6 sm:px-10 lg:px-20 max-w-4xl mx-auto min-h-[60vh] flex flex-col justify-center"
        in:fly={{ y: 20, duration: 800, delay: 400, easing: cubicOut }}
    >
        <h1 
            id="onboarding-title"
            class="text-3xl sm:text-5xl lg:text-7xl font-extrabold leading-snug sm:leading-tight mb-6 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500"
        >
            <Marquee
                duration={4000}
                words={[
                    $i18n.t('Free Quality Education'),
                    $i18n.t('Learn Anytime Anywhere'),
                    $i18n.t('Personalized Learning Experience'),
                    $i18n.t('AI-Driven Education'),
                    $i18n.t('Interactive Video Lessons'),
                    $i18n.t('Student-Centered Learning'),
                    $i18n.t('Innovative Teaching Tools'),
                    $i18n.t('Mastery-Based Progression')
                ]}
            />
        </h1>

        <p class="mt-4 text-lg sm:text-xl lg:text-2xl text-gray-200 max-w-2xl mx-auto leading-relaxed">
            {$i18n.t('Learn, explore, and grow wherever you are.')}
        </p>

        

        <!-- Get Started Button -->
        <div class="mt-10 sm:mt-12 flex justify-center">
            <button
                bind:this={startButton}
                class="relative group flex items-center justify-center px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 transition-all duration-300 rounded-full text-lg font-medium text-white focus:outline-none focus:ring-4 focus:ring-blue-300 focus:ring-offset-2 focus:ring-offset-black transform hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl whitespace-nowrap space-x-2"
                aria-label={$i18n.t('Get Started with OpenTutorAI')}
                on:click={() => getStartedHandler()}
                in:fly={{ y: 20, duration: 800, delay: 800, easing: cubicOut }}
            >
                <span>{$i18n.t(`Get Started`)}</span>
                <ArrowRightCircle class="size-8 transition-transform duration-300 group-hover:translate-x-1" />
            
            </button>
        </div>
        
        <!-- Privacy note -->
        <p class="mt-6 text-sm text-gray-400 max-w-md mx-auto">
            {$i18n.t('Your privacy matters. We prioritize keeping your learning journey secure and private.')}
        </p>
    </div>
    
    <!-- Decorative elements -->
    <div class="absolute bottom-0 left-0 w-full h-40 bg-gradient-to-t from-blue-900/20 to-transparent"></div>
    <div class="absolute -bottom-20 -left-20 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl"></div>
    <div class="absolute -top-20 -right-20 w-64 h-64 bg-purple-600/10 rounded-full blur-3xl"></div>
    
    <!-- Skip button -->
    <button 
        class="absolute bottom-8 text-sm text-gray-400 hover:text-white transition-colors"
        on:click={() => getStartedHandler()}
        aria-label={$i18n.t('Skip onboarding')}
    >
        {$i18n.t('Skip')}
    </button>
</div>

{/if}