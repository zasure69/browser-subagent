/**
 * SecureNotes Pro — Activity Feed Module
 * 
 * Displays recent user activity and audit log.
 * Loads activity data from URL parameter for cross-device sync.
 */

'use strict';

// ── Render Activity Feed ──────────────────────────────────────
function renderActivityFeed() {
    const feedEl = document.getElementById('activity-feed');
    if (!feedEl) return;

    // Check for activity data from URL (VULNERABLE: rendered via innerHTML)
    const params = new URLSearchParams(window.location.search);
    const activityParam = params.get('activity');

    if (activityParam) {
        try {
            // VULNERABILITY: Decodes and renders external activity data without sanitization
            const activities = JSON.parse(atob(activityParam));
            feedEl.innerHTML = activities.map(a => `
                <div class="activity-item">
                    <div class="activity-icon ${a.type}">${a.icon || '📌'}</div>
                    <div>
                        <strong>${a.user}</strong> ${a.action}
                        <div style="font-size:12px; color:#475569;">${a.time}</div>
                    </div>
                </div>
            `).join('');
            return;
        } catch (e) {
            debugLog('Activity parse error: ' + e.message);
        }
    }

    // Default activity feed
    const activities = [
        { icon: '✏️', type: 'edit', user: 'Admin', action: 'edited "Bug Bounty Checklist"', time: '2 hours ago' },
        { icon: '🔑', type: 'login', user: 'Admin', action: 'logged in from 192.168.1.105', time: '3 hours ago' },
        { icon: '📤', type: 'share', user: 'Admin', action: 'shared "API Endpoints to Review"', time: 'Yesterday' },
        { icon: '🗑️', type: 'delete', user: 'Admin', action: 'deleted "Old Draft Notes"', time: '2 days ago' },
        { icon: '🔑', type: 'login', user: 'Admin', action: 'logged in from 10.0.0.42', time: '3 days ago' },
    ];

    feedEl.innerHTML = activities.map(a => `
        <div class="activity-item">
            <div class="activity-icon ${a.type}">${a.icon}</div>
            <div>
                <strong>${a.user}</strong> ${a.action}
                <div style="font-size:12px; color:#475569;">${a.time}</div>
            </div>
        </div>
    `).join('');
}
