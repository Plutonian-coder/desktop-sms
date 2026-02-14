"""Placeholder for Settings Manager"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class SettingsManager(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Settings Manager - Coming Soon"))
