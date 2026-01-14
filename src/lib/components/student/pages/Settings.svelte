<!-- Settings.svelte -->
<script lang="ts">
    import { getContext } from 'svelte';
    import { user } from '$lib/stores'; // henna on Récupère les infos de l'utilisateur

    const i18n = getContext('i18n');
</script>

<div class="max-w-4xl mx-auto p-4">
    <!-- En-tête -->
    <div class="mb-8 border-b pb-4">
        <h2 class="text-3xl font-bold text-gray-800 dark:text-white">
            {$i18n.t('Mon Profil d\'Apprenant')}
        </h2>
        <p class="text-gray-500 italic">
            Bienvenue dans votre espace personnel, {$user?.name ?? 'mchkilfrécupéra'}.
        </p>
    </div>

    <!-- Grille principale -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Carte profil -->
        <div class="md:col-span-1 bg-gradient-to-br from-blue-600 to-indigo-700 p-6 rounded-2xl shadow-lg text-white text-center">
            {#if $user?.profile_image_url}
                <img
                    src="{$user.profile_image_url}"
                    alt="Avatar de {$user.name}"
                    class="w-20 h-20 rounded-full mx-auto mb-4 object-cover shadow-inner border-2 border-white"
                />
            {:else}
                <div class="w-20 h-20 bg-white rounded-full mx-auto mb-4 flex items-center justify-center text-blue-700 text-3xl font-bold shadow-inner">
                    {$user?.name?.charAt(0) ?? 'I'}
                </div>
            {/if}
            <h3 class="text-xl font-bold">{$user?.name ?? 'Utilisateur'}</h3>
            <p class="text-blue-100 text-sm mb-4 italic">{$user?.email ?? 'email@inconnu.com'}</p>
        </div>

        <!-- Informations de compte -->
        <div class="md:col-span-2 bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
            <h4 class="text-lg font-semibold mb-4 border-b pb-2">Informations de compte</h4>
            <div class="space-y-4">
                <div class="grid grid-cols-1 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Nom d'utilisateur</label>
                        <p class="p-2 bg-gray-50 dark:bg-gray-900 rounded-lg border">
                            {$user?.name ?? 'Non défini mchkilfrécupéra'}
                        </p>
                    </div>
                    <div>
    <label class="block text-sm font-medium text-gray-400 mb-1">
        Rôle au sein de l'école
    </label>
    <p class="p-2 bg-gray-50 dark:bg-gray-900 rounded-lg border">
        {#if $user?.role === 'user'}
             Apprenant
        {:else}
            Rôle inconnu
        {/if}
    </p>
              </div>

                </div>
                <button class="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-xl transition-all font-medium shadow-md">
                    Mettre à jour mon profil
                </button>
            </div>
        </div>
    </div>
</div>
