/* Nano Banana Pro - Report Manager Logic */
document.addEventListener('DOMContentLoaded', function () {
    console.log('Nano Reports Loaded');

    // --- State & Selectors ---
    const s = {
        session: document.getElementById('report-session'),
        term: document.getElementById('report-term'),
        class: document.getElementById('report-class'),
        studentSearch: document.getElementById('student-search'),
        editorEmpty: document.getElementById('editor-empty-state'),
        editorContent: document.getElementById('editor-content'),
        studentList: document.getElementById('student-list'),
        managerContainer: document.getElementById('manager-container')
    };

    let currentStudentId = null;

    // --- 0. Load Terms for selected session ---
    async function loadTerms(sessionId) {
        s.term.innerHTML = '<option value="">Loading...</option>';
        try {
            const res = await fetch(`/scores/api/terms/${sessionId}`);
            const terms = await res.json();
            s.term.innerHTML = '';
            if (terms.length === 0) {
                s.term.innerHTML = '<option value="">No terms found</option>';
                return;
            }
            terms.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.id;
                opt.textContent = `Term ${t.term_number}`;
                s.term.appendChild(opt);
            });
        } catch (e) {
            s.term.innerHTML = '<option value="">Error loading terms</option>';
        }
    }

    // Load terms on session change
    s.session.onchange = () => {
        if (s.session.value) loadTerms(s.session.value);
    };

    // Load terms on page load if session is pre-selected
    if (s.session.value) loadTerms(s.session.value);

    // --- Helper: Convert star rating (1-5) to text ---
    function ratingToText(val) {
        const map = { 1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Very Good', 5: 'Excellent' };
        return map[parseInt(val)] || 'Good';
    }

    // --- Helper: Get teacher comment from grade ---
    function getComment(grade) {
        if (!grade) return '-';
        const letter = grade.charAt(0);
        const comments = {
            'A': 'Excellent performance.',
            'B': 'Very good result.',
            'C': 'Good attempt.',
            'D': 'Fair performance.',
            'E': 'Keep trying.',
            'F': 'More effort needed.'
        };
        return comments[letter] || '-';
    }

    // --- 1. Class Selection -> Load Roster ---
    s.class.onchange = async () => {
        const classId = s.class.value;
        if (!classId) {
            s.managerContainer.style.display = 'none';
            return;
        }

        s.managerContainer.style.display = 'grid'; // Enable workspace
        s.studentList.innerHTML = '<div class="empty-roster" style="padding:20px; text-align:center; color:#999;">Loading...</div>';

        try {
            const res = await fetch(`/scores/api/students_in_class/${classId}`);
            const students = await res.json();

            s.studentList.innerHTML = '';
            if (students.length === 0) {
                s.studentList.innerHTML = '<div class="empty-roster" style="padding:20px; text-align:center;">No students found.</div>';
                return;
            }

            students.forEach(std => {
                const card = document.createElement('div');
                card.className = 'student-card';
                card.dataset.id = std.id;
                card.innerHTML = `
                    <div class="s-avatar">${std.first_name[0]}${std.last_name[0]}</div>
                    <div class="s-info">
                        <div style="font-weight:600; font-size:14px;">${std.last_name} ${std.first_name}</div>
                        <div style="font-size:11px; color:#888;">${std.reg_number}</div>
                    </div>
                `;
                card.onclick = () => loadStudent(std.id, card);
                s.studentList.appendChild(card);
            });
        } catch (e) {
            s.studentList.innerHTML = `<div style="padding:20px; color:red;">Error: ${e.message}</div>`;
        }
    };

    // --- 2. Load Student (Report Card Mode) ---
    async function loadStudent(id, cardEl) {
        currentStudentId = id;

        // Highlight Sidebar
        document.querySelectorAll('.student-card').forEach(c => c.classList.remove('active'));
        if (cardEl) cardEl.classList.add('active');

        // Show Editor
        s.editorEmpty.style.display = 'none';
        s.editorContent.style.display = 'flex';

        try {
            const params = new URLSearchParams({
                student_id: id,
                class_id: s.class.value,
                session_id: s.session.value,
                term_id: s.term.value
            });

            const res = await fetch(`/reports/api/student_report_data?${params}`);
            const data = await res.json();

            if (!data.success) throw new Error(data.message || 'Failed to load');

            // === POPULATE REPORT CARD ===

            // A. School Header
            document.getElementById('rc-school-name').textContent = data.school.name || 'School Name';
            document.getElementById('rc-school-address').textContent = data.school.address || '';
            document.getElementById('rc-school-website').textContent = data.school.website || '';

            // Student initials in passport
            const nameParts = data.student.name.split(' ');
            const initials = nameParts.length >= 2 ? nameParts[0][0] + nameParts[1][0] : nameParts[0].substring(0, 2);
            document.getElementById('rc-student-initials').textContent = initials.toUpperCase();

            // Photo Logic
            const photoImg = document.getElementById('rc-student-photo');
            const initialsSpan = document.getElementById('rc-student-initials');

            if (data.student.photo_url) {
                photoImg.src = data.student.photo_url + '?t=' + new Date().getTime(); // Prevent caching
                photoImg.style.display = 'block';
                initialsSpan.style.display = 'none';
            } else {
                photoImg.style.display = 'none';
                initialsSpan.style.display = 'block';
            }

            // B. Student Info Box
            document.getElementById('rc-student-name').textContent = data.student.name;
            document.getElementById('rc-date').textContent = data.date || '';
            document.getElementById('rc-term').textContent = data.term_number ? `Term ${data.term_number}` : '';
            document.getElementById('rc-class').textContent = data.class_name || '';
            document.getElementById('rc-gender').textContent = data.student.gender || '';
            document.getElementById('rc-position').textContent = data.term_result.position || '-';

            // C. Academic Table
            const tbody = document.getElementById('rc-academic-body');
            if (data.academic.length) {
                tbody.innerHTML = data.academic.map(sub => `
                    <tr>
                        <td>${sub.subject}</td>
                        <td class="rc-score-cell">${sub.total}</td>
                        <td class="rc-grade-cell">${sub.grade}</td>
                        <td class="rc-comment-cell">${getComment(sub.grade)}</td>
                    </tr>
                `).join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:15px; color:#999;">No academic records found. Enter scores in the Score Entry page first.</td></tr>';
            }

            // D. Skills / Psychomotor (on report card preview)
            const skillKeys = ['punctuality', 'neatness', 'handwriting', 'politeness', 'attentiveness', 'sports', 'tools', 'drawing'];
            skillKeys.forEach(key => {
                const val = data.skills[key] || 3;
                const text = ratingToText(val);

                // Update report card preview text elements
                const textEl = document.getElementById(`rc-skill-${key}-text`);
                if (textEl) textEl.textContent = text;

                const psychEl = document.getElementById(`rc-psych-${key}`);
                if (psychEl) psychEl.textContent = text;
            });

            // E. Attendance
            const present = data.attendance.times_present;
            const absent = data.attendance.times_absent;
            document.getElementById('rc-att-present').textContent = (present !== '-' && absent !== '-') ? `${present} / ${parseInt(present) + parseInt(absent)} days` : '-';

            // F. Remarks (on report card)
            document.getElementById('rc-teacher-remark').textContent = data.remarks.teacher || '-';
            document.getElementById('rc-principal-remark').textContent = data.remarks.principal || '-';

            // G. Populate Skills tab (star ratings)
            document.querySelectorAll('.star-rating').forEach(el => {
                const name = el.dataset.name;
                const val = data.skills[name] || 3;
                setStarValue(el, val);
            });

            // H. Populate Remarks tab
            setRemarkData('teacher', data.remarks.teacher);
            setRemarkData('principal', data.remarks.principal);

        } catch (e) {
            console.error(e);
            alert("Error loading student data: " + e.message);
        }
    }

    // --- Photo Upload Logic ---
    const passportBox = document.getElementById('rc-passport-box');
    const photoInput = document.getElementById('photo-upload-input');
    const uploadOverlay = document.querySelector('.upload-overlay');

    if (passportBox && photoInput) {
        // Show overlay on hover
        passportBox.onmouseenter = () => uploadOverlay.style.display = 'flex';
        passportBox.onmouseleave = () => uploadOverlay.style.display = 'none';

        // Click to trigger file input
        passportBox.onclick = () => photoInput.click();

        // Handle file selection
        photoInput.onchange = async () => {
            if (!photoInput.files || !photoInput.files[0]) return;

            const file = photoInput.files[0];
            const formData = new FormData();
            formData.append('photo', file);
            formData.append('student_id', currentStudentId);

            // Show loading state
            const icon = uploadOverlay.querySelector('i');
            const originalIconClass = icon.className;
            icon.className = 'fas fa-spinner fa-spin';

            try {
                const res = await fetch('/reports/api/upload_photo', {
                    method: 'POST',
                    body: formData
                });
                const result = await res.json();

                if (result.success) {
                    // Update image
                    const img = document.getElementById('rc-student-photo');
                    const initials = document.getElementById('rc-student-initials');

                    img.src = result.photo_url + '?t=' + new Date().getTime(); // Prevent cache
                    img.style.display = 'block';
                    initials.style.display = 'none';

                    // Reset input
                    photoInput.value = '';
                } else {
                    alert('Upload failed: ' + result.message);
                }
            } catch (err) {
                console.error(err);
                alert('Upload error: ' + err.message);
            } finally {
                // Restore icon
                icon.className = originalIconClass;
            }
        };
    }

    // --- 3. Tabs Logic ---
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.onclick = () => {
            // Remove active from all tabs & panes
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

            // Activate current
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        };
    });

    // --- 4. Star Rating Logic ---
    document.querySelectorAll('.star-rating').forEach(ratingEl => {
        const input = ratingEl.querySelector('input');
        const stars = ratingEl.querySelectorAll('.fas');

        stars.forEach(star => {
            // Hover
            star.onmouseenter = () => {
                const val = parseInt(star.dataset.val);
                highlightStars(ratingEl, val);
            };

            // Click
            star.onclick = () => {
                const val = parseInt(star.dataset.val);
                input.value = val;
                setStarValue(ratingEl, val);
            };
        });

        // Mouse Leave (Reset to saved value)
        ratingEl.onmouseleave = () => {
            highlightStars(ratingEl, parseInt(input.value));
        };
    });

    function highlightStars(container, val) {
        container.querySelectorAll('.fas').forEach(s => {
            const sVal = parseInt(s.dataset.val);
            if (sVal <= val) s.classList.add('active');
            else s.classList.remove('active');
        });
    }

    function setStarValue(container, val) {
        container.querySelector('input').value = val;
        highlightStars(container, val);
    }

    // --- 5. Quick Chips Logic ---
    document.querySelectorAll('.chip').forEach(chip => {
        chip.onclick = () => {
            const role = chip.dataset.for;
            const text = chip.dataset.text;

            const select = document.getElementById(role + '-remark');
            const textarea = document.getElementById(role + '-remark-text');

            let found = false;
            for (let opt of select.options) {
                if (opt.value === text) {
                    select.value = text;
                    textarea.value = "";
                    found = true;
                    break;
                }
            }

            if (!found) {
                select.value = "";
                textarea.value = text;
            }
        };
    });

    function setRemarkData(role, value) {
        if (!value) value = "";
        const select = document.getElementById(role + '-remark');
        const textarea = document.getElementById(role + '-remark-text');

        let match = false;
        for (let opt of select.options) {
            if (opt.value === value) {
                select.value = value;
                textarea.value = "";
                match = true;
                break;
            }
        }

        if (!match) {
            select.value = "";
            textarea.value = value;
        }
    }

    // --- 6. Save & Print ---
    document.getElementById('save-generate-btn').onclick = async function () {
        const btn = this;
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Saving...';
        btn.disabled = true;

        // Open window immediately to bypass popup blocker
        const pdfWindow = window.open('', '_blank');
        if (pdfWindow) {
            pdfWindow.document.write('<html><head><title>Generating Report...</title><style>body{font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;background:#f5f5f5;color:#333;}</style></head><body><div style="text-align:center"><h2>Generating PDF...</h2><p>Please wait while we prepare the report.</p></div></body></html>');
        }

        try {
            // Gather Data
            const form = document.getElementById('skills-form');
            const formData = new FormData(form);
            const skills = {};
            formData.forEach((value, key) => skills[key] = value);

            // Remarks
            const getRem = (role) => {
                const sel = document.getElementById(role + '-remark').value;
                const txt = document.getElementById(role + '-remark-text').value;
                return sel || txt;
            };

            const payload = {
                student_id: currentStudentId,
                session_id: s.session.value,
                term_id: s.term.value,
                skills: skills,
                remarks: {
                    teacher: getRem('teacher'),
                    principal: getRem('principal')
                }
            };

            // Save
            const saveRes = await fetch('/reports/api/save_report_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!(await saveRes.json()).success) throw new Error("Failed to save data.");

            // Generate
            const genRes = await fetch('/reports/api/generate_single_report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    student_id: currentStudentId,
                    session_id: s.session.value,
                    term_id: s.term.value
                })
            });

            const genData = await genRes.json();
            if (genData.success) {
                if (pdfWindow) {
                    pdfWindow.location.href = `/reports/download/${genData.filename}`;
                } else {
                    window.location.href = `/reports/download/${genData.filename}`;
                }
            } else {
                if (pdfWindow) pdfWindow.close();
                throw new Error(genData.message);
            }

        } catch (e) {
            if (pdfWindow) pdfWindow.close();
            alert("Error: " + e.message);
        } finally {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }
    };

    // --- Search ---
    s.studentSearch.onkeyup = function () {
        const val = this.value.toLowerCase();
        document.querySelectorAll('.student-card').forEach(card => {
            const txt = card.textContent.toLowerCase();
            card.style.display = txt.includes(val) ? 'flex' : 'none';
        });
    };

});
