"""Subject Management Routes"""
from flask import Blueprint, render_template, request, jsonify
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
from database.db_manager import DatabaseManager

bp = Blueprint('subjects', __name__, url_prefix='/subjects')
db = DatabaseManager()

@bp.route('/')
def index():
    """Subjects management page"""
    # Get all classes
    classes = db.execute_query('SELECT * FROM classes ORDER BY level, stream')
    
    # Get subject counts for each class
    classes_with_counts = []
    for cls in classes:
        # Count assigned subjects
        count_res = db.execute_query('SELECT count(*) as count FROM class_subjects WHERE class_id = ?', (cls['id'],))
        count = count_res[0]['count'] if count_res else 0
        
        # Create a dict copy to avoid modifying the read-only Row object if applicable, 
        # though db_manager returns dicts usually.
        cls_dict = dict(cls)
        cls_dict['subject_count'] = count
        classes_with_counts.append(cls_dict)

    return render_template('subjects/index.html', classes=classes_with_counts)

@bp.route('/add', methods=['POST'])
def add_subject():
    """Add new subject"""
    data = request.json
    try:
        db.execute_update('INSERT INTO subjects (name, code) VALUES (?, ?)', 
                         (data['name'], data.get('code', '')))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/assign', methods=['POST'])
def assign_to_class():
    """Assign subject(s) to a class with detailed feedback"""
    data = request.json
    class_id = data.get('class_id')

    # Support both single and multiple assignment
    subject_ids = data.get('subject_ids', [])
    if 'subject_id' in data and data['subject_id']:
        subject_ids.append(data['subject_id'])

    if not class_id or not subject_ids:
        return jsonify({'success': False, 'message': 'Missing Class or Subject(s)'}), 400

    try:
        # Check which subjects are already assigned
        existing_assignments = db.execute_query('''
            SELECT subject_id FROM class_subjects WHERE class_id = ?
        ''', (class_id,))
        existing_ids = [row['subject_id'] for row in existing_assignments]

        newly_assigned = []
        already_existed = []

        for subj_id in subject_ids:
            if int(subj_id) in existing_ids:
                # Get subject name for feedback
                subject = db.execute_query('SELECT name FROM subjects WHERE id = ?', (subj_id,))
                if subject:
                    already_existed.append(subject[0]['name'])
            else:
                # Assign new subject
                db.execute_update('''
                    INSERT INTO class_subjects (class_id, subject_id)
                    VALUES (?, ?)
                ''', (class_id, subj_id))

                # Get subject name for feedback
                subject = db.execute_query('SELECT name FROM subjects WHERE id = ?', (subj_id,))
                if subject:
                    newly_assigned.append(subject[0]['name'])

        # Build response message
        message_parts = []
        if newly_assigned:
            message_parts.append(f"{len(newly_assigned)} newly assigned")
        if already_existed:
            message_parts.append(f"{len(already_existed)} already existed")

        return jsonify({
            'success': True,
            'message': ', '.join(message_parts) if message_parts else 'No changes made',
            'newly_assigned': newly_assigned,
            'already_existed': already_existed,
            'total_assigned': len(newly_assigned)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Database error: {str(e)}'
        }), 500

@bp.route('/unassign', methods=['POST'])
def unassign_subject():
    """Remove a subject from a class"""
    data = request.json
    try:
        db.execute_update('''
            DELETE FROM class_subjects 
            WHERE class_id = ? AND subject_id = ?
        ''', (data['class_id'], data['subject_id']))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/<int:subject_id>/classes')
def get_subject_classes(subject_id):
    """Get all classes that have this subject assigned"""
    rows = db.execute_query('''
    ''', (subject_id,))
    return jsonify([row['class_id'] for row in rows])

@bp.route('/assign_status/<int:class_id>')
def get_assign_status(class_id):
    """Get all subjects with a boolean indicating if they are assigned to the class"""
    all_subjects = db.execute_query('SELECT * FROM subjects ORDER BY name')
    
    # Get assigned IDs
    assigned_rows = db.execute_query('SELECT subject_id FROM class_subjects WHERE class_id = ?', (class_id,))
    assigned_ids = [row['subject_id'] for row in assigned_rows]
    
    result = []
    for sub in all_subjects:
        result.append({
            'id': sub['id'],
            'name': sub['name'],
            'code': sub['code'],
            'assigned': sub['id'] in assigned_ids
        })
        
    return jsonify(result)

@bp.route('/sync_assignments', methods=['POST'])
def sync_assignments():
    """Sync all class subjects (overwrite existing)"""
    data = request.json
    class_id = data.get('class_id')
    subject_ids = data.get('subject_ids', [])
    
    if not class_id:
        return jsonify({'success': False, 'message': 'Class ID required'})
        
    try:
        # 1. Delete all existing assignments for this class
        db.execute_update('DELETE FROM class_subjects WHERE class_id = ?', (class_id,))
        
        # 2. Insert new assignments
        for sub_id in subject_ids:
            db.execute_update('INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)', (class_id, sub_id))
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/update_code', methods=['POST'])
def update_subject_code():
    """Update only the code of a subject"""
    data = request.json
    try:
        db.execute_update('UPDATE subjects SET code = ? WHERE id = ?', (data['code'], data['id']))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/class/<int:class_id>')
def get_class_subjects(class_id):
    """Get subjects assigned to a specific class"""
    subjects = db.execute_query('''
        SELECT s.* FROM subjects s
        JOIN class_subjects cs ON s.id = cs.subject_id
        WHERE cs.class_id = ?
        ORDER BY s.name
    ''', (class_id,))
    return jsonify([dict(s) for s in subjects])
