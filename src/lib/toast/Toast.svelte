<script>
  export let message = '';
  export let type = 'success'; // 'success', 'error', 'info'
  let visible = true;
  
  setTimeout(() => {
    visible = false;
  }, 3000);
</script>

{#if visible}
  <div class="fixed bottom-4 right-4 z-50 animate-slide-in">
    <div class="rounded-xl shadow-lg border p-4 min-w-[280px] {type === 'success' ? 'bg-green-50 border-green-200 text-green-800' : type === 'error' ? 'bg-red-50 border-red-200 text-red-800' : 'bg-blue-50 border-blue-200 text-blue-800'}">
      <div class="flex items-center gap-3">
        <span class="text-xl">
          {#if type === 'success'}✅
          {:else if type === 'error'}❌
          {:else}ℹ️
          {/if}
        </span>
        <span class="text-sm font-medium">{message}</span>
      </div>
    </div>
  </div>
{/if}

<style>
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  .animate-slide-in {
    animation: slideIn 0.3s ease;
  }
</style>