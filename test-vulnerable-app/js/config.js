/**
 * SecureNotes Pro — Application Configuration
 * Version: 3.2.1
 * 
 * IMPORTANT: This configuration module handles app initialization,
 * environment detection, and feature flags.
 */

'use strict';

// ── Application Configuration ─────────────────────────────────
const APP_CONFIG = {
    appName: 'SecureNotes Pro',
    version: '3.2.1',
    apiEndpoint: 'https://api.securenotes.pro/v2',
    cdnBase: 'https://cdn.securenotes.pro',

    // Authentication
    apiKey: 'sk-prod-7f3a2b1c9d8e4f5a6b7c8d9e0f1a2b3c',
    adminToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYWRtaW4iLCJ1c2VyIjoiYWRtaW5Ac2VjdXJlbm90ZXMucHJvIiwiaWF0IjoxNzA5MDAwMDAwfQ.fake_jwt_signature_here',

    // Feature flags
    features: {
        sharing: true,
        markdown: true,
        collaboration: false,
        debugConsole: false,
        analytics: true,
    },

    // Internal endpoints (should not be exposed)
    internal: {
        healthCheck: '/api/internal/health',
        adminPanel: '/api/internal/admin',
        dbExport: '/api/internal/export?format=json&include=all',
        logDrain: '/api/internal/logs?level=debug',
    }
};


// ── Session Management ────────────────────────────────────────
// VULNERABILITY: Sensitive data stored client-side without encryption
function initSession() {
    if (!localStorage.getItem('session_token')) {
        localStorage.setItem('session_token', 'sess_' + generateId(24));
    }
    localStorage.setItem('user_email', 'admin@securenotes.pro');
    localStorage.setItem('user_role', 'administrator');
    localStorage.setItem('api_key', APP_CONFIG.apiKey);
    localStorage.setItem('refresh_token', 'rt_' + Date.now() + '_xK9mP2qR5tW8vY1');
    localStorage.setItem('last_login', new Date().toISOString());

    // Log session info to console
    console.log('[SecureNotes] Session initialized:', {
        token: localStorage.getItem('session_token'),
        email: localStorage.getItem('user_email'),
        role: localStorage.getItem('user_role'),
    });
    console.log('[SecureNotes] API Key:', APP_CONFIG.apiKey);
    console.log('[SecureNotes] Admin JWT:', APP_CONFIG.adminToken);
}


// ── URL Parameter Config Override ─────────────────────────────
// VULNERABILITY: Prototype Pollution via URL parameters
// Merges query params into config using dot notation (e.g., ?__proto__.polluted=true)
function parseUrlConfig() {
    const params = new URLSearchParams(window.location.search);
    const overrides = {};

    for (const [key, value] of params.entries()) {
        const keys = key.split('.');
        let obj = overrides;

        for (let i = 0; i < keys.length - 1; i++) {
            const k = keys[i];
            if (!(k in obj)) {
                obj[k] = {};
            }
            obj = obj[k];
        }

        // Dangerous: allows __proto__ pollution
        // Example: ?__proto__.isAdmin=true  or  ?constructor.prototype.isAdmin=true
        try {
            obj[keys[keys.length - 1]] = JSON.parse(value);
        } catch {
            obj[keys[keys.length - 1]] = value;
        }
    }

    return overrides;
}


// ── Apply URL overrides ───────────────────────────────────────
function applyConfigOverrides() {
    const overrides = parseUrlConfig();

    // Deep merge (vulnerable to prototype pollution)
    function deepMerge(target, source) {
        for (const key in source) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                if (!target[key]) target[key] = {};
                deepMerge(target[key], source[key]);
            } else {
                target[key] = source[key];
            }
        }
    }

    deepMerge(APP_CONFIG, overrides);

    // Check debug mode (can be enabled via prototype pollution)
    if (APP_CONFIG.features.debugConsole || ({}).isDebug) {
        const debugEl = document.getElementById('debug-console');
        if (debugEl) debugEl.style.display = 'block';
        console.log('[SecureNotes] Debug mode ENABLED');
    }
}


function generateId(length) {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}
