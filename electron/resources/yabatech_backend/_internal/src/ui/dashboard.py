"""
Dashboard Screen - Summary and Quick Actions
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from database.db_manager import DatabaseManager


class Dashboard(QWidget):
    """Main dashboard with statistics and quick actions"""
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Header
        header = QLabel("Welcome, Administrator")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #000000;")
        layout.addWidget(header)
        
        # Statistics Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        # Get statistics
        total_students = self.get_total_students()
        current_session = self.db.get_current_session()
        current_term = self.db.get_current_term()
        
        session_name = current_session['name'] if current_session else "Not Set"
        term_num = f"Term {current_term['term_number']}" if current_term else "Not Set"
        
        # Create stat cards
        stats_layout.addWidget(self.create_stat_card("Total Students", str(total_students), "#4CAF50"))
        stats_layout.addWidget(self.create_stat_card("Current Session", session_name, "#2196F3"))
        stats_layout.addWidget(self.create_stat_card("Current Term", term_num, "#FF9800"))
        
        layout.addLayout(stats_layout)
        
        # Quick Actions
        actions_label = QLabel("Quick Actions")
        actions_label.setFont(QFont("Arial", 18, QFont.Bold))
        actions_label.setStyleSheet("color: #333333; margin-top: 20px;")
        layout.addWidget(actions_label)
        
        actions_layout = QGridLayout()
        actions_layout.setSpacing(15)
        
        # Action buttons
        btn_register = self.create_action_button("Register New Student", "#4CAF50")
        btn_scores = self.create_action_button("Enter Scores", "#2196F3")
        btn_attendance = self.create_action_button("Mark Attendance", "#FF9800")
        btn_reports = self.create_action_button("Generate Reports", "#9C27B0")
        
        actions_layout.addWidget(btn_register, 0, 0)
        actions_layout.addWidget(btn_scores, 0, 1)
        actions_layout.addWidget(btn_attendance, 1, 0)
        actions_layout.addWidget(btn_reports, 1, 1)
        
        layout.addLayout(actions_layout)
        layout.addStretch()
    
    def create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a statistics card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-radius: 8px;
                border-left: 4px solid {color};
            }}
        """)
        card.setMinimumHeight(120)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 28, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 13))
        title_label.setStyleSheet("color: #666666;")
        
        card_layout.addWidget(value_label)
        card_layout.addWidget(title_label)
        
        return card
    
    def create_action_button(self, text: str, color: str) -> QPushButton:
        """Create an action button"""
        btn = QPushButton(text)
        btn.setMinimumHeight(80)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                padding: 20px;
            }}
            QPushButton:hover {{
                background: {self.darken_color(color)};
            }}
        """)
        return btn
    
    def darken_color(self, color: str) -> str:
        """Darken a hex color"""
        color_map = {
            "#4CAF50": "#45A049",
            "#2196F3": "#1976D2",
            "#FF9800": "#F57C00",
            "#9C27B0": "#7B1FA2"
        }
        return color_map.get(color, color)
    
    def get_total_students(self) -> int:
        """Get total number of active students"""
        result = self.db.execute_query(
            'SELECT COUNT(*) as count FROM students WHERE active_status = 1'
        )
        return result[0]['count'] if result else 0
