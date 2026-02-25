document.addEventListener('DOMContentLoaded', () => {
    const sessionSelect = document.getElementById('session-select');
    const termSelect = document.getElementById('term-select');
    const classSelect = document.getElementById('class-select');
    const tbody = document.getElementById('attendance-tbody');
    const saveBtn = document.getElementById('save-btn');
    const headerSaveBtn = document.getElementById('header-save-btn');

    let currentAttendanceData = [];

    // Load matching terms when session changes
    sessionSelect.addEventListener('change', async (e) => {
        const sessionId = e.target.value;
        termSelect.innerHTML = '<option value="">Select Term</option>';

        if (sessionId) {
            try {
                const response = await fetch(`/attendance/api/terms/${sessionId}`);
                const terms = await response.json();

                terms.forEach(term => {
                    const option = document.createElement('option');
                    option.value = term.id;
                    option.textContent = `Term ${term.term_number}`;
                    termSelect.appendChild(option);
                });

                // Try to set current term if available from settings
                if (window.appConfig && window.appConfig.currentTermId) {
                    termSelect.value = window.appConfig.currentTermId;
                }
            } catch (error) {
                console.error("Error fetching terms:", error);
                showToast('Failed to load terms', 'error');
            }
        }
        loadAttendanceData();
    });

    termSelect.addEventListener('change', loadAttendanceData);
    classSelect.addEventListener('change', loadAttendanceData);

    async function loadAttendanceData() {
        const sessionId = sessionSelect.value;
        const termId = termSelect.value;
        const classId = classSelect.value;

        if (!sessionId || !termId || !classId) {
            tbody.innerHTML = '<tr><td colspan="4" class="no-data">Select session, term, and class to manage attendance</td></tr>';
            return;
        }

        tbody.innerHTML = '<tr><td colspan="4" class="no-data"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>';

        try {
            const url = `/attendance/api/class_attendance?class_id=${classId}&session_id=${sessionId}&term_id=${termId}`;
            const response = await fetch(url);
            currentAttendanceData = await response.json();

            renderAttendanceGrid();
        } catch (error) {
            console.error("Error loading attendance:", error);
            showToast('Failed to load attendance data', 'error');
            tbody.innerHTML = '<tr><td colspan="4" class="no-data text-danger">Error loading data. Try again.</td></tr>';
        }
    }

    function renderAttendanceGrid() {
        if (!currentAttendanceData || currentAttendanceData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="no-data">No students found in this class</td></tr>';
            return;
        }

        tbody.innerHTML = '';

        currentAttendanceData.forEach((student, index) => {
            const tr = document.createElement('tr');

            tr.innerHTML = `
                <td>${student.reg_number}</td>
                <td><strong>${student.full_name}</strong></td>
                <td>
                    <input type="number" 
                           class="score-input present-input" 
                           data-index="${index}" 
                           min="0" 
                           value="${student.times_present || 0}">
                </td>
                <td>
                    <input type="number" 
                           class="score-input absent-input" 
                           data-index="${index}" 
                           min="0" 
                           value="${student.times_absent || 0}">
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Add event listeners to input fields
        document.querySelectorAll('.present-input').forEach(input => {
            input.addEventListener('change', (e) => {
                const idx = parseInt(e.target.dataset.index);
                currentAttendanceData[idx].times_present = parseInt(e.target.value) || 0;
            });
            // Select text on focus for quick entry
            input.addEventListener('focus', function () { this.select(); });
        });

        document.querySelectorAll('.absent-input').forEach(input => {
            input.addEventListener('change', (e) => {
                const idx = parseInt(e.target.dataset.index);
                currentAttendanceData[idx].times_absent = parseInt(e.target.value) || 0;
            });
            // Select text on focus for quick entry
            input.addEventListener('focus', function () { this.select(); });
        });
    }

    async function saveAttendance() {
        const sessionId = sessionSelect.value;
        const termId = termSelect.value;
        const classId = classSelect.value;

        if (!sessionId || !termId || !classId) {
            showToast('Please select session, term, and class', 'warning');
            return;
        }

        if (!currentAttendanceData || currentAttendanceData.length === 0) {
            showToast('No data to save', 'warning');
            return;
        }

        const btnState1 = toggleButtonState(saveBtn, true);
        const btnState2 = toggleButtonState(headerSaveBtn, true);

        try {
            const payload = {
                class_id: classId,
                session_id: sessionId,
                term_id: termId,
                attendance: currentAttendanceData.map(s => ({
                    student_id: s.student_id,
                    times_present: parseInt(s.times_present) || 0,
                    times_absent: parseInt(s.times_absent) || 0
                }))
            };

            const response = await fetch('/attendance/api/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result.success) {
                showToast(result.message, 'success');
            } else {
                showToast(result.message || 'Failed to save attendance', 'error');
            }
        } catch (error) {
            console.error("Save error:", error);
            showToast('An error occurred while saving', 'error');
        } finally {
            toggleButtonState(saveBtn, false, btnState1);
            toggleButtonState(headerSaveBtn, false, btnState2);
        }
    }

    function toggleButtonState(btn, isLoading, originalHtml = '') {
        if (!btn) return originalHtml;
        if (isLoading) {
            const html = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            btn.disabled = true;
            return html;
        } else {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }
    }

    saveBtn.addEventListener('click', saveAttendance);
    headerSaveBtn.addEventListener('click', saveAttendance);

    // Initial load setup
    if (window.appConfig && window.appConfig.currentSessionId) {
        sessionSelect.value = window.appConfig.currentSessionId;
        // Trigger manual change to load terms
        sessionSelect.dispatchEvent(new Event('change'));
    }
});
