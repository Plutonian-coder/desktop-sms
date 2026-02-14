// Score Entry JavaScript (Dual Mode) v3
console.log("Scores JS Loaded");

let entryMode = 'student'; // 'student' or 'subject'
let selectedFilters = {
    session: null,
    term: null,
    class: null,
    student: null,
    subject: null
};

// Helper to safe-get value
const getValue = (id) => {
    const el = document.getElementById(id);
    return el ? el.value : null;
};

document.addEventListener('DOMContentLoaded', async function () {
    const urlParams = new URLSearchParams(window.location.search);
    const urlStudentId = urlParams.get('student_id');
    const urlClassId = urlParams.get('class_id');

    if (urlClassId) {
        document.getElementById('class-select').value = urlClassId;
        selectedFilters.class = urlClassId;
        await loadClassStudents(urlClassId);
        await loadClassSubjects(urlClassId);

        if (urlStudentId) {
            document.getElementById('student-select').value = urlStudentId;
            selectedFilters.student = urlStudentId;
            loadGrid();
        }
    }
});

// Mode Toggling
document.querySelectorAll('.btn-mode').forEach(btn => {
    btn.onclick = function () {
        document.querySelectorAll('.btn-mode').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        entryMode = this.dataset.mode;

        // UI Updates
        document.getElementById('student-filter-group').style.display = entryMode === 'student' ? 'block' : 'none';
        document.getElementById('subject-filter-group').style.display = entryMode === 'subject' ? 'block' : 'none';
        document.getElementById('row-header').textContent = entryMode === 'student' ? 'Subject' : 'Student';

        clearGrid();
        if (entryMode === 'subject' && selectedFilters.class) {
            loadClassSubjects(selectedFilters.class);
        }
    };
});

// Session Change -> Load Terms
document.getElementById('session-select').addEventListener('change', async function () {
    const sessionId = this.value;
    selectedFilters.session = sessionId;
    const termSelect = document.getElementById('term-select');

    termSelect.innerHTML = '<option value="">Loading...</option>';

    if (!sessionId) {
        termSelect.innerHTML = '<option value="">Select Term</option>';
        return;
    }

    try {
        const response = await fetch(`/scores/api/terms/${sessionId}`);
        const terms = await response.json();

        termSelect.innerHTML = '<option value="">Select Term</option>';
        terms.forEach(term => {
            const option = document.createElement('option');
            option.value = term.id;
            option.textContent = `Term ${term.term_number}`;
            termSelect.appendChild(option);
        });
    } catch (e) {
        console.error("Error loading terms:", e);
    }
    clearGrid();
});

// Class Change -> Load Students AND Subjects
document.getElementById('class-select').addEventListener('change', async function () {
    const classId = this.value;
    selectedFilters.class = classId;

    loadClassStudents(classId);
    loadClassSubjects(classId);
    clearGrid();
});

async function loadClassStudents(classId) {
    const studentSelect = document.getElementById('student-select');
    if (!classId) {
        studentSelect.innerHTML = '<option value="">Select Student</option>';
        return;
    }

    studentSelect.innerHTML = '<option value="">Loading students...</option>';
    try {
        const response = await fetch(`/scores/api/students_in_class/${classId}`);
        const students = await response.json();

        studentSelect.innerHTML = '<option value="">Select Student</option>';
        students.forEach(std => {
            const option = document.createElement('option');
            option.value = std.id;
            option.textContent = `${std.last_name} ${std.first_name} (${std.reg_number})`;
            studentSelect.appendChild(option);
        });
    } catch (e) {
        studentSelect.innerHTML = '<option value="">Error loading students</option>';
    }
}

async function loadClassSubjects(classId) {
    const subjectSelect = document.getElementById('subject-select');
    if (!classId) {
        subjectSelect.innerHTML = '<option value="">Select Subject</option>';
        return;
    }

    subjectSelect.innerHTML = '<option value="">Loading subjects...</option>';
    try {
        const response = await fetch(`/scores/api/class_subjects/${classId}`);
        const subjects = await response.json();

        subjectSelect.innerHTML = '<option value="">Select Subject</option>';
        subjects.forEach(sub => {
            const option = document.createElement('option');
            option.value = sub.id;
            option.textContent = sub.name;
            subjectSelect.appendChild(option);
        });
    } catch (e) {
        subjectSelect.innerHTML = '<option value="">Error loading subjects</option>';
    }
}

// Student/Subject Selection -> Load Grid
document.getElementById('student-select').onchange = () => {
    selectedFilters.student = getValue('student-select');
    loadGrid();
};

document.getElementById('subject-select').onchange = () => {
    selectedFilters.subject = getValue('subject-select');
    loadGrid();
};

document.getElementById('term-select').onchange = () => {
    selectedFilters.term = getValue('term-select');
    loadGrid();
};

async function loadGrid() {
    if (entryMode === 'student') {
        loadStudentScoreGrid();
    } else {
        loadSubjectScoreGrid();
    }
}

async function loadStudentScoreGrid() {
    const tbody = document.getElementById('score-tbody');
    const sessionId = getValue('session-select');
    const termId = getValue('term-select');
    const classId = getValue('class-select');
    const studentId = getValue('student-select');

    if (!sessionId || !termId || !classId || !studentId) return;

    tbody.innerHTML = '<tr><td colspan="9" class="no-data">Loading scores...</td></tr>';

    const params = new URLSearchParams({ session_id: sessionId, term_id: termId, class_id: classId, student_id: studentId });

    try {
        const response = await fetch(`/scores/api/student_score_grid?${params}`);
        const subjects = await response.json();

        if (subjects.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="no-data">No subjects assigned to this class</td></tr>';
            return;
        }

        tbody.innerHTML = subjects.map(sub => `
            <tr data-subject-id="${sub.subject_id}">
                <td style="font-weight: 500;">${sub.subject_name}</td>
                <td><input type="number" class="ca-input form-control" value="${sub.ca}" min="0" max="30"></td>
                <td><input type="number" class="exam-input form-control" value="${sub.exam}" min="0" max="70"></td>
                <td class="readonly total-cell" style="font-weight: bold;">${sub.total}</td>
                <td class="readonly grade-cell" style="color: var(--primary); font-weight: bold;">${sub.grade}</td>
                <td class="readonly text-muted">${sub.position}</td>
                <td class="readonly text-muted">${sub.highest}</td>
                <td class="readonly text-muted">${sub.lowest}</td>
                <td class="readonly text-muted">${sub.average}</td>
            </tr>
        `).join('');

        addInputListeners();
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="9" class="no-data">Error: ${e.message}</td></tr>`;
    }
}

async function loadSubjectScoreGrid() {
    const tbody = document.getElementById('score-tbody');
    const sessionId = getValue('session-select');
    const termId = getValue('term-select');
    const classId = getValue('class-select');
    const subjectId = getValue('subject-select');

    if (!sessionId || !termId || !classId || !subjectId) return;

    tbody.innerHTML = '<tr><td colspan="9" class="no-data">Loading students...</td></tr>';

    const params = new URLSearchParams({ session_id: sessionId, term_id: termId, class_id: classId, subject_id: subjectId });

    try {
        const response = await fetch(`/scores/api/subject_score_grid?${params}`);
        const students = await response.json();

        if (students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="no-data">No students found in this class</td></tr>';
            return;
        }

        tbody.innerHTML = students.map(std => `
            <tr data-student-id="${std.student_id}">
                <td style="font-weight: 500;"><div>${std.full_name}</div><small class="text-muted">${std.reg_number}</small></td>
                <td><input type="number" class="ca-input form-control" value="${std.ca}" min="0" max="30"></td>
                <td><input type="number" class="exam-input form-control" value="${std.exam}" min="0" max="70"></td>
                <td class="readonly total-cell" style="font-weight: bold;">${std.total}</td>
                <td class="readonly grade-cell" style="color: var(--primary); font-weight: bold;">${std.grade}</td>
                <td class="readonly text-muted">${std.position}</td>
                <td class="readonly text-muted">${std.highest}</td>
                <td class="readonly text-muted">${std.lowest}</td>
                <td class="readonly text-muted">${std.average}</td>
            </tr>
        `).join('');

        addInputListeners();
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="9" class="no-data">Error: ${e.message}</td></tr>`;
    }
}

function clearGrid() {
    document.getElementById('score-tbody').innerHTML = '<tr><td colspan="9" class="no-data">Select filters to load grid</td></tr>';
}

function addInputListeners() {
    document.querySelectorAll('.ca-input, .exam-input').forEach(input => {
        input.oninput = function () {
            const row = this.closest('tr');
            let ca = parseFloat(row.querySelector('.ca-input').value) || 0;
            let exam = parseFloat(row.querySelector('.exam-input').value) || 0;
            if (ca > 30) { ca = 30; row.querySelector('.ca-input').value = 30; }
            if (exam > 70) { exam = 70; row.querySelector('.exam-input').value = 70; }
            const total = ca + exam;
            row.querySelector('.total-cell').textContent = total;
            row.querySelector('.grade-cell').textContent = calculateGrade(total);
        };
    });
}

function calculateGrade(total) {
    if (total >= 80) return 'A1';
    if (total >= 70) return 'B2';
    if (total >= 65) return 'B3';
    if (total >= 60) return 'C4';
    if (total >= 55) return 'C5';
    if (total >= 50) return 'C6';
    if (total >= 45) return 'D7';
    if (total >= 40) return 'E8';
    return 'F9';
}

// SAVE
async function saveScores() {
    const btn = document.getElementById('save-btn');
    const headerBtn = document.getElementById('header-save-btn');
    const originalText = btn.innerHTML;

    btn.disabled = headerBtn.disabled = true;
    btn.innerHTML = headerBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    const session_id = getValue('session-select');
    const term_id = getValue('term-select');
    const class_id = getValue('class-select');

    const rows = document.querySelectorAll('#score-tbody tr');
    const scores = [];

    rows.forEach(row => {
        const id = entryMode === 'student' ? row.dataset.subjectId : row.dataset.studentId;
        if (id) {
            const ca = parseFloat(row.querySelector('.ca-input').value) || 0;
            const exam = parseFloat(row.querySelector('.exam-input').value) || 0;
            const entry = { ca, exam };
            if (entryMode === 'student') entry.subject_id = id;
            else entry.student_id = id;
            scores.push(entry);
        }
    });

    const url = entryMode === 'student' ? '/scores/api/save_student_scores' : '/scores/api/save_subject_scores';
    const body = { session_id, term_id, class_id, scores };
    if (entryMode === 'student') body.student_id = getValue('student-select');
    else body.subject_id = getValue('subject-select');

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const result = await response.json();
        alert(result.message);
        loadGrid();
    } catch (e) {
        alert('Error: ' + e.message);
    } finally {
        btn.disabled = headerBtn.disabled = false;
        btn.innerHTML = originalText;
        headerBtn.innerHTML = '<i class="fas fa-save"></i> Save Scores';
    }
}

document.getElementById('save-btn').onclick = saveScores;
document.getElementById('header-save-btn').onclick = saveScores;

// --- Excel Export / Import ---
document.getElementById('export-btn').onclick = () => {
    const classId = getValue('class-select');
    const sessionId = getValue('session-select');
    const termId = getValue('term-select');

    if (!classId || !sessionId || !termId) {
        alert('Please select Session, Term, and Class first.');
        return;
    }

    let url = `/scores/api/export_excel?class_id=${classId}&session_id=${sessionId}&term_id=${termId}`;
    if (entryMode === 'subject') {
        const subjectId = getValue('subject-select');
        if (subjectId) url += `&subject_id=${subjectId}`;
    }

    window.location.href = url;
};

document.getElementById('import-btn').onclick = () => {
    const classId = getValue('class-select');
    if (!classId) {
        alert('Please select a class first.');
        return;
    }
    document.getElementById('import-file').click();
};

document.getElementById('import-file').onchange = async function () {
    if (!this.files[0]) return;

    const file = this.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('class_id', getValue('class-select'));
    formData.append('session_id', getValue('session-select'));
    formData.append('term_id', getValue('term-select'));

    const btn = document.getElementById('import-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Importing...';
    btn.disabled = true;

    try {
        const res = await fetch('/scores/api/import_excel', {
            method: 'POST',
            body: formData
        });
        const result = await res.json();

        if (result.success) {
            alert(result.message);
            loadGrid();
        } else {
            alert('Import Failed: ' + result.message);
            if (result.errors) console.error(result.errors);
        }
    } catch (e) {
        alert('Error: ' + e.message);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
        this.value = ''; // Reset input
    }
};
