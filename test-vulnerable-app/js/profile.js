/**
 * SecureNotes Pro — Profile Module
 * 
 * Handles user profile display and settings.
 * Supports profile data loading via URL parameters.
 */

'use strict';

// ── Load Profile ──────────────────────────────────────────────
// VULNERABILITY: Profile data from URL param (base64 JSON) rendered via innerHTML
// Payload: ?profile=BASE64_ENCODED_JSON_WITH_XSS
function loadProfile() {
    const params = new URLSearchParams(window.location.search);
    const profileData = params.get('profile');
    const userName = params.get('user') || 'Admin';

    // Update navbar greeting
    const greetingEl = document.getElementById('user-greeting');
    const avatarEl = document.getElementById('user-avatar');

    if (greetingEl) greetingEl.textContent = `Welcome, ${userName}`;
    if (avatarEl) avatarEl.textContent = userName.charAt(0).toUpperCase();

    const profileContent = document.getElementById('profile-content');
    if (!profileContent) return;

    if (profileData) {
        try {
            // VULNERABLE: Decodes base64, parses JSON, renders fields via innerHTML
            // No sanitization of profile fields (name, email, bio, website)
            const profile = JSON.parse(atob(profileData));

            debugLog('Profile loaded from URL parameter');

            // VULNERABLE: All fields rendered with innerHTML — XSS in any field
            profileContent.innerHTML = `
                <div style="display:grid; gap:8px;">
                    <div><strong>Name:</strong> ${profile.name || 'N/A'}</div>
                    <div><strong>Email:</strong> ${profile.email || 'N/A'}</div>
                    <div><strong>Bio:</strong> ${profile.bio || 'No bio set'}</div>
                    ${profile.website ?
                    `<div><strong>Website:</strong> <a href="${profile.website}" target="_blank">${profile.website}</a></div>`
                    : ''}
                    ${profile.avatar ?
                    `<div><strong>Avatar:</strong> <img src="${profile.avatar}" style="width:48px;height:48px;border-radius:50%;"></div>`
                    : ''}
                </div>
            `;

            // VULNERABLE: Profile name used in page title without encoding
            if (profile.name) {
                document.title = `${profile.name}'s Notes — SecureNotes Pro`;
            }

        } catch (e) {
            profileContent.innerHTML = `
                <div style="color:#ef4444;">
                    ❌ Error loading profile: ${e.message}
                </div>
            `;
            debugLog('Profile parse error: ' + e.message);
        }
    } else {
        // Default profile
        profileContent.innerHTML = `
            <div style="display:grid; gap:8px;">
                <div><strong>Name:</strong> Admin User</div>
                <div><strong>Email:</strong> admin@securenotes.pro</div>
                <div><strong>Role:</strong> Administrator</div>
                <div><strong>Plan:</strong> Pro ⭐</div>
                <div><strong>Member Since:</strong> January 2024</div>
            </div>
            <div style="margin-top:12px;">
                <button class="btn-save" onclick="exportProfile()" style="font-size:12px; padding:6px 12px;">
                    📥 Export Profile Data
                </button>
            </div>
        `;
    }
}


// ── Export Profile ─────────────────────────────────────────────
// VULNERABILITY: Exports ALL localStorage data including secrets
function exportProfile() {
    const data = {};
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        data[key] = localStorage.getItem(key);
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'securenotes_profile_export.json';
    a.click();
    URL.revokeObjectURL(url);

    debugLog('Profile data exported (includes all localStorage)');
    showNotification('Profile exported', 'success');
}
