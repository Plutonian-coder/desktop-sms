from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import os
from database.db_manager import DatabaseManager

class PDFGenerator:
    """
    Generates PDF Report Cards matching the school report card layout.
    Uses score data entered via Score Entry for academic results.
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.styles = getSampleStyleSheet()
        self.define_custom_styles()

    def define_custom_styles(self):
        # Colors matching the report card design
        self.primary_color = colors.Color(0.1, 0.2, 0.4)  # Deep Blue
        self.accent_color = colors.Color(0.6, 0.1, 0.1)   # Deep Red

        if 'SchoolName' not in self.styles:
            self.styles.add(ParagraphStyle(name='SchoolName', fontSize=22, leading=26, alignment=TA_CENTER, fontName='Times-Bold', textColor=self.primary_color))
        else:
            self.styles['SchoolName'].fontSize = 22
            self.styles['SchoolName'].fontName = 'Times-Bold'
            self.styles['SchoolName'].textColor = self.primary_color

        if 'SchoolAddress' not in self.styles:
            self.styles.add(ParagraphStyle(name='SchoolAddress', fontSize=9, leading=11, alignment=TA_CENTER, fontName='Times-Roman'))

        if 'ReportTitle' not in self.styles:
            self.styles.add(ParagraphStyle(name='ReportTitle', fontSize=12, leading=14, alignment=TA_CENTER, fontName='Times-Bold', spaceBefore=0, spaceAfter=0, textColor=colors.white))

        if 'Label' not in self.styles:
            self.styles.add(ParagraphStyle(name='Label', fontSize=9, leading=11, fontName='Times-Bold'))

        if 'Value' not in self.styles:
             self.styles.add(ParagraphStyle(name='Value', fontSize=9, leading=11, fontName='Times-Roman'))

        self.card_header_bg = self.primary_color
        self.table_header_bg = colors.HexColor('#F2F2F2')

    def generate_class_reports(self, class_id: int, session_id: int, term_id: int, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        students = self.db.execute_query('SELECT * FROM students WHERE class_id = ? AND active_status = 1', (class_id,))

        generated_files = []
        for student in students:
            safe_reg = student['reg_number'].replace('/', '_').replace('\\', '_')
            filename = f"Report_{safe_reg}_{student['last_name']}.pdf"
            filepath = os.path.join(output_dir, filename)
            if self.generate_student_report(student['id'], session_id, term_id, filepath):
                generated_files.append(filepath)
        return generated_files

    def generate_student_report(self, student_id: int, session_id: int, term_id: int, filepath: str):
        # 1. Fetch Data
        student = self.db.execute_query('SELECT * FROM students WHERE id = ?', (student_id,))[0]
        term_result_rows = self.db.execute_query('SELECT * FROM term_results WHERE student_id=? AND session_id=? AND term_id=?', (student_id, session_id, term_id))
        term_result = term_result_rows[0] if term_result_rows else {'total_score': 0, 'average_score': 0, 'position': '-', 'class_average_avg': 0}

        scores = self.db.execute_query('''
            SELECT Sc.*, Su.name as subject_name
            FROM scores Sc
            JOIN subjects Su ON Sc.subject_id = Su.id
            WHERE Sc.student_id = ? AND Sc.session_id = ? AND Sc.term_id = ?
            ORDER BY Su.name
        ''', (student_id, session_id, term_id))

        class_info = self.db.execute_query('SELECT * FROM classes WHERE id = ?', (student['class_id'],))[0]
        self.db.execute_query('SELECT * FROM sessions WHERE id = ?', (session_id,))
        term_info = self.db.execute_query('SELECT * FROM terms WHERE id = ?', (term_id,))[0]
        settings = self.db.execute_query('SELECT * FROM settings WHERE id = 1')[0]

        remarks_data = self.db.execute_query('SELECT * FROM remarks WHERE student_id=? AND session_id=? AND term_id=?', (student_id, session_id, term_id))
        remarks = remarks_data[0] if remarks_data else {}

        affective_data = self.db.execute_query('SELECT * FROM affective_ratings WHERE student_id=? AND session_id=? AND term_id=?', (student_id, session_id, term_id))
        skills = {item['category']: item['rating'] for item in affective_data}

        attendance_data = self.db.execute_query('SELECT * FROM attendance WHERE student_id=? AND session_id=? AND term_id=?', (student_id, session_id, term_id))
        attendance = attendance_data[0] if attendance_data else {}

        # 2. Setup Document
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
        elements = []

        # Styles Helpers
        normal_small = ParagraphStyle('NS', parent=self.styles['Normal'], fontSize=9, fontName='Times-Roman')
        bold_small = ParagraphStyle('BS', parent=self.styles['Normal'], fontSize=9, fontName='Times-Bold')

        # --- HEADER SECTION ---
        school_name_p = Paragraph(settings['school_name'], self.styles['SchoolName'])
        address_p = Paragraph(f"{settings.get('address', '')}<br/>{settings.get('website', '')}", self.styles['SchoolAddress'])

        logo_path = settings['logo_path']
        passport_path = student.get('passport_path')

        logo_img = Image(logo_path, width=1.1*inch, height=1.1*inch) if logo_path and os.path.exists(logo_path) else Spacer(1,1)
        passport_img = Image(passport_path, width=1.0*inch, height=1.0*inch) if passport_path and os.path.exists(passport_path) else Spacer(1,1)

        header_data = [[logo_img, [school_name_p, Spacer(1,4), address_p], passport_img]]
        t_header = Table(header_data, colWidths=[1.5*inch, 4.3*inch, 1.5*inch])
        t_header.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 15))

        # --- STUDENT INFO BOX ---
        import datetime
        date_str = datetime.datetime.now().strftime("%d/%m/%Y")
        term_str = f"Term {term_info['term_number']}"

        info_data = [
            [
                Paragraph(f"<b>Name:</b> {student['last_name'].upper()} {student['first_name']}", normal_small),
                Paragraph(f"<b>Date:</b> {date_str}", normal_small)
            ],
            [
                Paragraph(f"<b>Student Term:</b> {term_str}", normal_small),
                Paragraph(f"<b>Class:</b> {class_info['name']}", normal_small)
            ],
            [
                Paragraph(f"<b>Gender:</b> {student['gender']}", normal_small),
                Paragraph(f"<b>Position:</b> {term_result['position']}", normal_small)
            ]
        ]

        t_info = Table(info_data, colWidths=[3.6*inch, 3.6*inch])
        t_info.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTNAME', (0,0), (-1,-1), 'Times-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BACKGROUND', (0,0), (-1,-1), colors.Color(0.95, 0.95, 0.9)),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_info)
        elements.append(Spacer(1, 10))

        # --- REPORT TITLE BAR ---
        title_table = Table([[Paragraph("ACADEMIC REPORT", self.styles['ReportTitle'])]], colWidths=[7.3*inch])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), self.accent_color),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(title_table)

        # --- ACADEMIC TABLE ---
        # Columns: Subject | Score | Grade | Teacher Comment
        headers = ['SUBJECT', 'SCORE', 'GRADE', 'TEACHER\'S COMMENT']
        table_data = [headers]

        def get_comment(grade):
            if not grade:
                return "-"
            letter = grade[0] if grade else ''
            comments = {
                'A': "Excellent performance.",
                'B': "Very good result.",
                'C': "Good attempt.",
                'D': "Fair performance.",
                'E': "Keep trying.",
                'F': "More effort needed."
            }
            return comments.get(letter, "-")

        for sc in scores:
            comment = get_comment(sc['grade'])
            table_data.append([
                Paragraph(sc['subject_name'], normal_small),
                str(int(sc['total']) if sc['total'] else 0),
                sc['grade'] or '-',
                Paragraph(comment, normal_small)
            ])

        t_acad = Table(table_data, colWidths=[2.5*inch, 1.0*inch, 1.0*inch, 2.8*inch])
        t_acad.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), self.primary_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
            ('ALIGN', (1,0), (2,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F8F8')]),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t_acad)

        # --- GRADES KEY ---
        elements.append(Spacer(1, 5))
        grade_key_data = [['Grades', 'A (70-100)', 'B (60-69)', 'C (50-59)', 'D (45-49)', 'E (40-44)', 'F (0-39)']]
        t_key = Table(grade_key_data, colWidths=[1.0*inch, 1.05*inch, 1.05*inch, 1.05*inch, 1.05*inch, 1.05*inch, 1.05*inch])
        t_key.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('BACKGROUND', (0,0), (0,0), colors.lightgrey),
        ]))
        elements.append(t_key)
        elements.append(Spacer(1, 12))

        # --- BOTTOM SECTION: ATTENDANCE & PSYCHOMOTOR SKILLS ---

        def get_rating_text(val):
            mapping = {1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Very Good', 5: 'Excellent'}
            return mapping.get(int(val), 'Good')

        # 1. Attendance & Behaviour Table
        att_present = attendance.get('times_present', '-')

        att_data = [
            [Paragraph('<b>ATTENDANCE &amp; BEHAVIOUR</b>', bold_small), ''],
            ['Attendance', f"{att_present}" if att_present != '-' else '-'],
            ['Punctuality', get_rating_text(skills.get('punctuality', 3))],
            ['Neatness', get_rating_text(skills.get('neatness', 3))],
            ['Handwriting', get_rating_text(skills.get('handwriting', 3))],
            ['Politeness', get_rating_text(skills.get('politeness', 3))]
        ]

        t_att = Table(att_data, colWidths=[1.5*inch, 1.0*inch])
        t_att.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), self.primary_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,-1), 'Times-Roman'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (1,1), (1,-1), 'CENTER'),
        ]))

        # 2. Psychomotor Skills Table
        psych_data = [
            [Paragraph('<b>PSYCHOMOTOR SKILLS</b>', bold_small), '', '', ''],
            ['Name', 'Rating', 'Name', 'Rating'],
            ['Handwriting', get_rating_text(skills.get('handwriting', 3)), 'Verbal Fluency', get_rating_text(skills.get('attentiveness', 3))],
            ['Games & Sports', get_rating_text(skills.get('sports', 3)), 'Drawing', get_rating_text(skills.get('drawing', 3))],
            ['Handling Tools', get_rating_text(skills.get('tools', 3)), '', ''],
        ]

        t_psych = Table(psych_data, colWidths=[1.2*inch, 0.9*inch, 1.2*inch, 0.9*inch])
        t_psych.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), self.primary_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('SPAN', (0,0), (-1,0)),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#EEEEEE')),
            ('FONTNAME', (0,1), (-1,1), 'Times-Bold'),
            ('FONTNAME', (0,2), (-1,-1), 'Times-Roman'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (1,1), (1,-1), 'CENTER'),
            ('ALIGN', (3,1), (3,-1), 'CENTER'),
        ]))

        # Put side-by-side
        t_bottom = Table([[t_att, Spacer(0.3*inch,0), t_psych]], colWidths=[2.6*inch, 0.3*inch, 4.4*inch])
        t_bottom.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        elements.append(t_bottom)

        elements.append(Spacer(1, 12))

        # --- TEACHER'S COMMENT ---
        teacher_remark = remarks.get('teacher_remark') or '-'
        teacher_box = Table([
            [Paragraph(f"<b>Teacher's Comment:</b> <i>{teacher_remark}</i>", normal_small)]
        ], colWidths=[7.3*inch])
        teacher_box.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(teacher_box)
        elements.append(Spacer(1, 5))

        # --- PRINCIPAL'S REMARK ---
        principal_remark = remarks.get('principal_remark') or '-'
        principal_box = Table([
            [Paragraph(f"<b>Principal's Remark:</b> <i>{principal_remark}</i>", normal_small)]
        ], colWidths=[7.3*inch])
        principal_box.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(principal_box)

        elements.append(Spacer(1, 20))

        # --- FOOTER: SIGNATURES ---
        sig_center_style = ParagraphStyle('SigCenter', alignment=TA_CENTER, fontName='Times-Roman', fontSize=9)

        sig_data = [[
            Paragraph("________________________<br/><b>Class Teacher</b>", sig_center_style),
            Paragraph("________________________<br/><b>Principal's Signature</b>", sig_center_style),
            Paragraph("<br/><b>School Stamp</b>", sig_center_style),
        ]]

        t_sig = Table(sig_data, colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
        t_sig.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ]))
        elements.append(t_sig)

        doc.build(elements)
        return True
