<!--
    Component: TeacherSettings.svelte
    Description: Teacher account settings page.
    Sections: Profile, Security, Preferences.
    FIX: Language now syncs properly between navbar and settings
    FIX: Theme now changes instantly when clicked without needing to save
-->
<script lang="ts">
    import { getContext, onMount } from 'svelte';
    import { fly, fade } from 'svelte/transition';
    import { cubicOut } from 'svelte/easing';
    import type { Writable } from 'svelte/store';
    import type { i18n as i18nType } from 'i18next';
    import { user, theme } from '$lib/stores';
    import i18next from 'i18next';
    import { toast } from 'svelte-sonner';

    const i18n = getContext<Writable<i18nType>>('i18n');
    
    // --- Reactive language state (synced with i18next) ---
    let language: string = i18next.language;

    // --- Profile state (first and last name separated) ---
    let profile = {
        firstName: 'Abdelaziz',
        lastName: 'Boukdous',
        email: $user?.email || 'professeur@example.com',
        avatar: $user?.profile_image_url || '/static/student-avatar.png'
    };

    let isUploading = false;
    let isSavingProfile = false;
    let isSavingPassword = false;

    // --- Preferences ---
    let currentTheme: 'light' | 'dark' | 'system' = $theme || 'system';
    let isSavingPreferences = false;

    // --- Security ---
    let oldPassword = '';
    let newPassword = '';
    let confirmPassword = '';




    let showOldPassword = false;
    let showNewPassword = false;
    let showConfirmPassword = false;

    // --- Tab navigation ---
    let activeTab: 'profile' | 'security' | 'preferences' = 'profile';

    let avatarKey = 0;

    // --- Load profile and preferences on mount ---
    onMount(async () => {
        try {
            // Load profile
            const profileRes = await fetch('/api/v1/settings/profile', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            if (profileRes.ok) {
                const profileData = await profileRes.json();
                const avatarUrl = profileData.avatar 
                    ? (profileData.avatar.startsWith('http') || profileData.avatar.startsWith('/static') 
                        ? profileData.avatar 
                        : `/${profileData.avatar}`)
                    : ($user?.profile_image_url || null);
                profile = {
                    firstName: profileData.firstName || '',
                    lastName: profileData.lastName || '',
                    email: profileData.email || profile.email,
                    avatar: profileData.avatar || $user?.profile_image_url || '/static/student-avatar.png'
                };
                // Sync user store with loaded profile data
                user.update(u => ({
                    ...(u ?? {}),
                    name: `${profileData.firstName || ''} ${profileData.lastName || ''}`.trim(),
                    email: profileData.email || u?.email || '',
                    profile_image_url: profileData.avatar || u?.profile_image_url || '/static/student-avatar.png',
                    _avatar_ts: Date.now()
                }));
                console.log('Profile loaded and synced to user store');
            }

            // Load preferences
            const prefsRes = await fetch('/api/v1/settings/preferences', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            if (prefsRes.ok) {
                const prefsData = await prefsRes.json();
                language = prefsData.language || 'en-US';
                currentTheme = prefsData.theme || 'system';
            }
        } catch (err) {
            console.error('Error loading settings:', err);
        }

        // Listen for language changes from navbar or any other source
        const handleLanguageChange = (lng: string) => {
            language = lng;
        };
        
        i18next.on('languageChanged', handleLanguageChange);
        
        return () => {
            i18next.off('languageChanged', handleLanguageChange);
        };
    });

    // --- Actions ---
    async function handleAvatarChange(e) {
        const file = (e.target as HTMLInputElement).files?.[0];
        if (!file) return;

        console.log('📁 File selected:', file.name, file.size, file.type);
        isUploading = true;

        try {
            const formData = new FormData();
            formData.append('file', file);

            console.log('📤 Uploading to /api/v1/settings/avatar...');
            const response = await fetch('/api/v1/settings/avatar', { 
                method: 'POST', 
                body: formData 
            });

            console.log('📥 Response status:', response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('✅ API Response:', JSON.stringify(data, null, 2));

                // الـ API ممكن كيرجع avatar_url أو avatar أو url
                const newAvatarUrl = data.avatar_url || data.avatar || data.url || null;
                console.log('🖼️ New avatar URL:', newAvatarUrl);

                if (!newAvatarUrl) {
                    console.error('❌ API رجع بيانات بدون avatar URL!');
                    alert('ال API ما رجعش رابط الصورة');
                    isUploading = false;
                    return;
                }

                // Update profile state
                profile.avatar = newAvatarUrl;
                avatarKey = Date.now();

                // Update user store
                user.update(u => ({ 
                    ...(u ?? {}), 
                    profile_image_url: newAvatarUrl, 
                    _avatar_ts: Date.now() 
                }));

                // Save to localStorage
                localStorage.setItem('profile_avatar', newAvatarUrl);


                // Dispatch event for navbar
                window.dispatchEvent(new CustomEvent('avatar-updated', { 
                    detail: { url: newAvatarUrl } 
                }));

                console.log('🎉 Avatar updated successfully!');
            } else {
                const errorText = await response.text();
                console.error('❌ Upload failed:', response.status, errorText);
                alert('Erreur lors du téléchargement: ' + errorText);
            }
        } catch (err) {
            console.error('💥 Upload error:', err);
            alert('Erreur: ' + err.message);
        } finally {
            isUploading = false;
        }
    }

    async function saveProfile() {
        isSavingProfile = true;
        try {
            const response = await fetch('/api/v1/settings/profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    firstName: profile.firstName,
                    lastName: profile.lastName,
                    email: profile.email,
                    avatar: profile.avatar
                })
            });

            if (response.ok) {
                const fullName = `${profile.firstName} ${profile.lastName}`.trim();

                user.update(u => ({
                    ...(u ?? {}),
                    name: fullName,
                    email: profile.email,
                    profile_image_url: profile.avatar,
                    _avatar_ts: Date.now()
                }));

                localStorage.setItem('profile_avatar', profile.avatar);

                window.dispatchEvent(new CustomEvent('avatar-updated', {
                    detail: { url: profile.avatar }
                }));

                alert($i18n.t('Profil mis à jour avec succès'));
            } else {
                const error = await response.json();
                alert(error.detail || $i18n.t('Erreur lors de la mise à jour du profil'));
            }
        } catch (err) {
            console.error('Error saving profile:', err);
            alert($i18n.t('Erreur lors de la mise à jour du profil'));
        } finally {
            isSavingProfile = false;
        }
    }

    async function changePassword() {
        if (newPassword !== confirmPassword) {
            alert($i18n.t('Les mots de passe ne correspondent pas'));
            return;
        }

        if (newPassword.length < 8) {
            alert($i18n.t('Le mot de passe doit contenir au moins 8 caractères'));
            return;
        }

        isSavingPassword = true;
        try {
            const response = await fetch('/api/v1/settings/password', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    oldPassword: oldPassword,
                    newPassword: newPassword
                })
            });

            if (response.ok) {
                alert($i18n.t('Mot de passe modifié'));
                oldPassword = newPassword = confirmPassword = '';
            } else {
                const error = await response.json();
                alert(error.detail || $i18n.t('Erreur lors du changement du mot de passe'));
            }
        } catch (err) {
            console.error('Error changing password:', err);
            alert($i18n.t('Erreur lors du changement du mot de passe'));
        } finally {
            isSavingPassword = false;
        }
    }

    function applyTheme(newTheme: 'light' | 'dark' | 'system') {
        currentTheme = newTheme;
        theme.set(newTheme);
        localStorage.setItem('theme', newTheme);
    }

    async function savePreferences() {
        isSavingPreferences = true;
        try {
            // Apply language immediately
            await i18next.changeLanguage(language);
            localStorage.setItem('locale', language);

            // Save to backend (non-blocking)
            const token = localStorage.getItem('token') ?? '';
            fetch('/api/v1/settings/preferences', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {})
                },
                body: JSON.stringify({ language, theme: currentTheme })
            }).catch(() => {});

            toast.success($i18n.t('Préférences enregistrées'));
        } catch (err) {
            console.error('Error saving preferences:', err);
            toast.error($i18n.t('Erreur lors de l\'enregistrement des préférences'));
        } finally {
            isSavingPreferences = false;
        }
    }

    // --- Tab configuration ---
    const tabs = [
        {
            id: 'profile',
            labelKey: 'Profil',
            icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>`
        },
        {
            id: 'security',
            labelKey: 'Sécurité',
            icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>`
        },
        {
            id: 'preferences',
            labelKey: 'Préférences',
            icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>`
        }
    ];

</script>

<div class="settings-page">

    <!-- Main container: sidebar + content -->
    <div class="page-wrapper">
        <!-- LEFT COLUMN: Sidebar -->
        <aside class="sidebar" in:fly={{ x: -20, duration: 400, easing: cubicOut }}>
            <!-- Profile card -->
            <div class="profile-hero">
                <div class="avatar-wrapper">
                    {#key avatarKey}
                        <img src={profile.avatar} alt="Avatar" class="avatar" />
                    {/key}
                    <label class="avatar-upload" title={$i18n.t('Changer la photo')}>
                        {#if isUploading}
                            <span class="spin-ring"></span>
                        {:else}
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5"
                                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5"
                                    d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/>
                            </svg>
                        {/if}
                        <input type="file" accept="image/*" on:change={handleAvatarChange} hidden />
                    </label>
                </div>
                <h2 class="hero-name">{profile.firstName} {profile.lastName}</h2>
                <p class="hero-email">{profile.email}</p>
                <span class="hero-badge">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>
                    </svg>
                    {$i18n.t('Professeur')}
                </span>
            </div>

            <!-- Tab navigation -->
            <nav class="tab-nav">
                {#each tabs as tab}
                    <button
                        class="tab-btn {activeTab === tab.id ? 'active' : ''}"
                        on:click={() => (activeTab = tab.id)}
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
                            {@html tab.icon}
                        </svg>
                        <span>{$i18n.t(tab.labelKey)}</span>
                        {#if activeTab === tab.id}
                            <span class="tab-dot"></span>
                        {/if}
                    </button>
                {/each}
            </nav>
        </aside>

        <!-- RIGHT COLUMN: Dynamic content -->
        <main class="content" in:fly={{ x: 20, duration: 400, easing: cubicOut }}>

            <!-- ========== PROFILE TAB ========== -->
            {#if activeTab === 'profile'}
                <div class="panel" in:fade={{ duration: 200 }}>
                    <div class="panel-header">
                        <div class="panel-icon blue">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="20" height="20">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                            </svg>
                        </div>
                        <div>
                            <h2 class="panel-title">{$i18n.t('Informations du profil')}</h2>
                            <p class="panel-sub">{$i18n.t('Mettez à jour vos informations personnelles')}</p>
                        </div>
                    </div>
                    <div class="divider"></div>
                    <div class="form-stack">
                        <!-- First name -->
                        <div class="input-group">
                            <label class="input-label">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                                </svg>
                                {$i18n.t('Prénom')}
                            </label>
                            <input type="text" bind:value={profile.firstName} class="field" placeholder={$i18n.t('Votre prénom...')} />
                        </div>
                        <!-- Last name -->
                        <div class="input-group">
                            <label class="input-label">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                                </svg>
                                {$i18n.t('Nom')}
                            </label>
                            <input type="text" bind:value={profile.lastName} class="field" placeholder={$i18n.t('Votre nom...')} />
                        </div>
                        <!-- Email -->
                        <div class="input-group">
                            <label class="input-label">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                                </svg>
                                {$i18n.t('Adresse email')}
                            </label>
                            <input type="email" bind:value={profile.email} class="field" placeholder={$i18n.t('votre@email.com')} />
                        </div>
                    </div>
                    <div class="panel-footer">
                        <button class="btn-save" on:click={saveProfile} disabled={isSavingProfile}>
                            {#if isSavingProfile}
                                <span class="spin-ring-small"></span>
                            {:else}
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                                </svg>
                            {/if}
                            {isSavingProfile ? $i18n.t('Enregistrement...') : $i18n.t('Enregistrer les modifications')}
                        </button>
                    </div>
                </div>

            <!-- ========== SECURITY TAB ========== -->
            {:else if activeTab === 'security'}
                <div class="panel" in:fade={{ duration: 200 }}>
                    <div class="panel-header">
                        <div class="panel-icon purple">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="20" height="20">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                            </svg>
                        </div>
                        <div>
                            <h2 class="panel-title">{$i18n.t('Sécurité du compte')}</h2>
                            <p class="panel-sub">{$i18n.t('Changez votre mot de passe régulièrement')}</p>
                        </div>
                    </div>
                    <div class="divider"></div>
                    <div class="security-tip">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        {$i18n.t('Utilisez au moins 8 caractères avec des chiffres et symboles.')}
                    </div>
                    <div class="form-stack">
                        <div class="input-group">
                            <label class="input-label">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                                </svg>
                                {$i18n.t('Ancien mot de passe')}
                            </label>
                            <div class="password-wrapper">
                                {#if showOldPassword}
                                    <input type="text" bind:value={oldPassword} class="field" placeholder="••••••••" />
                                {:else}
                                    <input type="password" bind:value={oldPassword} class="field" placeholder="••••••••" />
                                {/if}
                                <button type="button" class="toggle-password" on:click={() => (showOldPassword = !showOldPassword)}>
                                    {#if showOldPassword}
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                                        </svg>
                                    {:else}
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                                        </svg>
                                    {/if}
                                </button>
                            </div>
                        </div>
                        <div class="input-group">
                            <label class="input-label">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
                                </svg>
                                {$i18n.t('Nouveau mot de passe')}
                            </label>
                            <div class="password-wrapper">
                                {#if showNewPassword}
                                    <input type="text" bind:value={newPassword} class="field" placeholder="••••••••" />
                                {:else}
                                    <input type="password" bind:value={newPassword} class="field" placeholder="••••••••" />
                                {/if}
                                <button type="button" class="toggle-password" on:click={() => (showNewPassword = !showNewPassword)}>
                                    {#if showNewPassword}
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                                        </svg>
                                    {:else}
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                                        </svg>
                                    {/if}
                                </button>
                            </div>
                        </div>
                        <div class="input-group">
                            <label class="input-label">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                                </svg>
                                {$i18n.t('Confirmer le mot de passe')}
                            </label>
                            <div class="password-wrapper">
                                {#if showConfirmPassword}
                                    <input type="text" bind:value={confirmPassword} class="field" placeholder="••••••••" />
                                {:else}
                                    <input type="password" bind:value={confirmPassword} class="field" placeholder="••••••••" />
                                {/if}
                                <button type="button" class="toggle-password" on:click={() => (showConfirmPassword = !showConfirmPassword)}>
                                    {#if showConfirmPassword}
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                                        </svg>
                                    {:else}
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                                        </svg>
                                    {/if}
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="panel-footer">
                        <button class="btn-save purple-btn" on:click={changePassword} disabled={isSavingPassword}>
                            {#if isSavingPassword}
                                <span class="spin-ring-small"></span>
                            {:else}
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                                </svg>
                            {/if}
                            {isSavingPassword ? $i18n.t('Mise à jour...') : $i18n.t('Mettre à jour le mot de passe')}
                        </button>
                    </div>
                </div>

            <!-- ========== PREFERENCES TAB ========== -->
            {:else if activeTab === 'preferences'}
                <div class="panel" in:fade={{ duration: 200 }}>
                    <div class="panel-header">
                        <div class="panel-icon green">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="20" height="20">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            </svg>
                        </div>
                        <div>
                            <h2 class="panel-title">{$i18n.t('Préférences')}</h2>
                            <p class="panel-sub">{$i18n.t('Personnalisez votre expérience')}</p>
                        </div>
                    </div>
                    <div class="divider"></div>
                    <div class="pref-list-new">
                        <!-- Language option -->
                        <div class="pref-card">
                            <div class="pref-card-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" stroke-linecap="round"/>
                                    <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke-linecap="round"/>
                                </svg>
                            </div>
                            <div class="pref-card-content">
                                <div class="pref-card-header">
                                    <label class="pref-card-title">{$i18n.t('Langue')}</label>
                                    <p class="pref-card-desc">{$i18n.t('Choisissez la langue de l\'interface')}</p>
                                </div>
                                <div class="lang-selector">
                                    {#each [
                                        { code: 'fr-FR', flag: '🇫🇷', name: 'Français' },
                                        { code: 'en-US', flag: '🇺🇸', name: 'English' },
                                        { code: 'ar-MA', flag: '🇲🇦', name: 'العربية' }
                                    ] as langOpt}
                                        <button
                                            class="lang-option {language === langOpt.code ? 'active' : ''}"
                                            on:click={() => {
                                                language = langOpt.code;
                                                i18next.changeLanguage(langOpt.code);
                                                localStorage.setItem('locale', langOpt.code);
                                            }}
                                        >
                                            <span class="lang-flag">{langOpt.flag}</span>
                                            <span class="lang-name">{langOpt.name}</span>
                                            {#if language === langOpt.code}
                                                <span class="check-mark">✓</span>
                                            {/if}
                                        </button>
                                    {/each}
                                </div>
                            </div>
                        </div>

                        <!-- Elegant separator -->
                        <div class="pref-separator"></div>

                        <!-- Theme option -->
                        <div class="pref-card">
                            <div class="pref-card-icon theme-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke-linecap="round"/>
                                </svg>
                            </div>
                            <div class="pref-card-content">
                                <div class="pref-card-header">
                                    <label class="pref-card-title">{$i18n.t('Thème')}</label>
                                    <p class="pref-card-desc">{$i18n.t('Personnalisez l\'apparence')}</p>
                                </div>
                                <div class="theme-selector">
                                    {#each [
                                        { id: 'light', icon: '☀️', label: 'Clair' },
                                        { id: 'system', icon: '💻', label: 'Système' },
                                        { id: 'dark', icon: '🌙', label: 'Sombre' }
                                    ] as themeOpt}
                                        <button
                                            class="theme-option {currentTheme === themeOpt.id ? 'active' : ''}"
                                            on:click={() => applyTheme(themeOpt.id)}
                                        >
                                            <span class="theme-icon-large">{themeOpt.icon}</span>
                                            <span class="theme-label">{$i18n.t(themeOpt.label)}</span>
                                            <div class="theme-radio {currentTheme === themeOpt.id ? 'checked' : ''}">
                                                {#if currentTheme === themeOpt.id}
                                                    <span class="radio-dot"></span>
                                                {/if}
                                            </div>
                                        </button>
                                    {/each}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="panel-footer">
                        <button class="btn-save green-btn" on:click={savePreferences} disabled={isSavingPreferences}>
                            {#if isSavingPreferences}
                                <span class="spin-ring-small"></span>
                            {:else}
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                                </svg>
                            {/if}
                            {isSavingPreferences ? $i18n.t('Enregistrement...') : $i18n.t('Appliquer les préférences')}
                        </button>
                    </div>
                </div>
            {/if}
        </main>
    </div>
</div>

<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    /* --- Base --- */
    .settings-page {
        font-family: 'Plus Jakarta Sans', sans-serif;
        max-width: 1100px;
        margin: 0 auto;
        padding: 1.5rem 2rem 3rem;
        color: #0f172a;
    }
    :global(.dark) .settings-page {
        color: #f1f5f9;
    }

    /* --- Main layout --- */
    .page-wrapper {
        display: flex;
        gap: 2rem;
        align-items: flex-start;
    }

    /* --- Sidebar --- */
    .sidebar {
        width: 260px;
        flex-shrink: 0;
        position: sticky;
        top: 2rem;
    }

    .profile-hero {
        background: linear-gradient(145deg, #2563eb, #4f46e5);
        border-radius: 1.5rem;
        padding: 2rem 1rem 1.5rem;
        text-align: center;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 8px 20px -6px rgba(37, 99, 235, 0.4);
    }

    .avatar-wrapper {
        position: relative;
        display: inline-block;
    }
    .avatar {
        width: 88px;
        height: 88px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid rgba(255,255,255,0.4);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .avatar-upload {
        position: absolute;
        bottom: 0;
        right: 0;
        width: 30px;
        height: 30px;
        background: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        transition: transform 0.15s;
        color: #2563eb;
    }
    .avatar-upload:hover {
        transform: scale(1.1);
    }
    .spin-ring {
        width: 16px;
        height: 16px;
        border: 2px solid #e0e7ff;
        border-top-color: #2563eb;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    .spin-ring-small {
        width: 12px;
        height: 12px;
        border: 2px solid rgba(255,255,255,0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        display: inline-block;
    }

    .hero-name {
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0.75rem 0 0.25rem;
    }
    .hero-email {
        font-size: 0.75rem;
        opacity: 0.8;
        margin: 0 0 0.75rem;
        word-break: break-all;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: rgba(255,255,255,0.2);
        backdrop-filter: blur(4px);
        border-radius: 2rem;
        padding: 0.25rem 0.9rem;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .tab-nav {
        background: white;
        border-radius: 1.25rem;
        padding: 0.5rem;
        border: 1px solid #eef2f6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    :global(.dark) .tab-nav {
        background: #1e293b;
        border-color: #334155;
    }

    .tab-btn {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        width: 100%;
        padding: 0.8rem 1rem;
        border: none;
        background: none;
        border-radius: 0.85rem;
        font-size: 0.9rem;
        font-weight: 500;
        color: #64748b;
        cursor: pointer;
        transition: all 0.15s;
        text-align: left;
    }
    .tab-btn:hover {
        background: #f8faff;
        color: #2563eb;
    }
    :global(.dark) .tab-btn:hover {
        background: #1e2d45;
        color: #93c5fd;
    }
    .tab-btn.active {
        background: #eef2ff;
        color: #2563eb;
        font-weight: 600;
    }
    :global(.dark) .tab-btn.active {
        background: #1e3a8a;
        color: #93c5fd;
    }
    .tab-dot {
        width: 6px;
        height: 6px;
        background: #2563eb;
        border-radius: 50%;
        margin-left: auto;
    }

    /* --- Main content (panels) --- */
    .content {
        flex: 1;
        min-width: 0;
    }

    .panel {
        background: white;
        border-radius: 1.5rem;
        border: 1px solid #eef2f6;
        box-shadow: 0 4px 24px rgba(0,0,0,0.04);
        overflow: hidden;
    }
    :global(.dark) .panel {
        background: #1e293b;
        border-color: #334155;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }

    .panel-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.75rem 2rem;
    }
    .panel-icon {
        width: 48px;
        height: 48px;
        border-radius: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .panel-icon.blue  { background: #eef2ff; color: #2563eb; }
    .panel-icon.purple{ background: #f5f3ff; color: #7c3aed; }
    .panel-icon.green { background: #ecfdf5; color: #059669; }
    :global(.dark) .panel-icon.blue  { background: #1e3a8a; color: #93c5fd; }
    :global(.dark) .panel-icon.purple{ background: #2d1b69; color: #c4b5fd; }
    :global(.dark) .panel-icon.green { background: #064e3b; color: #6ee7b7; }

    .panel-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0 0 0.2rem;
    }
    .panel-sub {
        font-size: 0.82rem;
        color: #94a3b8;
        margin: 0;
    }

    .divider {
        height: 1px;
        background: #f1f5f9;
        margin: 0 2rem;
    }
    :global(.dark) .divider {
        background: #334155;
    }

    .form-stack {
        padding: 1.75rem 2rem;
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    .input-group {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }
    .input-label {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    :global(.dark) .input-label {
        color: #94a3b8;
    }

    .field {
        padding: 0.8rem 1.1rem;
        border: 1.5px solid #e2e8f0;
        border-radius: 0.85rem;
        background: #fafbfc;
        font-size: 0.95rem;
        color: #0f172a;
        transition: border 0.15s, box-shadow 0.15s;
        width: 100%;
        box-sizing: border-box;
    }
    .field:focus {
        border-color: #2563eb;
        outline: none;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        background: white;
    }
    :global(.dark) .field {
        background: #0f172a;
        border-color: #334155;
        color: #f1f5f9;
    }

    .security-tip {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 0.75rem;
        padding: 0.75rem 1.25rem;
        margin: 1.25rem 2rem 0;
        font-size: 0.82rem;
        color: #92400e;
    }
    :global(.dark) .security-tip {
        background: #292100;
        border-color: #7c5a00;
        color: #fcd34d;
    }

    .panel-footer {
        padding: 1.25rem 2rem 1.75rem;
        border-top: 1px solid #f1f5f9;
        display: flex;
        justify-content: flex-end;
    }
    :global(.dark) .panel-footer {
        border-top-color: #334155;
    }

    /* Buttons */
    .btn-save {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        background: linear-gradient(145deg, #2563eb, #4f46e5);
        color: white;
        border: none;
        border-radius: 0.85rem;
        font-size: 0.9rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        transition: transform 0.1s, box-shadow 0.15s;
    }
    .btn-save:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.45);
    }
    .btn-save:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none;
    }
    .btn-save:disabled:hover {
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
    }
    .btn-save.purple-btn {
        background: linear-gradient(145deg, #7c3aed, #6d28d9);
        box-shadow: 0 4px 14px rgba(124, 58, 237, 0.35);
    }
    .btn-save.green-btn {
        background: linear-gradient(145deg, #059669, #047857);
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.35);
    }

    /* Preferences */
    .pref-list-new {
        padding: 0.5rem 2rem 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .pref-card {
        display: flex;
        gap: 1.25rem;
        align-items: flex-start;
        padding: 0.75rem 0;
    }

    .pref-card-icon {
        width: 44px;
        height: 44px;
        background: linear-gradient(145deg, #eef2ff, #ffffff);
        border-radius: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #2563eb;
        box-shadow: 0 6px 10px -4px rgba(37, 99, 235, 0.12);
        border: 1px solid rgba(255,255,255,0.6);
        flex-shrink: 0;
    }
    :global(.dark) .pref-card-icon {
        background: linear-gradient(145deg, #1e3a8a, #1e293b);
        color: #93c5fd;
        border-color: #334155;
        box-shadow: 0 6px 10px -4px rgba(0,0,0,0.4);
    }

    .pref-card-content {
        flex: 1;
    }

    .pref-card-header {
        margin-bottom: 0.9rem;
    }

    .pref-card-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        display: block;
        margin-bottom: 0.2rem;
    }
    :global(.dark) .pref-card-title {
        color: #f1f5f9;
    }

    .pref-card-desc {
        font-size: 0.8rem;
        color: #64748b;
        margin: 0;
    }
    :global(.dark) .pref-card-desc {
        color: #94a3b8;
    }

    .pref-separator {
        height: 1px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        margin: 0.5rem 0 0.5rem 3.5rem;
    }
    :global(.dark) .pref-separator {
        background: linear-gradient(90deg, transparent, #334155, transparent);
    }

    /* Language selector (buttons) */
    .lang-selector {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
    }

    .lang-option {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.55rem 1rem;
        background: #f8fafc;
        border: 1.5px solid #e2e8f0;
        border-radius: 2.5rem;
        font-size: 0.9rem;
        font-weight: 500;
        color: #334155;
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.23, 1, 0.32, 1);
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .lang-option:hover {
        background: #ffffff;
        border-color: #2563eb;
        transform: translateY(-1px);
        box-shadow: 0 6px 10px -4px rgba(37, 99, 235, 0.15);
    }
    .lang-option.active {
        background: #2563eb;
        border-color: #2563eb;
        color: white;
        box-shadow: 0 8px 14px -6px rgba(37, 99, 235, 0.35);
    }
    :global(.dark) .lang-option {
        background: #1e293b;
        border-color: #334155;
        color: #cbd5e1;
    }
    :global(.dark) .lang-option:hover {
        background: #2d3a52;
        border-color: #60a5fa;
        color: #f1f5f9;
    }
    :global(.dark) .lang-option.active {
        background: #2563eb;
        border-color: #2563eb;
        color: white;
    }

    .lang-flag {
        font-size: 1.2rem;
        line-height: 1;
    }

    .check-mark {
        font-size: 0.9rem;
        font-weight: 700;
        margin-left: 0.2rem;
    }

    /* Theme selector */
    .theme-selector {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
    }

    .theme-option {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.65rem 1rem;
        background: #f8fafc;
        border: 1.5px solid #e2e8f0;
        border-radius: 1rem;
        width: 100%;
        cursor: pointer;
        transition: all 0.2s;
        text-align: left;
    }
    .theme-option:hover {
        background: #ffffff;
        border-color: #2563eb;
        box-shadow: 0 4px 8px -2px rgba(37, 99, 235, 0.1);
    }
    .theme-option.active {
        background: #eef2ff;
        border-color: #2563eb;
    }
    :global(.dark) .theme-option {
        background: #1e293b;
        border-color: #334155;
    }
    :global(.dark) .theme-option:hover {
        background: #2d3a52;
        border-color: #60a5fa;
    }
    :global(.dark) .theme-option.active {
        background: #1e3a8a;
        border-color: #3b82f6;
    }

    .theme-icon-large {
        font-size: 1.6rem;
        line-height: 1;
        width: 32px;
        text-align: center;
    }

    .theme-label {
        flex: 1;
        font-size: 0.95rem;
        font-weight: 500;
        color: #1e293b;
    }
    :global(.dark) .theme-label {
        color: #f1f5f9;
    }

    .theme-radio {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        border: 2px solid #cbd5e1;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: border-color 0.15s;
        background: white;
    }
    .theme-option.active .theme-radio {
        border-color: #2563eb;
    }
    :global(.dark) .theme-radio {
        background: #0f172a;
        border-color: #475569;
    }
    :global(.dark) .theme-option.active .theme-radio {
        border-color: #3b82f6;
    }

    .radio-dot {
        width: 10px;
        height: 10px;
        background: #2563eb;
        border-radius: 50%;
        display: inline-block;
    }
    :global(.dark) .radio-dot {
        background: #3b82f6;
    }

    /* --- Password wrapper & toggle --- */
    .password-wrapper {
        position: relative;
        display: flex;
        align-items: center;
    }

    .password-wrapper .field {
        padding-right: 2.8rem;  /* laisse la place pour le bouton */
    }

    .toggle-password {
        position: absolute;
        right: 0.6rem;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        cursor: pointer;
        color: #94a3b8;
        padding: 0.35rem;
        border-radius: 0.4rem;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: color 0.15s, background 0.15s;
        line-height: 1;
    }

    .toggle-password:hover {
        color: #2563eb;
        background: #eef2ff;
    }

    :global(.dark) .toggle-password {
        color: #64748b;
    }

    :global(.dark) .toggle-password:hover {
        color: #93c5fd;
        background: #1e3a8a;
    }
    /* Responsive */
    @media (max-width: 768px) {
        .settings-page {
            padding: 1rem;
        }
        .page-wrapper {
            flex-direction: column;
        }
        .sidebar {
            width: 100%;
            position: static;
        }
        .profile-hero {
            padding: 1.5rem 1rem;
        }
        .tab-nav {
            flex-direction: row;
            overflow-x: auto;
        }
        .tab-btn {
            flex-shrink: 0;
        }
        .tab-dot {
            display: none;
        }
        .panel-header, .panel-footer, .form-stack, .pref-list {
            padding-left: 1.25rem;
            padding-right: 1.25rem;
        }
        .divider {
            margin-left: 1.25rem;
            margin-right: 1.25rem;
        }
        .security-tip {
            margin-left: 1.25rem;
            margin-right: 1.25rem;
        }
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }
</style>