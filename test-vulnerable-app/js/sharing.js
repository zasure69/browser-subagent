/**
 * SecureNotes Pro — Sharing Module
 * 
 * Handles note sharing functionality including
 * URL generation and recipient validation.
 */

'use strict';

// ── Share Note ────────────────────────────────────────────────
function shareNote(index) {
    const modal = document.getElementById('share-modal');
    if (modal) {
        modal.style.display = 'flex';
        modal.dataset.noteIndex = index;
    }
}


// ── Close Share Modal ─────────────────────────────────────────
function closeShareModal() {
    const modal = document.getElementById('share-modal');
    if (modal) {
        modal.style.display = 'none';
        document.getElementById('share-url').value = '';
        document.getElementById('share-preview').innerHTML = 'Preview will appear here...';
    }
}


// ── Process Share ─────────────────────────────────────────────
// VULNERABILITY: Open Redirect — weak URL validation
// Only checks if URL *contains* the string 'securenotes' anywhere
// Bypass examples:
//   - https://evil.com/?redirect=securenotes.pro
//   - https://evil.com/securenotes/
//   - https://securenotes.evil.com/phish
//   - javascript:alert('securenotes')//
function processShare() {
    const shareUrl = document.getElementById('share-url').value.trim();
    const preview = document.getElementById('share-preview');
    const noteIndex = document.getElementById('share-modal').dataset.noteIndex;

    if (!shareUrl) {
        preview.innerHTML = '⚠️ Please enter a URL';
        return;
    }

    debugLog('Share URL submitted: ' + shareUrl);

    // VULNERABLE: Insufficient URL validation
    // Only checks substring match, not actual domain
    if (shareUrl.includes('securenotes')) {
        const notes = JSON.parse(localStorage.getItem('notes') || '[]');
        const note = notes[noteIndex];

        if (note) {
            // VULNERABLE: URL rendered in innerHTML with <a href="">
            // If shareUrl contains javascript: scheme, href is directly injectable
            preview.innerHTML = `
                ✅ Sharing "<strong>${note.title}</strong>" to:<br>
                <a href="${shareUrl}" style="color:#818cf8; word-break:break-all;">${shareUrl}</a>
                <br><br>
                <small style="color:#475569;">
                    📤 Share data will include note content and your profile info.
                    <br>Auto-redirecting in 3 seconds...
                </small>
            `;

            // VULNERABLE: Open redirect — navigates to attacker-controlled URL
            setTimeout(() => {
                debugLog('Redirecting to share target: ' + shareUrl);
                window.location.href = shareUrl;
            }, 3000);

        } else {
            preview.innerHTML = '❌ Note not found';
        }
    } else {
        preview.innerHTML = `
            ❌ Invalid URL. Must be a SecureNotes profile URL.<br>
            <small style="color:#64748b;">URL must contain "securenotes" domain.</small>
        `;
    }
}


// ── Generate Share Link ───────────────────────────────────────
// VULNERABILITY: Includes sensitive note content in URL without access control
function generateShareLink(noteIndex) {
    const notes = JSON.parse(localStorage.getItem('notes') || '[]');
    const note = notes[noteIndex];

    if (!note) return null;

    // Encodes full note content into the URL
    const shareData = btoa(JSON.stringify({
        title: note.title,
        content: note.content,
        author: note.author,
        sharedBy: localStorage.getItem('user_email'),
        sharedAt: new Date().toISOString(),
        sessionToken: localStorage.getItem('session_token'), // LEAKED!
    }));

    return `${window.location.origin}?shared=${shareData}`;
}
