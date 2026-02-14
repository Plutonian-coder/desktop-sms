from src.database.db_manager import DatabaseManager

db = DatabaseManager()

print("--- CLASSES ---")
classes = db.supabase.table('classes').select('*').execute().data
for c in classes:
    print(c)

print("\n--- SUBJECTS ---")
subjects = db.supabase.table('subjects').select('*').execute().data
for s in subjects:
    print(s)

print("\n--- CLASS_SUBJECTS ---")
cs = db.supabase.table('class_subjects').select('*').execute().data
for mapping in cs:
    print(mapping)
