# Technical Documentation: Report Generation Module

## 1. Overview
The **Report Generation Module** is a core component of the Prograde Pulsar (YabaTech Desktop) application, responsible for compiling academic performance scores, attendance records, skills ratings, and administrative remarks into a printable PDF report card for each student.

The module operates on a "Select-edit-Generate" workflow, where the user reviews auto-calculated academic data, enriches it with qualitative data (skills/remarks), and triggers the final PDF production.

## 2. Technology Stack
- **Backend API**: Python (Flask)
- **Database**: SQLite (managed via `DatabaseManager`)
- **PDF Engine**: ReportLab (Python library for programmatic PDF creation)
- **Frontend**: HTML5, Vanilla JavaScript, CSS (Nano Banana Pro design system)
- **Communication**: RESTful JSON API using `fetch`

## 3. Architecture

### 3.1 Backend Controller (`app/routes/reports.py`)
The Flask blueprint `reports` handles data retrieval and saving.
- **Data fetching**: Aggregates data from multiple tables (`scores`, `attendance`, `remarks`, `term_results`) to populate the frontend editor.
- **Persistence**: Upserts qualitative data (Skills and Remarks) into the database.
- **Generation**: Triggers the `PDFGenerator` class to create the physical file.

### 3.2 PDF Engine (`src/reports/pdf_generator.py`)
Uses `reportlab.platypus` to construct a document from flowables (Tables, Paragraphs, Images).
- **Styling**: Defines a strictly typed custom stylesheet (`define_custom_styles`) to match the "Greenwood Academy" aesthetic.
- **Layout**: Features a tabular layout with:
  - Header (School Logo, Name, Student Passport).
  - Student Information Grid.
  - Academic Scores Table (Subject, Score, Grade, Comment).
  - Bottom Section (Split view: Attendance & Psychomotor Skills).
  - Remarks & Signatures Footer.

### 3.3 Frontend Logic (`app/static/js/reports.js`)
- **State Management**: Tracks selected Session, Term, Class, and active Student ID.
- **Dynamic Loading**: Fetches student roster and report data asynchronously without page reloads.
- **Interactivity**: 
  - **Star Ratings**: Interactive 1-5 star UI for psychomotor skills.
  - **Quick Chips**: One-click predefined templates for remarks.
  - **Live Preview**: The "Report Card" tab shows a HTML approximation of the final PDF.

## 4. Database Schema
The module relies on the following relational tables:

### `scores` (Academic Data)
Core academic performance data.
- `student_id`: FK to Students
- `subject_id`: FK to Subjects
- `ca_score`, `exam_score`: Raw components
- `total`: Computed total (CA + Exam)
- `grade`: Letter grade (A-F)

### `affective_ratings` (Skills)
Stores rating (1-5) for non-academic traits.
- `category`: Skill name (e.g., 'neatness', 'sports', 'handwriting')
- `rating`: Integer (1-5)

### `remarks` (Qualitative)
Stores text comments from staff.
- `teacher_remark`: Text
- `principal_remark`: Text

### `term_results` (Aggregation)
Stores computed positions and averages.
- `position`: Class ranking
- `average_score`: Student's average
- `class_average_avg`: Class-wide benchmark

## 5. API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reports/` | GET | Renders the main interface (index.html). |
| `/reports/api/student_report_data` | GET | Returns JSON payload with full student profile, scores, and existing remarks. |
| `/reports/api/save_report_data` | POST | Saves Skills (Star ratings) and Remarks to DB. |
| `/reports/api/generate_single_report` | POST | Generates the PDF file on disk and returns the filename. |
| `/reports/download/<filename>` | GET | Serves the generated PDF file (Inline for preview). |

## 6. PDF styling Details
- **Colors**: Deep Blue (`#1a3366`) and Deep Red (`#8b1a1a`) are used as primary accents.
- **Fonts**: 'Times-Bold' for headers and 'Times-Roman' for body text to emulate a formal academic document.
- **Structure**: Uses `Table` flowables heavily for alignment, with precise column widths measured in inches.

