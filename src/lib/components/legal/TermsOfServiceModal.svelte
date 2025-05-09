<script>
    import { getContext } from 'svelte';
    import Modal from '../common/LegalModal.svelte';

    export let open = false;

    const i18n = getContext('i18n');

    function handleClose() {
        open = false;
    }
</script>

<Modal title={$i18n.t('Terms of Service')} {open} on:close={handleClose}>
    <div class="prose dark:prose-invert max-w-none">
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('Last Updated')}: {new Date().toLocaleDateString()}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('1. Introduction')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('Welcome to OpenTutorAI ("we," "our," or "us"). By accessing or using our AI-powered educational platform, you agree to these Terms of Service. Please read them carefully.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('2. Definitions')}
        </h2>
        <ul class="list-disc pl-6 text-gray-700 dark:text-gray-300">
            <li>{$i18n.t('"Platform" refers to OpenTutorAI\'s website, applications, and services.')}</li>
            <li>{$i18n.t('"User" refers to students, teachers, parents, or any individual accessing our Platform.')}</li>
            <li>{$i18n.t('"Content" refers to all materials, including but not limited to text, images, and educational resources available on the Platform.')}</li>
        </ul>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('3. Account Registration')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('To use certain features of the Platform, you must register for an account. You agree to provide accurate information during the registration process and to keep your password secure. You are responsible for all activities that occur under your account.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('4. Educational Platform Use')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('Our Platform is designed to provide personalized AI-powered learning experiences. Users agree to use the Platform solely for educational purposes and in accordance with all applicable laws and regulations.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('5. User Content')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('By submitting content to our Platform, you grant us a non-exclusive, transferable, sub-licensable, royalty-free, worldwide license to use, modify, publicly display, and distribute such content in connection with the operation of our Platform.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('6. Prohibited Activities')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('Users agree not to:')}
        </p>
        <ul class="list-disc pl-6 text-gray-700 dark:text-gray-300">
            <li>{$i18n.t('Use the Platform to cheat, plagiarize, or engage in academic dishonesty')}</li>
            <li>{$i18n.t('Upload harmful, offensive, or illegal content')}</li>
            <li>{$i18n.t('Attempt to gain unauthorized access to other user accounts or platform systems')}</li>
            <li>{$i18n.t('Use the Platform for commercial purposes without our express permission')}</li>
            <li>{$i18n.t('Engage in any activity that could harm, disrupt, or negatively affect the Platform')}</li>
        </ul>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('7. Data Collection and Privacy')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('We collect and process user data as described in our Privacy Policy. By using our Platform, you consent to our data collection practices outlined therein.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('8. Intellectual Property')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('All content on the Platform, including but not limited to text, graphics, logos, and software, is the property of OpenTutorAI or its licensors and is protected by intellectual property laws.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('9. Termination')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('We reserve the right to suspend or terminate your access to the Platform at any time for violations of these Terms or for any other reason at our sole discretion.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('10. Disclaimer of Warranties')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('The Platform is provided "as is" without warranties of any kind, either express or implied. We do not guarantee that the Platform will be error-free or uninterrupted.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('11. Limitation of Liability')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('To the maximum extent permitted by law, we shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of or inability to use the Platform.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('12. Changes to Terms')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('We may modify these Terms at any time. Continued use of the Platform after changes constitutes acceptance of the modified Terms.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('13. Contact Us')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('If you have any questions about these Terms, please contact us at contact@opentutorai.com.')}
        </p>
    </div>
</Modal> 