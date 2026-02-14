"""Placeholder for Student Manager"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class StudentManager(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Student Manager - Coming Soon"))
