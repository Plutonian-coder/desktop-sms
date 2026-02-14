"""
Main Window - Application Shell
Clean white theme with sidebar navigation
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

from .dashboard import Dashboard
from .student_manager import StudentManager
from .session_manager import SessionManager
from .subject_manager import SubjectManager
from .score_entry import ScoreEntry
from .attendance import AttendanceManager
from .reports import ReportsManager
from .settings import SettingsManager


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yabatech JSS Management System")
        self.setMinimumSize(1200, 800)
        
        # Apply white theme stylesheet
        self.setStyleSheet(self.get_stylesheet())
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Create stacked widget for different views
        self.stack = QStackedWidget()
       
        self.stack.setStyleSheet("background: #F5F5F5;")
        main_layout.addWidget(self.stack)
        
        # Add different screens
        self.dashboard = Dashboard()
        self.student_manager = StudentManager()
        self.session_manager = SessionManager()
        self.subject_manager = SubjectManager()
        self.score_entry = ScoreEntry()
        self.attendance_manager = AttendanceManager()
        self.reports_manager = ReportsManager()
        self.settings_manager = SettingsManager()
        
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.student_manager)
        self.stack.addWidget(self.session_manager)
        self.stack.addWidget(self.subject_manager)
        self.stack.addWidget(self.score_entry)
        self.stack.addWidget(self.attendance_manager)
        self.stack.addWidget(self.reports_manager)
        self.stack.addWidget(self.settings_manager)
        
        # Show dashboard by default
        self.stack.setCurrentWidget(self.dashboard)
    
    def create_sidebar(self) -> QWidget:
        """Create the navigation sidebar"""
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame {
                background: white;
                border-right: 1px solid #E0E0E0;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(5)
        
        # School logo/title
        title = QLabel("YABATECH JSS")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333333; padding: 20px; border: none;")
        layout.addWidget(title)
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", 0),
            ("Students", 1),
            ("Sessions/Terms", 2),
            ("Subjects", 3),
            ("Score Entry", 4),
            ("Attendance", 5),
            ("Reports", 6),
            ("Settings", 7)
        ]
        
        for label, index in nav_buttons:
            btn = QPushButton(label)
            btn.setFixedHeight(45)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=index: self.stack.setCurrentIndex(idx))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        return sidebar
    
    def get_stylesheet(self) -> str:
        """Return the application stylesheet (White Mode)"""
        return """
            QMainWindow {
                background: #F5F5F5;
            }
            
            QPushButton {
                background: white;
                border: none;
                color: #333333;
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background: #FDD835;
                color: #000000;
            }
            
            QPushButton:pressed {
                background: #FBC02D;
            }
            
            QLabel {
                color: #333333;
            }
            
            QLineEdit, QComboBox, QSpinBox, QDateEdit {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                color: #333333;
                font-size: 13px;
            }
            
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #FDD835;
            }
            
            QTableWidget {
                background: white;
                alternate-background-color: #FAFAFA;
                gridline-color: #E0E0E0;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                color: #333333;
            }
            
            QTableWidget::item {
                padding: 5px;
            }
            
            QTableWidget::item:selected {
                background: #FFF9C4;
                color: #000000;
            }
            
            QHeaderView::section {
                background: #333333;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
            
            QScrollBar:vertical {
                border: none;
                background: #F5F5F5;
                width: 12px;
            }
            
            QScrollBar::handle:vertical {
                background: #BDBDBD;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #9E9E9E;
            }
        """
