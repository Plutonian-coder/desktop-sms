"""Attendance Routes - Placeholder"""
from flask import Blueprint, render_template

bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@bp.route('/')
def index():
    return render_template('attendance/index.html')
