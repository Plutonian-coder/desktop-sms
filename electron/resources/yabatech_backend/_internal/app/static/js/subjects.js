document.addEventListener('DOMContentLoaded', function () {
    const manageModal = document.getElementById('manage-class-modal');
    const checklistContainer = document.getElementById('subject-checklist');
    const searchInput = document.getElementById('subject-search');
    const closeBtns = document.querySelectorAll('.close-modal');

    // Modal Close Logic
    closeBtns.forEach(btn => {
        btn.onclick = () => manageModal.style.display = 'none';
    });

    window.onclick = (e) => {
        if (e.target == manageModal) manageModal.style.display = 'none';
    };

    // Edit Class Subjects Button
    document.querySelectorAll('.edit-class-btn').forEach(btn => {
        btn.onclick = async () => {
            const classId = btn.dataset.id;
            const className = btn.dataset.name;

            document.getElementById('current-class-id').value = classId;
            document.getElementById('modal-class-title').innerHTML = `<i class="fas fa-book"></i> Manage: ${className}`;

            manageModal.style.display = 'block';
            checklistContainer.innerHTML = '<div style="text-align: center; padding: 20px;">Loading subjects...</div>';

            try {
                // Fetch all subjects with assigned status
                const res = await fetch(`/subjects/assign_status/${classId}`);
                const subjects = await res.json();
                renderChecklist(subjects);
            } catch (e) {
                checklistContainer.innerHTML = `<div class="text-danger">Error: ${e.message}</div>`;
            }
        };
    });

    // Render Checklist
    function renderChecklist(subjects) {
        checklistContainer.innerHTML = '';
        if (subjects.length === 0) {
            checklistContainer.innerHTML = '<div style="padding: 20px;">No subjects found.</div>';
            return;
        }

        subjects.forEach(sub => {
            const item = document.createElement('label');
            item.className = 'checklist-item';
            item.innerHTML = `
                <input type="checkbox" name="subject_ids" value="${sub.id}" ${sub.assigned ? 'checked' : ''}>
                <span class="checklist-label">
                    ${sub.name}
                    ${sub.code ? `<span class="checklist-code">${sub.code}</span>` : ''}
                </span>
            `;
            checklistContainer.appendChild(item);
        });
    }

    // Search Filter
    searchInput.onkeyup = () => {
        const filter = searchInput.value.toLowerCase();
        const items = checklistContainer.getElementsByClassName('checklist-item');

        Array.from(items).forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(filter) ? '' : 'none';
        });
    };

    // Save Changes
    document.getElementById('save-class-subjects-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const classId = formData.get('class_id');
        const subjectIds = formData.getAll('subject_ids');

        // We use the bulk assign endpoint, but first we need to make sure we handle the "unassigned" ones.
        // The /subjects/assign logic appends. We probably need a 'sync' logic or just delete all and re-add.
        // Or simpler: The backend /assign endpoint (as written before) just adds new ones. 
        // We need a proper SYNC endpoint or logic.

        // Let's implement a Sync logic here:
        // 1. Unassign all (optional, but safer is separate calls or a new sync endpoint)
        // Actually, let's use a new endpoint or the logic we have.
        // Since we didn't add a /sync endpoint, let's modify the frontend to send a full replacement list
        // which the backend should handle.

        // Wait, the client asked for simple "add or delete subject".
        // Let's simply call a new /subjects/sync endpoint which we will adding.

        const saveBtn = e.target.querySelector('button[type="submit"]');
        const origText = saveBtn.textContent;
        saveBtn.textContent = 'Saving...';

        try {
            const res = await fetch('/subjects/sync_assignments', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ class_id: classId, subject_ids: subjectIds })
            });

            if ((await res.json()).success) {
                manageModal.style.display = 'none';
                location.reload(); // Reload to update counts
            } else {
                alert('Error saving assignments');
            }
        } catch (e) {
            alert('Error: ' + e.message);
        } finally {
            saveBtn.textContent = origText;
        }
    };
});
