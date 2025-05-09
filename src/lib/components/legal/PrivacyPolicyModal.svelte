<script>
    import { getContext } from 'svelte';
    import Modal from '../common/LegalModal.svelte';

    export let open = false;

    const i18n = getContext('i18n');

    function handleClose() {
        open = false;
    }
</script>

<Modal title={$i18n.t('Privacy Policy')} {open} on:close={handleClose}>
    <div class="prose dark:prose-invert max-w-none">
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('Last Updated')}: {new Date().toLocaleDateString()}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('1. Introduction')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('At OpenTutorAI, we are committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our educational AI platform. Please read this policy carefully.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('2. Information We Collect')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('We collect information in the following categories:')}
        </p>
        <h3 class="text-lg font-medium mt-4 mb-2 text-gray-800 dark:text-gray-200">
            {$i18n.t('2.1. Personal Information')}
        </h3>
        <ul class="list-disc pl-6 text-gray-700 dark:text-gray-300">
            <li>{$i18n.t('Account information: Name, email address, password, and profile picture')}</li>
            <li>{$i18n.t('Role information: Student, teacher, or parent status')}</li>
            <li>{$i18n.t('Login credentials and authentication data')}</li>
        </ul>
        
        <h3 class="text-lg font-medium mt-4 mb-2 text-gray-800 dark:text-gray-200">
            {$i18n.t('2.2. Usage Information')}
        </h3>
        <ul class="list-disc pl-6 text-gray-700 dark:text-gray-300">
            <li>{$i18n.t('Learning activities and progress')}</li>
            <li>{$i18n.t('Interactions with AI tutors and educational content')}</li>
            <li>{$i18n.t('Time spent on different learning modules')}</li>
        </ul>
        
        <h3 class="text-lg font-medium mt-4 mb-2 text-gray-800 dark:text-gray-200">
            {$i18n.t('2.3. Technical Information')}
        </h3>
        <ul class="list-disc pl-6 text-gray-700 dark:text-gray-300">
            <li>{$i18n.t('Device information: IP address, browser type, operating system')}</li>
            <li>{$i18n.t('Cookies and similar technologies')}</li>
            <li>{$i18n.t('Log data and analytics information')}</li>
        </ul>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('3. How We Use Your Information')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('We use collected information for the following purposes:')}
        </p>
        <ul class="list-disc pl-6 text-gray-700 dark:text-gray-300">
            <li>{$i18n.t('To provide and maintain our educational Platform')}</li>
            <li>{$i18n.t('To personalize learning experiences through AI')}</li>
            <li>{$i18n.t('To analyze usage patterns and improve our Platform')}</li>
            <li>{$i18n.t('To communicate with you about your account or Platform updates')}</li>
            <li>{$i18n.t('To provide support and respond to inquiries')}</li>
            <li>{$i18n.t('To comply with legal obligations')}</li>
        </ul>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('4. Sharing Your Information')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('We may share your information with:')}
        </p>
        <ul class="list-disc pl-6 text-gray-700 dark:text-gray-300">
            <li>{$i18n.t('Teachers and educational institutions (for student users)')}</li>
            <li>{$i18n.t('Parents or guardians (for minor students)')}</li>
            <li>{$i18n.t('Service providers who help us operate our Platform')}</li>
            <li>{$i18n.t('Law enforcement or regulatory authorities when required by law')}</li>
        </ul>
        <p class="text-gray-700 dark:text-gray-300 mt-3">
            {$i18n.t('We do not sell your personal information to third parties.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('5. Data Security')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('We implement appropriate technical and organizational measures to protect your information against unauthorized access, alteration, disclosure, or destruction. However, no method of transmission over the Internet or electronic storage is 100% secure.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('6. Data Retention')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('We retain your information for as long as your account is active or as needed to provide services. We may retain certain information for legitimate business purposes or as required by law.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('7. Children\'s Privacy')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('Our Platform may be used by children with appropriate supervision. Parents/guardians of users under 16 have the right to review and request deletion of their child\'s information.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('8. AI Data Processing')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('Our Platform uses artificial intelligence to provide personalized educational experiences. We may process user interactions, responses, and learning patterns to improve our AI systems. This data is used in an aggregated and anonymized form whenever possible.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('9. Your Privacy Rights')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('Depending on your location, you may have the right to:')}
        </p>
        <ul class="list-disc pl-6 text-gray-700 dark:text-gray-300">
            <li>{$i18n.t('Access your personal information')}</li>
            <li>{$i18n.t('Correct inaccurate information')}</li>
            <li>{$i18n.t('Delete your personal information')}</li>
            <li>{$i18n.t('Object to or restrict the processing of your information')}</li>
            <li>{$i18n.t('Data portability')}</li>
        </ul>
        <p class="text-gray-700 dark:text-gray-300 mt-3">
            {$i18n.t('To exercise these rights, please contact us using the information provided at the end of this policy.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('10. Cookies and Tracking Technologies')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('We use cookies and similar tracking technologies to enhance your experience on our Platform. You can control cookie settings through your browser preferences.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('11. Changes to This Privacy Policy')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('We may update this Privacy Policy periodically. We will notify you of any significant changes by posting a notice on our Platform or sending you an email.')}
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-3 text-gray-800 dark:text-gray-200">
            {$i18n.t('12. Contact Us')}
        </h2>
        <p class="text-gray-700 dark:text-gray-300">
            {$i18n.t('If you have questions about this Privacy Policy, please contact us at:')}
        </p>
        <p class="text-gray-700 dark:text-gray-300">
            Email: contact@opentutorai.com<br>
        </p>
    </div>
</Modal> 