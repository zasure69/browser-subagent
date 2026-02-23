/**
 * SecureNotes Pro — Utility Functions
 * 
 * Shared helpers for DOM manipulation, formatting,
 * and inter-component communication.
 */

'use strict';

// ── Debug Logger ──────────────────────────────────────────────
function debugLog(msg) {
    const debugConsole = document.getElementById('debug-console');
    if (debugConsole) {
        const time = new Date().toLocaleTimeString();
        debugConsole.innerHTML += `<span style="color:#64748b">[${time}]</span> ${msg}\n`;
        debugConsole.scrollTop = debugConsole.scrollHeight;
    }
}


// ── Date Formatting ───────────────────────────────────────────
function formatDate(isoDate) {
    try {
        return new Date(isoDate).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return 'Unknown date';
    }
}


// ── Safe Text Escaping (but not always used!) ─────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


// ── Markdown-like Rendering ───────────────────────────────────
// NOTE: This is intentionally simplified and DOES NOT sanitize HTML
function renderMarkdown(text) {
    if (!text) return '';

    // Bold
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Code
    text = text.replace(/`(.*?)`/g, '<code style="background:#334155;padding:2px 6px;border-radius:3px;">$1</code>');
    // Line breaks
    text = text.replace(/\n/g, '<br>');

    return text;
}


// ── PostMessage Communication Layer ───────────────────────────
// VULNERABILITY: No origin validation on incoming messages
// Accepts and processes messages from ANY origin/window
window.addEventListener('message', function (event) {
    // WARNING: No event.origin check!
    debugLog('postMessage received from: ' + event.origin);
    debugLog('Data: ' + JSON.stringify(event.data));

    const data = event.data;
    if (!data || !data.action) return;

    switch (data.action) {
        case 'updateProfile':
            // VULNERABLE: Renders arbitrary HTML from external message
            const profileEl = document.getElementById('profile-content');
            if (profileEl) {
                profileEl.innerHTML = data.html;
            }
            break;

        case 'addNote':
            // VULNERABLE: Adds note with unsanitized content from external source
            const notes = JSON.parse(localStorage.getItem('notes') || '[]');
            notes.push({
                id: 'note-ext-' + Date.now(),
                title: data.title,
                content: data.content,
                date: new Date().toISOString(),
                author: data.author || 'external',
                source: 'postMessage'
            });
            localStorage.setItem('notes', JSON.stringify(notes));
            if (typeof renderNotes === 'function') renderNotes();
            break;

        case 'getConfig':
            // VULNERABLE: Leaks full config (including API keys) to any requesting origin
            event.source.postMessage({
                action: 'configResponse',
                config: APP_CONFIG,
                session: {
                    token: localStorage.getItem('session_token'),
                    email: localStorage.getItem('user_email'),
                    apiKey: localStorage.getItem('api_key'),
                }
            }, '*');  // Sending to ANY origin!
            break;

        case 'eval':
            // VULNERABILITY: Arbitrary code execution via postMessage
            try {
                const result = eval(data.code);
                event.source.postMessage({
                    action: 'evalResult',
                    result: String(result)
                }, '*');
            } catch (e) {
                event.source.postMessage({
                    action: 'evalError',
                    error: e.message
                }, '*');
            }
            break;

        case 'navigate':
            // VULNERABLE: Allows any origin to redirect the page
            if (data.url) {
                window.location.href = data.url;
            }
            break;

        default:
            debugLog('Unknown postMessage action: ' + data.action);
    }
});


// ── Notification Helper ───────────────────────────────────────
function showNotification(message, type) {
    // Simple console notification
    const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️';
    debugLog(`${prefix} ${message}`);
}
