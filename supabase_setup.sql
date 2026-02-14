-- Yabatech JSS Management System - Supabase Schema (PostgreSQL)

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    school_name TEXT NOT NULL,
    address TEXT,
    logo_path TEXT,
    current_session_id INTEGER,
    current_term_id INTEGER
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    start_date DATE,
    end_date DATE
);

-- Terms table
CREATE TABLE IF NOT EXISTS terms (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_number INTEGER NOT NULL,
    resumption_date DATE,
    vacation_date DATE,
    UNIQUE(session_id, term_number)
);

-- Classes table
CREATE TABLE IF NOT EXISTS classes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    level INTEGER NOT NULL,
    stream TEXT,
    capacity INTEGER DEFAULT 40
);

-- Subjects table
CREATE TABLE IF NOT EXISTS subjects (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    code TEXT
);

-- Class-Subject mapping
CREATE TABLE IF NOT EXISTS class_subjects (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id),
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    display_order INTEGER DEFAULT 0,
    UNIQUE(class_id, subject_id)
);

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    reg_number TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT NOT NULL,
    dob DATE,
    class_id INTEGER REFERENCES classes(id),
    parent_name TEXT,
    parent_phone TEXT,
    parent_address TEXT,
    date_enrolled DATE DEFAULT CURRENT_DATE,
    active_status INTEGER DEFAULT 1
);

-- Scores table
CREATE TABLE IF NOT EXISTS scores (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    ca_score NUMERIC DEFAULT 0,
    exam_score NUMERIC DEFAULT 0,
    total NUMERIC DEFAULT 0,
    grade TEXT,
    position INTEGER,
    class_highest NUMERIC,
    class_lowest NUMERIC,
    class_average NUMERIC,
    UNIQUE(student_id, subject_id, session_id, term_id)
);

-- Attendance table
CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    times_present INTEGER DEFAULT 0,
    times_absent INTEGER DEFAULT 0,
    UNIQUE(student_id, session_id, term_id)
);

-- Psychomotor ratings
CREATE TABLE IF NOT EXISTS psychomotor_ratings (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    category TEXT NOT NULL,
    rating INTEGER DEFAULT 1
);

-- Affective ratings
CREATE TABLE IF NOT EXISTS affective_ratings (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    category TEXT NOT NULL,
    rating INTEGER DEFAULT 1
);

-- Remarks table
CREATE TABLE IF NOT EXISTS remarks (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    teacher_remark TEXT,
    principal_remark TEXT,
    UNIQUE(student_id, session_id, term_id)
);

-- Term Results table (Overall Stats)
CREATE TABLE IF NOT EXISTS term_results (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    term_id INTEGER NOT NULL REFERENCES terms(id),
    class_id INTEGER NOT NULL REFERENCES classes(id),
    total_score NUMERIC DEFAULT 0,
    average_score NUMERIC DEFAULT 0,
    position INTEGER,
    class_highest_avg NUMERIC,
    class_lowest_avg NUMERIC,
    class_average_avg NUMERIC,
    UNIQUE(student_id, session_id, term_id)
);

-- Default Data
INSERT INTO settings (school_name, address) VALUES ('Yabatech Secondary School', 'Yaba, Lagos, Nigeria') ON CONFLICT DO NOTHING;
INSERT INTO classes (name, level, stream) VALUES 
('JSS 1A', 1, 'A'), ('JSS 1B', 1, 'B'),
('JSS 2A', 2, 'A'), ('JSS 2B', 2, 'B'),
('JSS 3A', 3, 'A'), ('JSS 3B', 3, 'B') ON CONFLICT DO NOTHING;
INSERT INTO subjects (name, code) VALUES 
('Mathematics', 'MTH'), ('English Language', 'ENG'),
('Basic Science', 'SCI'), ('Basic Technology', 'TECH'),
('Social Studies', 'SOS'), ('Civic Education', 'CIV'),
('Cultural & Creative Arts', 'CCA'), ('Agricultural Science', 'AGR'),
('Home Economics', 'HEC'), ('Physical & Health Education', 'PHE'),
('Business Studies', 'BUS'), ('French', 'FRN'), ('Yoruba', 'YOR') ON CONFLICT DO NOTHING;
