// Student Management JavaScript

// Toast Notification Utility
function showToast(title, message, type = 'success') {
    // Create toast container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Create toast element
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

    // Add to container
    container.appendChild(toast);

    // Close button functionality
    toast.querySelector('.toast-close').onclick = () => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    };

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// Show validation errors
function showValidationErrors(errors) {
    if (Array.isArray(errors)) {
        errors.forEach(error => {
            showToast('Validation Error', error, 'error');
        });
    } else {
        showToast('Validation Error', errors, 'error');
    }
}

// Add table row dynamically
function addStudentRow(student) {
    const tbody = document.getElementById('student-tbody');
    const noDataRow = tbody.querySelector('.no-data');
    if (noDataRow) {
        noDataRow.parentElement.remove();
    }

    const row = document.createElement('tr');
    row.innerHTML = `
        <td class="gray-bg">${student.reg_number}</td>
        <td style="font-weight: 600;">${student.last_name} ${student.first_name}</td>
        <td>${student.class_name || 'Not Assigned'}</td>
        <td>${student.gender}</td>
        <td>${student.parent_phone || 'N/A'}</td>
        <td class="text-right">
            <button class="btn-icon btn-blue edit-student-btn" data-id="${student.id}" title="Edit">
                <i class="fas fa-edit"></i>
            </button>
            <button class="btn-icon btn-red delete-student-btn" data-id="${student.id}" title="Delete">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    tbody.insertBefore(row, tbody.firstChild);

    // Re-attach event listeners
    attachRowEventListeners(row);

    // Highlight new row
    row.style.background = 'rgba(46, 204, 113, 0.1)';
    setTimeout(() => {
        row.style.background = '';
    }, 2000);
}

// Update table row
function updateStudentRow(student) {
    const rows = document.querySelectorAll('#student-tbody tr');
    rows.forEach(row => {
        const editBtn = row.querySelector('.edit-student-btn');
        if (editBtn && editBtn.dataset.id == student.id) {
            row.cells[0].textContent = student.reg_number;
            row.cells[1].textContent = `${student.last_name} ${student.first_name}`;
            row.cells[2].textContent = student.class_name || 'Not Assigned';
            row.cells[3].textContent = student.gender;
            row.cells[4].textContent = student.parent_phone || 'N/A';

            // Highlight updated row
            row.style.background = 'rgba(253, 216, 53, 0.2)';
            setTimeout(() => {
                row.style.background = '';
            }, 2000);
        }
    });
}

// Attach event listeners to row buttons
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
                    document.getElementById('modal-title').innerHTML = '<i class="fas fa-user-edit"></i> Edit Student';
                    document.getElementById('student_id').value = student.id;
                    document.getElementById('add-student-form').elements['reg_number'].value = student.reg_number;
                    document.getElementById('add-student-form').elements['first_name'].value = student.first_name;
                    document.getElementById('add-student-form').elements['last_name'].value = student.last_name;
                    document.getElementById('add-student-form').elements['gender'].value = student.gender;
                    document.getElementById('add-student-form').elements['dob'].value = student.dob;
                    document.getElementById('add-student-form').elements['class_id'].value = student.class_id;
                    document.getElementById('add-student-form').elements['parent_name'].value = student.parent_name || '';
                    document.getElementById('add-student-form').elements['parent_phone'].value = student.parent_phone || '';
                    document.getElementById('add-student-form').elements['parent_address'].value = student.parent_address || '';

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

document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('student-modal');
    const addBtn = document.getElementById('add-student-btn');
    const closeBtns = document.querySelectorAll('.close-modal');
    const addForm = document.getElementById('add-student-form');
    const studentSearch = document.getElementById('student-search');
    const classFilter = document.getElementById('class-filter');
    const studentTable = document.getElementById('student-table');

    // Modal Control
    if (addBtn) {
        addBtn.onclick = () => {
            document.getElementById('modal-title').innerHTML = '<i class="fas fa-user-plus"></i> Register New Student';
            document.getElementById('student_id').value = '';
            addForm.reset();
            modal.style.display = 'block';
        };
    }

    closeBtns.forEach(btn => {
        btn.onclick = () => modal.style.display = 'none';
    });

    window.onclick = (event) => {
        if (event.target == modal) modal.style.display = 'none';
    };

    // Attach event listeners to existing rows
    document.querySelectorAll('#student-tbody tr').forEach(row => {
        attachRowEventListeners(row);
    });

    // Form Submission
    if (addForm) {
        addForm.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(addForm);
            const data = Object.fromEntries(formData.entries());
            const studentId = document.getElementById('student_id').value;
            const submitBtn = addForm.querySelector('button[type="submit"]');

            const url = studentId ? `/students/update/${studentId}` : '/students/add';
            const isUpdate = !!studentId;

            console.log('Submitting student form:', data);
            console.log('URL:', url);
            console.log('Is Update:', isUpdate);

            // Show loading state
            submitBtn.classList.add('btn-loading');
            submitBtn.disabled = true;

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                console.log('Response status:', response.status);
                const result = await response.json();
                console.log('Response data:', result);

                // Remove loading state
                submitBtn.classList.remove('btn-loading');
                submitBtn.disabled = false;

                if (result.success) {
                    // Close modal
                    modal.style.display = 'none';
                    addForm.reset();

                    // Show success toast
                    showToast(
                        'Success',
                        isUpdate ? 'Student updated successfully' : 'Student registered successfully',
                        'success'
                    );

                    // Update table dynamically
                    if (result.student) {
                        console.log('Adding/updating student row:', result.student);
                        if (isUpdate) {
                            updateStudentRow(result.student);
                        } else {
                            addStudentRow(result.student);
                        }
                    } else {
                        console.warn('No student data in response, reloading page');
                        // Fallback to reload if student data not returned
                        setTimeout(() => location.reload(), 1000);
                    }
                } else {
                    console.error('Registration failed:', result);
                    // Show error
                    if (result.errors) {
                        showValidationErrors(result.errors);
                    } else {
                        showToast('Error', result.message || 'Operation failed', 'error');
                    }
                }
            } catch (error) {
                console.error('Form submission error:', error);
                // Remove loading state
                submitBtn.classList.remove('btn-loading');
                submitBtn.disabled = false;
                showToast('Error', 'Network error: ' + error.message, 'error');
            }
        };
    }

    // Search and Filter Logic
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
            const matchesClass = classVal === "" || cls === classVal;

            if (matchesSearch && matchesClass) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    if (studentSearch) studentSearch.oninput = filterTable;
    if (classFilter) classFilter.onchange = filterTable;
});
