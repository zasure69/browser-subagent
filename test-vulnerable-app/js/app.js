/**
 * SecureNotes Pro — Main Application Bootstrap
 * 
 * Initializes all modules and starts the application.
 */

'use strict';

// ── Application Startup ──────────────────────────────────────
(function init() {
    console.log(`[SecureNotes] v${APP_CONFIG.version} starting...`);

    // 1. Initialize session & localStorage
    initSession();

    // 2. Apply URL config overrides (prototype pollution vector)
    applyConfigOverrides();

    // 3. Seed demo data
    seedDemoNotes();

    // 4. Load UI components
    loadProfile();
    renderNotes();
    renderActivityFeed();

    // 5. Process URL hash (XSS / script injection vector)
    processHash();

    // 6. Log startup complete
    debugLog('SecureNotes Pro v' + APP_CONFIG.version + ' initialized');
    debugLog('Loaded ' + (JSON.parse(localStorage.getItem('notes') || '[]')).length + ' notes');
    debugLog('API endpoint: ' + APP_CONFIG.apiEndpoint);

    console.log('[SecureNotes] App ready. Config:', APP_CONFIG);
    console.log('[SecureNotes] Session token:', localStorage.getItem('session_token'));
    console.log('[SecureNotes] Refresh token:', localStorage.getItem('refresh_token'));
})();
