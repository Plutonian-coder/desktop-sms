"""
Score Entry Module - The Core Grid
Excel-like interface for entering student scores
"""
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from database.db_manager import DatabaseManager
from logic.grading import calculate_grade


class ScoreEntry(QWidget):
    """Score entry screen with spreadsheet-like grid"""
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.current_class_id = None
        self.current_subject_id = None
        self.current_session_id = None
        self.current_term_id = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Score Entry Grid")
        header.setFont(QFont("Arial", 22, QFont.Bold))
        header.setStyleSheet("color: #000000;")
        layout.addWidget(header)
        
        # Score Table (create BEFORE filter panel)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Student Name", "CA Score (30)", "Exam Score (70)", 
            "Total (100)", "Grade", "Remarks"
        ])
        
        # Configure table
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        
        # Filter Panel (create AFTER table)
        filter_panel = self.create_filter_panel()
        layout.addWidget(filter_panel)
        layout.addWidget(self.table)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_save = QPushButton("Save Scores")
        btn_save.setFixedHeight(40)
        btn_save.setMinimumWidth(150)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #45A049;
            }
        """)
        btn_save.clicked.connect(self.save_scores)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
    
    def create_filter_panel(self) -> QFrame:
        """Create the filter panel"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        panel.setMaximumHeight(100)
        
        panel_layout = QHBoxLayout(panel)
        panel_layout.setSpacing(15)
        
        # Session dropdown
        panel_layout.addWidget(QLabel("Session:"))
        self.session_combo = QComboBox()
        self.session_combo.currentIndexChanged.connect(self.on_session_changed)
        panel_layout.addWidget(self.session_combo)
        
        # Term dropdown
        panel_layout.addWidget(QLabel("Term:"))
        self.term_combo = QComboBox()
        self.term_combo.currentIndexChanged.connect(self.load_table_data)
        panel_layout.addWidget(self.term_combo)
        
        # Class dropdown
        panel_layout.addWidget(QLabel("Class:"))
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.load_table_data)
        panel_layout.addWidget(self.class_combo)
        
        # Subject dropdown
        panel_layout.addWidget(QLabel("Subject:"))
        self.subject_combo = QComboBox()
        self.subject_combo.currentIndexChanged.connect(self.load_table_data)
        panel_layout.addWidget(self.subject_combo)
        
        panel_layout.addStretch()
        
        # Load initial data
        self.load_sessions()
        self.load_classes()
        self.load_subjects()
        
        return panel
    
    def load_sessions(self):
        """Load sessions into dropdown"""
        sessions = self.db.execute_query('SELECT * FROM sessions ORDER BY name DESC')
        self.session_combo.clear()
        self.session_combo.addItem("Select Session", None)
        for session in sessions:
            self.session_combo.addItem(session['name'], session['id'])
    
    def on_session_changed(self):
        """Handle session change"""
        session_id = self.session_combo.currentData()
        self.term_combo.clear()
        self.term_combo.addItem("Select Term", None)
        
        if session_id:
            terms = self.db.execute_query(
                'SELECT * FROM terms WHERE session_id = ? ORDER BY term_number',
                (session_id,)
            )
            for term in terms:
                self.term_combo.addItem(f"Term {term['term_number']}", term['id'])
        
        self.load_table_data()
    
    def load_classes(self):
        """Load classes into dropdown"""
        classes = self.db.execute_query('SELECT * FROM classes ORDER BY level, stream')
        self.class_combo.clear()
        self.class_combo.addItem("Select Class", None)
        for cls in classes:
            self.class_combo.addItem(cls['name'], cls['id'])
    
    def load_subjects(self):
        """Load subjects into dropdown"""
        subjects = self.db.execute_query('SELECT * FROM subjects ORDER BY name')
        self.subject_combo.clear()
        self.subject_combo.addItem("Select Subject", None)
        for subject in subjects:
            self.subject_combo.addItem(subject['name'], subject['id'])
    
    def load_table_data(self):
        """Load students and scores into the table"""
        self.current_class_id = self.class_combo.currentData()
        self.current_subject_id = self.subject_combo.currentData()
        self.current_session_id = self.session_combo.currentData()
        self.current_term_id = self.term_combo.currentData()
        
        if not all([self.current_class_id, self.current_subject_id, 
                    self.current_session_id, self.current_term_id]):
            self.table.setRowCount(0)
            return
        
        # Get students in the class
        students = self.db.execute_query('''
            SELECT id, first_name, last_name 
            FROM students 
            WHERE class_id = ? AND active_status = 1
            ORDER BY last_name, first_name
        ''', (self.current_class_id,))
        
        self.table.setRowCount(len(students))
        
        for row, student in enumerate(students):
            student_id = student['id']
            student_name = f"{student['first_name']} {student['last_name']}"
            
            # Get existing scores
            score = self.db.execute_query('''
                SELECT * FROM scores 
                WHERE student_id = ? AND subject_id = ? 
                AND session_id = ? AND term_id = ?
            ''', (student_id, self.current_subject_id, 
                  self.current_session_id, self.current_term_id))
            
            ca_score = score[0]['ca_score'] if score else 0
            exam_score = score[0]['exam_score'] if score else 0
            total = ca_score + exam_score
            grade = calculate_grade(total)
            
            # Student name (read-only)
            name_item = QTableWidgetItem(student_name)
            name_item.setFlags(Qt.ItemIsEnabled)
            name_item.setBackground(QColor("#F5F5F5"))
            name_item.setData(Qt.UserRole, student_id)
            self.table.setItem(row, 0, name_item)
            
            # CA Score (editable)
            ca_item = QTableWidgetItem(str(int(ca_score)))
            self.table.setItem(row, 1, ca_item)
            
            # Exam Score (editable)
            exam_item = QTableWidgetItem(str(int(exam_score)))
            self.table.setItem(row, 2, exam_item)
            
            # Total (auto-calculated, read-only)
            total_item = QTableWidgetItem(str(int(total)))
            total_item.setFlags(Qt.ItemIsEnabled)
            total_item.setBackground(QColor("#FFF9C4"))
            self.table.setItem(row, 3, total_item)
            
            # Grade (auto-calculated, read-only)
            grade_item = QTableWidgetItem(grade)
            grade_item.setFlags(Qt.ItemIsEnabled)
            grade_item.setBackground(QColor("#FFF9C4"))
            self.table.setItem(row, 4, grade_item)
            
            # Remarks (read-only for now)
            remarks_item = QTableWidgetItem("")
            remarks_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 5, remarks_item)
        
        # Connect cell changed signal
        self.table.cellChanged.connect(self.on_cell_changed)
    
    def on_cell_changed(self, row: int, column: int):
        """Handle cell value changes"""
        if column not in [1, 2]:  # Only CA and Exam columns
            return
        
        try:
            ca_item = self.table.item(row, 1)
            exam_item = self.table.item(row, 2)
            
            ca_score = float(ca_item.text()) if ca_item and ca_item.text() else 0
            exam_score = float(exam_item.text()) if exam_item and exam_item.text() else 0
            
            # Validate
            if ca_score > 30 or ca_score < 0:
                QMessageBox.warning(self, "Invalid Score", "CA score must be between 0 and 30")
                ca_item.setText("0")
                return
            
            if exam_score > 70 or exam_score < 0:
                QMessageBox.warning(self, "Invalid Score", "Exam score must be between 0 and 70")
                exam_item.setText("0")
                return
            
            # Update total and grade
            total = ca_score + exam_score
            grade = calculate_grade(total)
            
            self.table.item(row, 3).setText(str(int(total)))
            self.table.item(row, 4).setText(grade)
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers only")
    
    def save_scores(self):
        """Save all scores to database"""
        if not all([self.current_class_id, self.current_subject_id,
                    self.current_session_id, self.current_term_id]):
            QMessageBox.warning(self, "Missing Selection", 
                                "Please select Session, Term, Class, and Subject")
            return
        
        try:
            for row in range(self.table.rowCount()):
                student_id = self.table.item(row, 0).data(Qt.UserRole)
                ca_score = float(self.table.item(row, 1).text() or 0)
                exam_score = float(self.table.item(row, 2).text() or 0)
                total = ca_score + exam_score
                grade = calculate_grade(total)
                
                # Insert or update score
                self.db.execute_update('''
                    INSERT OR REPLACE INTO scores 
                    (student_id, subject_id, session_id, term_id, ca_score, exam_score, total, grade)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (student_id, self.current_subject_id, self.current_session_id,
                      self.current_term_id, ca_score, exam_score, total, grade))
            
            QMessageBox.information(self, "Success", "Scores saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save scores: {str(e)}")
