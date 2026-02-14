"""
Subject Management and Class Assignment
Redesigned with modern look and class assignment logic
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox, 
    QMessageBox, QFrame, QTabWidget, QListWidget, QListWidgetItem,
    QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from database.db_manager import DatabaseManager


class SubjectDialog(QDialog):
    """Dialog for creating new subjects"""
    def __init__(self, parent=None, subject_data=None):
        super().__init__(parent)
        self.setWindowTitle("Subject Details")
        self.setFixedWidth(400)
        self.db = DatabaseManager()
        self.subject_id = subject_data['id'] if subject_data else None
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Mathematics")
        if subject_data:
            self.name_input.setText(subject_data['name'])
            
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("e.g. MTH")
        if subject_data:
            self.code_input.setText(subject_data['code'])
            
        form_layout.addRow("Subject Name:", self.name_input)
        form_layout.addRow("Subject Code:", self.code_input)
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Subject")
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
        name = self.name_input.text().strip()
        code = self.code_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter subject name.")
            return
            
        try:
            if self.subject_id:
                self.db.execute_update(
                    "UPDATE subjects SET name = ?, code = ? WHERE id = ?",
                    (name, code, self.subject_id)
                )
            else:
                self.db.execute_update(
                    "INSERT INTO subjects (name, code) VALUES (?, ?)",
                    (name, code)
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")


class AssignSubjectDialog(QDialog):
    """Dialog for assigning multiple subjects to a class"""
    def __init__(self, parent=None, class_id=None, class_name=""):
        super().__init__(parent)
        self.setWindowTitle(f"Assign Subjects to {class_name}")
        self.setMinimumSize(500, 600)
        self.db = DatabaseManager()
        self.class_id = class_id
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        layout.addWidget(QLabel(f"Select subjects to assign to <b>{class_name}</b>:"))
        
        # Search/Filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search subjects...")
        self.search_input.textChanged.connect(self.filter_subjects)
        layout.addWidget(self.search_input)
        
        # List of subjects
        self.subject_list = QListWidget()
        self.subject_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.subject_list.setStyleSheet("QListWidget::item { padding: 8px; border-bottom: 1px solid #EEE; }")
        layout.addWidget(self.subject_list)
        
        # Load subjects and mark already assigned ones
        self.load_subjects()
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Assignments")
        self.save_btn.setFixedHeight(40)
        self.save_btn.setStyleSheet("background: #333333; color: white; font-weight: bold;")
        self.save_btn.clicked.connect(self.save)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def load_subjects(self):
        # Get all subjects
        all_subjects = self.db.execute_query("SELECT id, name, code FROM subjects ORDER BY name ASC")
        
        # Get already assigned subjects for this class
        assigned = self.db.execute_query(
            "SELECT subject_id FROM class_subjects WHERE class_id = ?", (self.class_id,)
        )
        assigned_ids = [r['subject_id'] for r in assigned]
        
        for sub in all_subjects:
            item = QListWidgetItem(f"{sub['name']} ({sub['code']})")
            item.setData(Qt.UserRole, sub['id'])
            self.subject_list.addItem(item)
            if sub['id'] in assigned_ids:
                item.setSelected(True)

    def filter_subjects(self, text):
        for i in range(self.subject_list.count()):
            item = self.subject_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def save(self):
        selected_items = self.subject_list.selectedItems()
        selected_subject_ids = [item.data(Qt.UserRole) for item in selected_items]
        
        try:
            # Delete existing assignments for this class to refresh
            # Or we could do a more complex diff, but this is simpler for manual assignment
            # Requirement: "once subject is assigned... it cannot be created/assigned again except edited"
            self.db.execute_update("DELETE FROM class_subjects WHERE class_id = ?", (self.class_id,))
            
            # Insert new assignments
            for sub_id in selected_subject_ids:
                self.db.execute_update(
                    "INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)",
                    (self.class_id, sub_id)
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save assignments: {str(e)}")


class SubjectManager(QWidget):
    """Redesigned Subject Manager with Class Assignments"""
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
        title_label = QLabel("Subject Management")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.add_subject_btn = QPushButton(" + New Subject")
        self.add_subject_btn.setFixedSize(160, 45)
        self.add_subject_btn.setStyleSheet("""
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
        self.add_subject_btn.clicked.connect(self.show_add_subject_dialog)
        header_layout.addWidget(self.add_subject_btn)
        
        layout.addLayout(header_layout)
        
        # Tabs for Subject List and Class Assignments
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 10px 20px;
                font-weight: bold;
                background: #EEE;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #FDD835;
            }
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                background: white;
            }
        """)
        
        # Tab 1: All Subjects
        self.subject_tab = QWidget()
        sub_layout = QVBoxLayout(self.subject_tab)
        self.subject_table = QTableWidget()
        self.subject_table.setColumnCount(3)
        self.subject_table.setHorizontalHeaderLabels(["ID", "Subject Name", "Subject Code"])
        self.subject_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.subject_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.subject_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.subject_table.itemDoubleClicked.connect(self.edit_subject)
        sub_layout.addWidget(self.subject_table)
        
        # Tab 2: Class Assignments
        self.class_tab = QWidget()
        class_layout = QVBoxLayout(self.class_tab)
        self.class_table = QTableWidget()
        self.class_table.setColumnCount(3)
        self.class_table.setHorizontalHeaderLabels(["Class ID", "Class Name", "Assigned Subjects Count"])
        self.class_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.class_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.class_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.class_table.itemDoubleClicked.connect(self.assign_subjects_to_class)
        class_layout.addWidget(self.class_table)
        
        self.tabs.addTab(self.subject_tab, "Subject List")
        self.tabs.addTab(self.class_tab, "Class Assignments")
        
        layout.addWidget(self.tabs)
        
        self.load_subjects()
        self.load_classes()
        
    def load_subjects(self):
        subjects = self.db.execute_query("SELECT id, name, code FROM subjects ORDER BY name ASC")
        self.subject_table.setRowCount(0)
        for i, sub in enumerate(subjects):
            self.subject_table.insertRow(i)
            self.subject_table.setItem(i, 0, QTableWidgetItem(str(sub['id'])))
            self.subject_table.setItem(i, 1, QTableWidgetItem(sub['name']))
            self.subject_table.setItem(i, 2, QTableWidgetItem(sub['code']))
            
    def load_classes(self):
        classes = self.db.execute_query("""
            SELECT c.id, c.name, COUNT(cs.subject_id) as sub_count
            FROM classes c
            LEFT JOIN class_subjects cs ON c.id = cs.class_id
            GROUP BY c.id
        """)
        self.class_table.setRowCount(0)
        for i, cls in enumerate(classes):
            self.class_table.insertRow(i)
            self.class_table.setItem(i, 0, QTableWidgetItem(str(cls['id'])))
            self.class_table.setItem(i, 1, QTableWidgetItem(cls['name']))
            self.class_table.setItem(i, 2, QTableWidgetItem(str(cls['sub_count'])))
            
    def show_add_subject_dialog(self):
        dialog = SubjectDialog(self)
        if dialog.exec():
            self.load_subjects()
            
    def edit_subject(self, item):
        row = item.row()
        sub_id = int(self.subject_table.item(row, 0).text())
        name = self.subject_table.item(row, 1).text()
        code = self.subject_table.item(row, 2).text()
        
        dialog = SubjectDialog(self, {'id': sub_id, 'name': name, 'code': code})
        if dialog.exec():
            self.load_subjects()
            self.load_classes() # Counts might change if subject names updated? No, only id matters.
            
    def assign_subjects_to_class(self, item):
        row = item.row()
        class_id = int(self.class_table.item(row, 0).text())
        class_name = self.class_table.item(row, 1).text()
        
        dialog = AssignSubjectDialog(self, class_id, class_name)
        if dialog.exec():
            self.load_classes()
