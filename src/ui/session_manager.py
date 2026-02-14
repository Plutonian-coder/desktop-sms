"""
Session and Term Management
Redesigned with a modern look and pop-out form
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from database.db_manager import DatabaseManager


class SessionDialog(QDialog):
    """Dialog for creating new academic session and term"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Academic Session/Term")
        self.setFixedWidth(400)
        self.db = DatabaseManager()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.session_name = QLineEdit()
        self.session_name.setPlaceholderText("e.g. 2023/2024")
        
        self.term_number = QComboBox()
        self.term_number.addItems(["1", "2", "3"])
        
        self.resumption_date = QDateEdit()
        self.resumption_date.setCalendarPopup(True)
        self.resumption_date.setDate(QDate.currentDate())
        
        self.vacation_date = QDateEdit()
        self.vacation_date.setCalendarPopup(True)
        self.vacation_date.setDate(QDate.currentDate().addMonths(3))
        
        form_layout.addRow("Academic Session:", self.session_name)
        form_layout.addRow("Term Number:", self.term_number)
        form_layout.addRow("Resumption Date:", self.resumption_date)
        form_layout.addRow("Vacation Date:", self.vacation_date)
        
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Session/Term")
        self.save_btn.setFixedHeight(40)
        self.save_btn.setStyleSheet("background: #333333; color: white; font-weight: bold;")
        self.save_btn.clicked.connect(self.save)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)

    def save(self):
        name = self.session_name.text().strip()
        term_num = int(self.term_number.currentText())
        res_date = self.resumption_date.date().toString(Qt.ISODate)
        vac_date = self.vacation_date.date().toString(Qt.ISODate)
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter academic session name.")
            return
            
        try:
            # Check if session exists or create it
            sessions = self.db.execute_query("SELECT id FROM sessions WHERE name = ?", (name,))
            if sessions:
                session_id = sessions[0]['id']
            else:
                session_id = self.db.execute_update(
                    "INSERT INTO sessions (name) VALUES (?)", (name,)
                )
            
            # Create term
            self.db.execute_update(
                "INSERT INTO terms (session_id, term_number, resumption_date, vacation_date) VALUES (?, ?, ?, ?)",
                (session_id, term_num, res_date, vac_date)
            )
            
            # If this is the first session/term, set as current
            settings = self.db.execute_query("SELECT current_session_id FROM settings WHERE id = 1")
            if settings and not settings[0]['current_session_id']:
                term = self.db.execute_query(
                    "SELECT id FROM terms WHERE session_id = ? AND term_number = ?", 
                    (session_id, term_num)
                )
                self.db.execute_update(
                    "UPDATE settings SET current_session_id = ?, current_term_id = ? WHERE id = 1",
                    (session_id, term[0]['id'])
                )
                
            QMessageBox.information(self, "Success", "Session and Term successfully added.")
            self.accept()
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                QMessageBox.critical(self, "Error", f"Term {term_num} for session {name} already exists!")
            else:
                QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")


class SessionManager(QWidget):
    """Redesigned Session Manager View"""
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Academic Sessions & Terms")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.add_btn = QPushButton(" + New Session/Term")
        self.add_btn.setFixedSize(180, 45)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: #333333;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #444444;
            }
        """)
        self.add_btn.clicked.connect(self.show_add_dialog)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Academic Session", "Term", "Resumption Date", "Vacation Date"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.table)
        
        # Load initial data
        self.load_data()
        
    def load_data(self):
        """Fetch and display session/term data"""
        query = """
            SELECT t.id, s.name, t.term_number, t.resumption_date, t.vacation_date 
            FROM terms t
            JOIN sessions s ON t.session_id = s.id
            ORDER BY s.name DESC, t.term_number DESC
        """
        rows = self.db.execute_query(query)
        
        self.table.setRowCount(0)
        for row_idx, row in enumerate(rows):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row['name']))
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"Term {row['term_number']}"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row['resumption_date']))
            self.table.setItem(row_idx, 4, QTableWidgetItem(row['vacation_date']))
            
    def show_add_dialog(self):
        dialog = SessionDialog(self)
        if dialog.exec():
            self.load_data()
