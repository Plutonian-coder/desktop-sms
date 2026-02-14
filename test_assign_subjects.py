from src.database.db_manager import DatabaseManager

db = DatabaseManager()

# Class JSS 1A ID is 1 (based on check_data.py)
# Subjects: Mathematics (ID 1?), English (ID 2?) - let's find them
subjects = db.supabase.table('subjects').select('*').execute().data
class_id = 1

print(f"Assigning subjects to class {class_id}...")

for sub in subjects:
    if sub['name'] in ['Mathematics', 'English Language', 'Basic Science']:
        print(f"Assigning {sub['name']} (ID {sub['id']})")
        # INSERT INTO class_subjects
        db.execute_update('INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)', (class_id, sub['id']))

print("Done. Verification:")
assigned = db.execute_query('SELECT s.* FROM subjects s JOIN class_subjects cs ON s.id = cs.subject_id WHERE cs.class_id = ?', (class_id,))
for a in assigned:
    print(f"- {a['name']}")
