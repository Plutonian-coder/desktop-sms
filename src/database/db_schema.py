"""
Embedded SQLite schema — used as a fallback when sqlite_setup.sql
cannot be found (e.g. inside a PyInstaller bundle).
"""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_name TEXT NOT NULL,
    address TEXT,
    logo_path TEXT,
    current_session_id INTEGER,
    current_term_id INTEGER
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    start_date TEXT,
    end_date TEXT
);

CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_number INTEGER NOT NULL,
    resumption_date TEXT,
    vacation_date TEXT,
    UNIQUE(session_id, term_number)
);

CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    level INTEGER NOT NULL,
    stream TEXT,
    capacity INTEGER DEFAULT 40
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    code TEXT
);

CREATE TABLE IF NOT EXISTS class_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES classes(id),
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    display_order INTEGER DEFAULT 0,
    UNIQUE(class_id, subject_id)
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reg_number TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT NOT NULL,
    dob TEXT,
    class_id INTEGER REFERENCES classes(id),
    parent_name TEXT,
    parent_phone TEXT,
    parent_address TEXT,
    date_enrolled TEXT DEFAULT (date('now')),
    active_status INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    ca_score REAL DEFAULT 0,
    exam_score REAL DEFAULT 0,
    total REAL DEFAULT 0,
    grade TEXT,
    position INTEGER,
    class_highest REAL,
    class_lowest REAL,
    class_average REAL,
    UNIQUE(student_id, subject_id, session_id, term_id)
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    times_present INTEGER DEFAULT 0,
    times_absent INTEGER DEFAULT 0,
    UNIQUE(student_id, session_id, term_id)
);

CREATE TABLE IF NOT EXISTS psychomotor_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    category TEXT NOT NULL,
    rating INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS affective_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    category TEXT NOT NULL,
    rating INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS remarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    teacher_remark TEXT,
    principal_remark TEXT,
    UNIQUE(student_id, session_id, term_id)
);

CREATE TABLE IF NOT EXISTS term_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    class_id INTEGER NOT NULL REFERENCES classes(id),
    total_score REAL DEFAULT 0,
    average_score REAL DEFAULT 0,
    position INTEGER,
    class_highest_avg REAL,
    class_lowest_avg REAL,
    class_average_avg REAL,
    UNIQUE(student_id, session_id, term_id)
);

CREATE TABLE IF NOT EXISTS fee_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    receipt_number TEXT NOT NULL UNIQUE,
    amount_paid REAL NOT NULL,
    description TEXT,
    payment_date TEXT DEFAULT (date('now')),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS fee_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES classes(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    items TEXT NOT NULL,
    total_amount REAL NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(class_id, session_id, term_id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'admin',
    security_question TEXT,
    security_answer_hash TEXT
);

INSERT OR IGNORE INTO settings (id, school_name, address)
    VALUES (1, 'Yabatech Secondary School', 'Yaba, Lagos, Nigeria');

INSERT OR IGNORE INTO classes (name, level, stream) VALUES
    ('JSS 1A', 1, 'A'), ('JSS 1B', 1, 'B'),
    ('JSS 2A', 2, 'A'), ('JSS 2B', 2, 'B'),
    ('JSS 3A', 3, 'A'), ('JSS 3B', 3, 'B');

INSERT OR IGNORE INTO subjects (name, code) VALUES
    ('Mathematics', 'MTH'),
    ('English Language', 'ENG'),
    ('Basic Science', 'SCI'),
    ('Basic Technology', 'TECH'),
    ('Social Studies', 'SOS'),
    ('Civic Education', 'CIV'),
    ('Cultural & Creative Arts', 'CCA'),
    ('Agricultural Science', 'AGR'),
    ('Home Economics', 'HEC'),
    ('Physical & Health Education', 'PHE'),
    ('Business Studies', 'BUS'),
    ('French', 'FRN'),
    ('Yoruba', 'YOR');
"""
