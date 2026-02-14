// Session and Term Management JavaScript

// Toast Notification Utility (shared)
function showToast(title, message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    toast.innerHTML = `
        <i class="fas ${iconMap[type]} toast-icon"></i>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            ${message ? `<div class="toast-message">${message}</div>` : ''}
        </div>
        <i class="fas fa-times toast-close"></i>
    `;

    container.appendChild(toast);

    toast.querySelector('.toast-close').onclick = () => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    };

    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// Form Validation
function validateSessionForm(data) {
    const errors = [];

    // Session name format validation (YYYY/YYYY)
    const sessionNameRegex = /^\d{4}\/\d{4}$/;
    if (!sessionNameRegex.test(data.name)) {
        errors.push('Session name must be in format YYYY/YYYY (e.g., 2024/2025)');
    }

    // Date validation
    const startDate = new Date(data.start_date);
    const endDate = new Date(data.end_date);
    const resumptionDate = new Date(data.resumption_date);
    const vacationDate = new Date(data.vacation_date);

    if (endDate <= startDate) {
        errors.push('Session end date must be after start date');
    }

    if (vacationDate <= resumptionDate) {
        errors.push('Vacation date must be after resumption date');
    }

    // Term dates should be within session dates
    if (resumptionDate < startDate || resumptionDate > endDate) {
        errors.push('Term resumption date must be within session dates');
    }

    if (vacationDate < startDate || vacationDate > endDate) {
        errors.push('Term vacation date must be within session dates');
    }

    return errors;
}

function validateTermForm(data) {
    const errors = [];

    const resumptionDate = new Date(data.resumption_date);
    const vacationDate = new Date(data.vacation_date);

    if (vacationDate <= resumptionDate) {
        errors.push('Vacation date must be after resumption date');
    }

    return errors;
}

// Add session card dynamically
function addSessionCard(sessionName, sessionId) {
    const sessionList = document.getElementById('session-list');
    const noData = sessionList.querySelector('.no-data-msg');
    if (noData) noData.remove();

    const card = document.createElement('div');
    card.className = 'session-card';
    card.dataset.sessionId = sessionId;
    card.dataset.sessionName = sessionName;
    card.innerHTML = `
        <div class="session-info">
            <span class="session-name">${sessionName}</span>
        </div>
        <i class="fas fa-chevron-right"></i>
    `;

    sessionList.insertBefore(card, sessionList.firstChild);

    // Highlight new card
    card.style.background = 'rgba(46, 204, 113, 0.1)';
    setTimeout(() => {
        card.style.background = '';
    }, 2000);

    // Attach click handler
    card.onclick = () => loadSessionDetails(card);
}

document.addEventListener('DOMContentLoaded', function () {
    const sessionModal = document.getElementById('session-modal');
    const termModal = document.getElementById('term-modal');
    const addSessionBtn = document.getElementById('add-session-btn');
    const addTermBtn = document.getElementById('add-term-btn');
    const closeBtns = document.querySelectorAll('.close-modal');
    const sessionCards = document.querySelectorAll('.session-card');
    const termList = document.getElementById('term-list');
    const termSection = document.getElementById('term-section');
    const sessionTitle = document.getElementById('selected-session-title');

    let currentSessionId = null;

    // Modal Control
    if (addSessionBtn) {
        addSessionBtn.onclick = () => {
            document.getElementById('add-session-form').reset();
            document.getElementById('form-errors').style.display = 'none';
            sessionModal.style.display = 'block';
        };
    }

    if (addTermBtn) {
        addTermBtn.onclick = () => {
            document.getElementById('modal-session-id').value = currentSessionId;
            termModal.style.display = 'block';
        };
    }

    closeBtns.forEach(btn => {
        btn.onclick = () => {
            sessionModal.style.display = 'none';
            termModal.style.display = 'none';
        };
    });

    window.onclick = (event) => {
        if (event.target == sessionModal) sessionModal.style.display = 'none';
        if (event.target == termModal) termModal.style.display = 'none';
    };

    // Load Session Details
    function loadSessionDetails(card) {
        sessionCards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');

        const sessionId = card.dataset.sessionId;
        const sessionName = card.dataset.sessionName;
        currentSessionId = sessionId;

        sessionTitle.textContent = `Terms for ${sessionName}`;
        termSection.style.display = 'block';

        loadTerms(sessionId);
    }

    sessionCards.forEach(card => {
        card.onclick = () => loadSessionDetails(card);
    });

    async function loadTerms(sessionId) {
        termList.innerHTML = '<div class="no-data-msg">Loading terms...</div>';

        try {
            const response = await fetch(`/sessions/details/${sessionId}`);
            const data = await response.json();

            termList.innerHTML = '';

            if (data.terms.length === 0) {
                termList.innerHTML = '<div class="no-data-msg">No terms created for this session.</div>';
            } else {
                data.terms.forEach(term => {
                    const isActive = (data.active_session_id == sessionId && data.active_term_id == term.id);
                    const termName = term.term_number == 1 ? "1st Term" : (term.term_number == 2 ? "2nd Term" : "3rd Term");

                    const card = document.createElement('div');
                    card.className = `term-card ${isActive ? 'is-active' : ''}`;
                    card.innerHTML = `
                        <div class="term-info">
                            <h3>${termName}</h3>
                            <div class="term-dates">
                                <i class="fas fa-calendar-alt"></i>
                                ${term.resumption_date || 'N/A'} — ${term.vacation_date || 'N/A'}
                            </div>
                        </div>
                        <div class="term-actions">
                            ${isActive ?
                            '<span class="active-badge">Current Active</span>' :
                            `<button class="btn btn-light btn-sm set-active-btn" data-term-id="${term.id}">Set as Active</button>`
                        }
                        </div>
                    `;
                    termList.appendChild(card);
                });

                // Set Active Event
                document.querySelectorAll('.set-active-btn').forEach(btn => {
                    btn.onclick = async () => {
                        const termId = btn.dataset.termId;
                        btn.classList.add('btn-loading');
                        btn.disabled = true;

                        try {
                            const res = await fetch('/sessions/set_active', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ session_id: sessionId, term_id: termId })
                            });
                            const result = await res.json();

                            btn.classList.remove('btn-loading');
                            btn.disabled = false;

                            if (result.success) {
                                showToast('Success', 'Active session and term updated', 'success');
                                loadTerms(sessionId);
                            } else {
                                showToast('Error', result.message, 'error');
                            }
                        } catch (error) {
                            btn.classList.remove('btn-loading');
                            btn.disabled = false;
                            showToast('Error', 'Failed to update active term', 'error');
                        }
                    };
                });
            }

            // Hide Add Term button if 3 terms already exist
            if (addTermBtn) {
                addTermBtn.style.display = data.terms.length >= 3 ? 'none' : 'block';
            }

        } catch (error) {
            termList.innerHTML = `<div class="no-data-msg">Error loading terms: ${error.message}</div>`;
        }
    }

    // Session Form Submission
    document.getElementById('add-session-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        const submitBtn = e.target.querySelector('button[type="submit"]');
        const errorDiv = document.getElementById('form-errors');

        // Validate form
        const validationErrors = validateSessionForm(data);
        if (validationErrors.length > 0) {
            errorDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + validationErrors.join('<br>');
            errorDiv.style.display = 'block';
            validationErrors.forEach(err => showToast('Validation Error', err, 'error'));
            return;
        }

        errorDiv.style.display = 'none';
        submitBtn.classList.add('btn-loading');
        submitBtn.disabled = true;

        try {
            const res = await fetch('/sessions/add_academic_period', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await res.json();

            submitBtn.classList.remove('btn-loading');
            submitBtn.disabled = false;

            if (result.success) {
                sessionModal.style.display = 'none';
                e.target.reset();
                showToast('Success', 'Academic period created successfully', 'success');

                // Add session card dynamically
                if (result.session && result.session.id) {
                    addSessionCard(result.session.name, result.session.id);
                } else {
                    // Fallback to reload
                    setTimeout(() => location.reload(), 1000);
                }
            } else {
                showToast('Error', result.message || 'Failed to create academic period', 'error');
            }
        } catch (error) {
            submitBtn.classList.remove('btn-loading');
            submitBtn.disabled = false;
            showToast('Error', 'Network error: ' + error.message, 'error');
        }
    };

    // Term Form Submission
    document.getElementById('add-term-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        const submitBtn = e.target.querySelector('button[type="submit"]');

        // Validate form
        const validationErrors = validateTermForm(data);
        if (validationErrors.length > 0) {
            validationErrors.forEach(err => showToast('Validation Error', err, 'error'));
            return;
        }

        submitBtn.classList.add('btn-loading');
        submitBtn.disabled = true;

        try {
            const res = await fetch('/sessions/terms/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await res.json();

            submitBtn.classList.remove('btn-loading');
            submitBtn.disabled = false;

            if (result.success) {
                termModal.style.display = 'none';
                e.target.reset();
                showToast('Success', 'Term added successfully', 'success');
                loadTerms(currentSessionId);
            } else {
                showToast('Error', result.message || 'Failed to add term', 'error');
            }
        } catch (error) {
            submitBtn.classList.remove('btn-loading');
            submitBtn.disabled = false;
            showToast('Error', 'Network error: ' + error.message, 'error');
        }
    };
});
