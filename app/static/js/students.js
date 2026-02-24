// Student Management JavaScript

// ─── Toast Notification Utility ───────────────────────────────────────────────
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

function showValidationErrors(errors) {
    if (Array.isArray(errors)) {
        errors.forEach(error => showToast('Validation Error', error, 'error'));
    } else {
        showToast('Validation Error', errors, 'error');
    }
}

// ─── Reg Number Auto-Generation ───────────────────────────────────────────────
async function fetchAndSetRegNumber(classId) {
    const regInput = document.getElementById('reg-number-display');
    const spinner = document.getElementById('reg-spinner');
    const badge = document.getElementById('reg-badge');
    const saveBtn = document.getElementById('save-student-btn');

    if (!classId) {
        regInput.value = '';
        regInput.placeholder = 'Select a class first…';
        if (badge) badge.style.display = 'none';
        if (spinner) spinner.style.display = 'none';
        return;
    }

    // Show loading state
    regInput.value = '';
    regInput.placeholder = 'Generating…';
    if (spinner) spinner.style.display = 'inline';
    if (badge) badge.style.display = 'none';
    if (saveBtn) saveBtn.disabled = true;

    try {
        const res = await fetch(`/students/generate-reg-number?class_id=${classId}`);
        const data = await res.json();

        if (data.success) {
            regInput.value = data.reg_number;
            regInput.placeholder = '';
            if (badge) {
                badge.style.display = 'inline';
            }
        } else {
            regInput.value = '';
            regInput.placeholder = 'Error generating number';
            showToast('Warning', data.message || 'Could not generate reg number', 'warning');
        }
    } catch (err) {
        regInput.value = '';
        regInput.placeholder = 'Network error';
        showToast('Error', 'Failed to fetch registration number', 'error');
    } finally {
        if (spinner) spinner.style.display = 'none';
        if (saveBtn) saveBtn.disabled = false;
    }
}

// ─── Table Row Helpers ────────────────────────────────────────────────────────
function buildRegBadge(regNumber) {
    return `<span style="font-family:monospace; font-weight:600;
        background:var(--primary-light,#eef2ff); color:var(--primary);
        padding:3px 8px; border-radius:6px; font-size:12px;">${regNumber}</span>`;
}

function addStudentRow(student) {
    const tbody = document.getElementById('student-tbody');
    const noDataRow = tbody.querySelector('.no-data');
    if (noDataRow) noDataRow.parentElement.remove();

    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${buildRegBadge(student.reg_number)}</td>
        <td style="font-weight: 600;">${student.last_name} ${student.first_name}</td>
        <td><span class="class-badge">${student.class_name || 'Not Assigned'}</span></td>
        <td>${student.gender}</td>
        <td>${student.parent_phone || 'N/A'}</td>
        <td class="text-right">
            <button class="btn btn-sm btn-outline edit-student-btn" data-id="${student.id}" title="Edit">
                <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-sm btn-outline delete-student-btn" data-id="${student.id}" title="Delete"
                style="color:var(--red); border-color:var(--red);">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    tbody.insertBefore(row, tbody.firstChild);
    attachRowEventListeners(row);

    row.style.background = 'rgba(46, 204, 113, 0.1)';
    setTimeout(() => { row.style.background = ''; }, 2000);
}

function updateStudentRow(student) {
    const rows = document.querySelectorAll('#student-tbody tr');
    rows.forEach(row => {
        const editBtn = row.querySelector('.edit-student-btn');
        if (editBtn && editBtn.dataset.id == student.id) {
            row.cells[0].innerHTML = buildRegBadge(student.reg_number);
            row.cells[1].textContent = `${student.last_name} ${student.first_name}`;
            row.cells[2].textContent = student.class_name || 'Not Assigned';
            row.cells[3].textContent = student.gender;
            row.cells[4].textContent = student.parent_phone || 'N/A';

            row.style.background = 'rgba(253, 216, 53, 0.2)';
            setTimeout(() => { row.style.background = ''; }, 2000);
        }
    });
}

// ─── Row Button Event Listeners ───────────────────────────────────────────────
function attachRowEventListeners(row) {
    const editBtn = row.querySelector('.edit-student-btn');
    const deleteBtn = row.querySelector('.delete-student-btn');

    if (editBtn) {
        editBtn.onclick = async () => {
            const studentId = editBtn.dataset.id;
            try {
                const res = await fetch(`/students/${studentId}`);
                const student = await res.json();

                if (student) {
                    const form = document.getElementById('add-student-form');

                    document.getElementById('modal-title').innerHTML =
                        '<i class="fas fa-user-edit"></i> Edit Student';
                    document.getElementById('student_id').value = student.id;

                    // Reg number is displayed read-only — just show existing value
                    const regInput = document.getElementById('reg-number-display');
                    regInput.value = student.reg_number;
                    regInput.style.color = 'var(--text-primary)';
                    const badge = document.getElementById('reg-badge');
                    if (badge) badge.style.display = 'inline';

                    form.elements['first_name'].value = student.first_name;
                    form.elements['last_name'].value = student.last_name;
                    form.elements['gender'].value = student.gender;
                    form.elements['dob'].value = student.dob;
                    form.elements['class_id'].value = student.class_id;
                    form.elements['parent_name'].value = student.parent_name || '';
                    form.elements['parent_phone'].value = student.parent_phone || '';
                    form.elements['parent_address'].value = student.parent_address || '';

                    document.getElementById('student-modal').style.display = 'block';
                }
            } catch (e) {
                showToast('Error', 'Failed to fetch student details', 'error');
            }
        };
    }

    if (deleteBtn) {
        deleteBtn.onclick = async () => {
            if (confirm('Are you sure you want to delete this student?')) {
                const studentId = deleteBtn.dataset.id;
                try {
                    const res = await fetch(`/students/delete/${studentId}`, { method: 'POST' });
                    const result = await res.json();
                    if (result.success) {
                        row.style.animation = 'slideOutRight 0.3s ease';
                        setTimeout(() => row.remove(), 300);
                        showToast('Success', 'Student deleted successfully', 'success');
                    } else {
                        showToast('Error', result.message, 'error');
                    }
                } catch (e) {
                    showToast('Error', 'Failed to delete student', 'error');
                }
            }
        };
    }
}

// ─── Main DOMContentLoaded ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('student-modal');
    const addBtn = document.getElementById('add-student-btn');
    const closeBtns = document.querySelectorAll('.close-modal');
    const addForm = document.getElementById('add-student-form');
    const studentSearch = document.getElementById('student-search');
    const classFilter = document.getElementById('class-filter');
    const classSelect = document.getElementById('form-class-id');

    // ── Modal open (Add mode) ─────────────────────────────────────────────────
    if (addBtn) {
        addBtn.onclick = () => {
            document.getElementById('modal-title').innerHTML =
                '<i class="fas fa-user-plus"></i> Register New Student';
            document.getElementById('student_id').value = '';
            addForm.reset();

            // Reset reg number display
            const regInput = document.getElementById('reg-number-display');
            regInput.value = '';
            regInput.placeholder = 'Select a class first…';
            regInput.style.color = 'var(--text-muted)';
            const badge = document.getElementById('reg-badge');
            if (badge) badge.style.display = 'none';

            modal.style.display = 'block';
        };
    }

    // ── Close modal ───────────────────────────────────────────────────────────
    closeBtns.forEach(btn => {
        btn.onclick = () => modal.style.display = 'none';
    });
    window.onclick = (event) => {
        if (event.target === modal) modal.style.display = 'none';
    };

    // ── Class dropdown → auto-generate reg number (Add mode only) ────────────
    if (classSelect) {
        classSelect.addEventListener('change', function () {
            const studentId = document.getElementById('student_id').value;
            // Only auto-fill on new student forms, not edit
            if (!studentId && this.value) {
                fetchAndSetRegNumber(this.value);
            }
        });
    }

    // ── Attach listeners to existing rows ────────────────────────────────────
    document.querySelectorAll('#student-tbody tr').forEach(row => {
        attachRowEventListeners(row);
    });

    // ── Form Submission ───────────────────────────────────────────────────────
    if (addForm) {
        addForm.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(addForm);
            const data = Object.fromEntries(formData.entries());
            const studentId = document.getElementById('student_id').value;
            const submitBtn = addForm.querySelector('button[type="submit"]');
            const isUpdate = !!studentId;

            const url = isUpdate
                ? `/students/update/${studentId}`
                : '/students/add';

            submitBtn.classList.add('btn-loading');
            submitBtn.disabled = true;

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                submitBtn.classList.remove('btn-loading');
                submitBtn.disabled = false;

                if (result.success) {
                    modal.style.display = 'none';
                    addForm.reset();

                    showToast(
                        'Success',
                        isUpdate ? 'Student updated successfully' : 'Student registered successfully',
                        'success'
                    );

                    if (result.student) {
                        if (isUpdate) {
                            updateStudentRow(result.student);
                        } else {
                            addStudentRow(result.student);
                        }
                    } else {
                        setTimeout(() => location.reload(), 1000);
                    }
                } else {
                    if (result.errors) {
                        showValidationErrors(result.errors);
                    } else {
                        showToast('Error', result.message || 'Operation failed', 'error');
                    }
                }
            } catch (error) {
                submitBtn.classList.remove('btn-loading');
                submitBtn.disabled = false;
                showToast('Error', 'Network error: ' + error.message, 'error');
            }
        };
    }

    // ── Search & Filter ───────────────────────────────────────────────────────
    function filterTable() {
        const searchText = studentSearch.value.toLowerCase();
        const classVal = classFilter.value;
        const rows = document.querySelectorAll('#student-tbody tr');

        rows.forEach(row => {
            if (row.querySelector('.no-data')) return;

            const name = row.cells[1].textContent.toLowerCase();
            const reg = row.cells[0].textContent.toLowerCase();
            const cls = row.cells[2].textContent;

            const matchesSearch = name.includes(searchText) || reg.includes(searchText);
            const matchesClass = classVal === '' || cls.trim() === classVal;

            row.style.display = (matchesSearch && matchesClass) ? '' : 'none';
        });
    }

    if (studentSearch) studentSearch.oninput = filterTable;
    if (classFilter) classFilter.onchange = filterTable;
});
