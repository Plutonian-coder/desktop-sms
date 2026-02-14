from src.database.db_manager import DatabaseManager

db = DatabaseManager()

print("Listing all students in Supabase:")
try:
    res = db.supabase.table('students').select('*, classes(name)').execute()
    students = res.data
    print(f"Total students found: {len(students)}")
    for s in students:
        print(f"ID: {s['id']}, Reg: {s['reg_number']}, Name: {s['first_name']} {s['last_name']}, Class: {s.get('classes', {}).get('name')}, Active: {s['active_status']}")
        
    print("\nListing all classes in Supabase:")
    res_cls = db.supabase.table('classes').select('*').execute()
    for c in res_cls.data:
        print(f"ID: {c['id']}, Name: {c['name']}")

except Exception as e:
    print(f"Error: {e}")
