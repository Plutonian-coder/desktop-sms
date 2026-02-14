from src.database.db_manager import DatabaseManager

db = DatabaseManager()
class_id = 1

print(f"Testing Join Query for Class ID {class_id}...")
# This is the exact query from scores.py
query = '''
        SELECT s.id, s.name, s.code 
        FROM subjects s
        JOIN class_subjects cs ON s.id = cs.subject_id
        WHERE cs.class_id = ?
        ORDER BY cs.display_order, s.name
    '''

res = db.execute_query(query, (class_id,))
print(f"Results: {res}")

# Test the SDK call directly
print("\nTesting SDK directly:")
try:
    res_sdk = db.supabase.table('class_subjects').select('subject_id, subjects(id, name, code)').eq('class_id', class_id).execute()
    print(f"SDK Raw Data: {res_sdk.data}")
except Exception as e:
    print(f"SDK Error: {e}")
