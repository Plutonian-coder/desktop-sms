"""Fee Management Routes"""
from flask import Blueprint, render_template, request, jsonify
import sys, os, uuid, json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
from database.db_manager import DatabaseManager

bp = Blueprint('fees', __name__, url_prefix='/fees')
db = DatabaseManager()

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN PAGE
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/')
def index():
    sessions = db.execute_query('SELECT * FROM sessions ORDER BY name DESC')
    current_session = db.get_current_session()
    current_term = db.get_current_term()
    classes = db.execute_query('SELECT * FROM classes ORDER BY level, stream')
    settings = db.execute_query('SELECT * FROM settings WHERE id = 1')

    # All fee receipts with student info
    recent_receipts = db.execute_query('''
        SELECT fr.*, s.first_name, s.last_name, s.reg_number
        FROM fee_receipts fr
        JOIN students s ON fr.student_id = s.id
    ''')

    # All fee templates with class info
    templates = []
    if current_session and current_term:
        templates = db.execute_query('''
            SELECT * FROM fee_templates WHERE session_id = ? AND term_id = ?
        ''', (current_session['id'], current_term['id']))
        for t in templates:
            cls_rows = db.execute_query('SELECT * FROM classes WHERE id = ?', (t['class_id'],))
            t['class_name'] = cls_rows[0]['name'] if cls_rows else '—'

    return render_template('fees/index.html',
                           sessions=sessions,
                           classes=classes,
                           current_session=current_session,
                           current_term=current_term,
                           recent_receipts=recent_receipts,
                           templates=templates,
                           settings=settings[0] if settings else None)

# ─────────────────────────────────────────────────────────────────────────────
# API – students list (filtered by class)
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/api/students')
def api_students():
    class_id = request.args.get('class_id', '')
    if class_id:
        students = db.execute_query(
            'SELECT id, first_name, last_name, reg_number, class_id FROM students '
            'WHERE active_status = 1 AND class_id = ? ORDER BY last_name',
            (class_id,)
        )
    else:
        students = db.execute_query(
            'SELECT id, first_name, last_name, reg_number, class_id FROM students '
            'WHERE active_status = 1 ORDER BY last_name'
        )
    return jsonify(students)

# ─────────────────────────────────────────────────────────────────────────────
# API – terms for a session
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/api/terms/<int:session_id>')
def api_terms(session_id):
    terms = db.execute_query('SELECT * FROM terms WHERE session_id = ?', (session_id,))
    return jsonify(terms)

# ─────────────────────────────────────────────────────────────────────────────
# API – get fee template for a class/session/term
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/api/template')
def api_template():
    class_id  = request.args.get('class_id')
    session_id = request.args.get('session_id')
    term_id    = request.args.get('term_id')
    if not all([class_id, session_id, term_id]):
        return jsonify(None)
    rows = db.execute_query(
        'SELECT * FROM fee_templates WHERE class_id = ? AND session_id = ? AND term_id = ?',
        (class_id, session_id, term_id)
    )
    if rows:
        row = rows[0]
        row['items'] = json.loads(row.get('items') or '[]')
        return jsonify(row)
    return jsonify(None)

# ─────────────────────────────────────────────────────────────────────────────
# SAVE – bulk class fee template
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/template/save', methods=['POST'])
def save_template():
    data = request.json
    class_id   = data.get('class_id')
    session_id = data.get('session_id')
    term_id    = data.get('term_id')
    items      = data.get('items', [])
    total      = sum(float(i.get('amt', 0)) for i in items)

    if not all([class_id, session_id, term_id, items]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    try:
        db.execute_update(
            'INSERT OR REPLACE INTO fee_templates (class_id, session_id, term_id, items, total_amount) VALUES (?,?,?,?,?)',
            (class_id, session_id, term_id, json.dumps(items), total)
        )
        return jsonify({'success': True, 'total': total})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
# SAVE – individual student receipt
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/save', methods=['POST'])
def save_receipt():
    data       = request.json
    student_id = data.get('student_id')
    session_id = data.get('session_id')
    term_id    = data.get('term_id')
    amount_paid = data.get('amount_paid')
    description = data.get('description', '[]')

    if not all([student_id, session_id, term_id, amount_paid]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    try:
        date_str = datetime.now().strftime('%Y%m')
        receipt_number = f"RCP-{date_str}-{str(uuid.uuid4().hex)[:6].upper()}"
        db.execute_update(
            'INSERT INTO fee_receipts (student_id, session_id, term_id, receipt_number, amount_paid, description) VALUES (?,?,?,?,?,?)',
            (student_id, session_id, term_id, receipt_number, amount_paid, description)
        )
        return jsonify({'success': True, 'receipt_number': receipt_number})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
# RECEIPT VIEW (printable)
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/receipt/<receipt_number>')
def view_receipt(receipt_number):
    receipts = db.execute_query('''
        SELECT fr.*, s.first_name, s.last_name, s.reg_number, s.class_id
        FROM fee_receipts fr JOIN students s ON fr.student_id = s.id
        WHERE fr.receipt_number = ?
    ''', (receipt_number,))
    if not receipts:
        return "Receipt not found", 404
    receipt = receipts[0]
    session_info = db.execute_query('SELECT name FROM sessions WHERE id = ?', (receipt['session_id'],))
    term_info    = db.execute_query('SELECT term_number FROM terms WHERE id = ?', (receipt['term_id'],))
    settings     = db.execute_query('SELECT * FROM settings WHERE id = 1')

    # Get class fee template to compute outstanding balance
    template_rows = db.execute_query(
        'SELECT * FROM fee_templates WHERE class_id = ? AND session_id = ? AND term_id = ?',
        (receipt['class_id'], receipt['session_id'], receipt['term_id'])
    )
    template = template_rows[0] if template_rows else None
    template_total = float(template['total_amount']) if template else 0

    # Sum previous payments for this student this term
    all_receipts = db.execute_query('''
        SELECT fr.*, s.first_name, s.last_name, s.reg_number
        FROM fee_receipts fr JOIN students s ON fr.student_id = s.id
        WHERE fr.student_id = ? AND fr.session_id = ? AND fr.term_id = ?
    ''', (receipt['student_id'], receipt['session_id'], receipt['term_id']))
    total_paid = sum(float(r.get('amount_paid', 0)) for r in all_receipts)
    balance = max(0, template_total - total_paid)

    try:
        items = json.loads(receipt.get('description') or '[]')
    except (json.JSONDecodeError, TypeError):
        items = []

    return render_template('fees/receipt.html',
                           receipt=receipt,
                           items=items,
                           session=session_info[0] if session_info else None,
                           term=term_info[0] if term_info else None,
                           settings=settings[0] if settings else None,
                           template_total=template_total,
                           total_paid=total_paid,
                           balance=balance,
                           date_issued=receipt.get('payment_date', datetime.now().date()))

# ─────────────────────────────────────────────────────────────────────────────
# LOGO UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/settings/upload-logo', methods=['POST'])
def upload_logo():
    if 'logo' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    file = request.files['logo']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    allowed = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        return jsonify({'success': False, 'message': 'File type not allowed'}), 400
    
    filename = f"school_logo{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    db.execute_update('UPDATE settings SET logo_path = ? WHERE id = 1', (filename,))
    return jsonify({'success': True, 'filename': filename})
