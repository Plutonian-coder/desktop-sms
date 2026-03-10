"""Placeholder for Reports Manager"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class ReportsManager(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Reports Manager - Coming Soon"))
