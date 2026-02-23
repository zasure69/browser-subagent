/**
 * SecureNotes Pro — Notes CRUD Module
 * 
 * Manages note creation, reading, updating, and deletion.
 * Notes are persisted in localStorage.
 */

'use strict';

// ── Toggle Note Form ──────────────────────────────────────────
function toggleNoteForm() {
    const form = document.getElementById('note-form');
    const isVisible = form.style.display === 'block';
    form.style.display = isVisible ? 'none' : 'block';

    if (!isVisible) {
        document.getElementById('note-title').focus();
    }
}


// ── Save Note ─────────────────────────────────────────────────
function saveNote() {
    const titleInput = document.getElementById('note-title');
    const contentInput = document.getElementById('note-content');
    const title = titleInput.value.trim();
    const content = contentInput.value.trim();

    if (!title || !content) {
        showNotification('Title and content are required', 'error');
        return;
    }

    const notes = JSON.parse(localStorage.getItem('notes') || '[]');

    const newNote = {
        id: 'note-' + Date.now(),
        title: title,
        content: renderMarkdown(content),  // Renders markdown → HTML (unsanitized)
        rawContent: content,
        date: new Date().toISOString(),
        author: localStorage.getItem('user_email') || 'anonymous',
        tags: extractTags(content),
    };

    notes.unshift(newNote);
    localStorage.setItem('notes', JSON.stringify(notes));

    titleInput.value = '';
    contentInput.value = '';
    toggleNoteForm();
    renderNotes();

    debugLog('Note saved: ' + title);
    showNotification('Note saved successfully', 'success');
}


// ── Delete Note ───────────────────────────────────────────────
function deleteNote(index) {
    const notes = JSON.parse(localStorage.getItem('notes') || '[]');
    const deleted = notes.splice(index, 1);
    localStorage.setItem('notes', JSON.stringify(notes));
    renderNotes();

    if (deleted[0]) {
        debugLog('Note deleted: ' + deleted[0].title);
    }
}


// ── Render Notes ──────────────────────────────────────────────
// VULNERABILITY: DOM Clobbering + Stored XSS
// Note content is rendered with innerHTML without sanitization.
// If a note contains HTML with id/name attributes, it can clobber
// existing DOM elements and global variables.
function renderNotes() {
    const notes = JSON.parse(localStorage.getItem('notes') || '[]');
    const list = document.getElementById('notes-list');

    if (!list) return;

    if (notes.length === 0) {
        list.innerHTML = `
            <div style="text-align:center; padding:40px; color:#475569;">
                <p style="font-size:48px; margin-bottom:12px;">📒</p>
                <p>No notes yet. Click "+ New Note" to get started!</p>
            </div>`;
        return;
    }

    // VULNERABLE: All note fields rendered via innerHTML
    // Title and content can contain arbitrary HTML → Stored XSS
    // Content can include elements with id="" to clobber DOM globals
    list.innerHTML = notes.map((note, i) => `
        <div class="note-card" id="${note.id}">
            <h3>${note.title}</h3>
            <div class="note-body">${note.content}</div>
            <div class="note-meta">
                <span>${formatDate(note.date)} • ${note.author || 'Unknown'}</span>
                <span>
                    <button class="share-btn" onclick="shareNote(${i})">📤 Share</button>
                    <button class="delete-btn" onclick="deleteNote(${i})">🗑️ Delete</button>
                </span>
            </div>
        </div>
    `).join('');
}


// ── Extract Tags ──────────────────────────────────────────────
function extractTags(content) {
    const tagRegex = /#(\w+)/g;
    const tags = [];
    let match;
    while ((match = tagRegex.exec(content)) !== null) {
        tags.push(match[1]);
    }
    return tags;
}


// ── Seed Demo Notes ───────────────────────────────────────────
function seedDemoNotes() {
    if (localStorage.getItem('notes_seeded')) return;

    const demoNotes = [
        {
            id: 'note-demo-1',
            title: 'Bug Bounty Checklist',
            content: 'Remember to check: <strong>XSS</strong>, CSRF, IDOR, SSRF, SQL Injection, Open Redirects, and business logic flaws. Always test with different authorization levels.',
            date: '2026-02-19T10:30:00Z',
            author: 'admin@securenotes.pro'
        },
        {
            id: 'note-demo-2',
            title: 'API Endpoints to Review',
            content: `<strong>Internal endpoints:</strong><br>
                      • <code>/api/v2/users</code> — User management<br>
                      • <code>/api/v2/admin/config</code> — Server config (needs auth)<br>
                      • <code>/api/v2/debug/logs</code> — Debug logs<br>
                      • <code>/api/v2/export?format=csv&amp;include=passwords</code> — Data export`,
            date: '2026-02-18T14:20:00Z',
            author: 'admin@securenotes.pro'
        },
        {
            id: 'note-demo-3',
            title: 'Server Credentials (TEMP)',
            content: `<em>Staging server:</em> ssh admin@staging.securenotes.pro<br>
                      Password: <code>Pr0d_St4g1ng_2026!</code><br>
                      DB: <code>postgresql://dbadmin:s3cur3_db_p4ss@db.internal:5432/notes</code><br>
                      <br><em>⚠️ TODO: Move these to vault</em>`,
            date: '2026-02-17T09:15:00Z',
            author: 'admin@securenotes.pro'
        },
        {
            id: 'note-demo-4',
            title: 'Client Meeting Notes',
            content: 'Discussed Q1 roadmap. Priority features: real-time collaboration, E2E encryption, <strong>SSO integration</strong>. Budget approved for 3 new engineers.',
            date: '2026-02-16T11:00:00Z',
            author: 'admin@securenotes.pro'
        }
    ];

    localStorage.setItem('notes', JSON.stringify(demoNotes));
    localStorage.setItem('notes_seeded', 'true');
    debugLog('Demo notes seeded');
}
