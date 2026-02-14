"""
Grading Logic - Christlead Standard
Implements the Nigerian grading system
"""

def calculate_grade(total_score: float) -> str:
    """
    Calculate grade based on total score (0-100)
    Following the Christlead Model College grading standard
    
    Args:
        total_score: Total score (CA + Exam)
        
    Returns:
        Grade string (A1, B2, etc.)
    """
    if total_score >= 80:
        return "A1"
    elif total_score >= 70:
        return "B2"
    elif total_score >= 65:
        return "B3"
    elif total_score >= 60:
        return "C4"
    elif total_score >= 55:
        return "C5"
    elif total_score >= 50:
        return "C6"
    elif total_score >= 45:
        return "D7"
    elif total_score >= 40:
        return "E8"
    else:
        return "F9"


def get_grade_remark(grade: str) -> str:
    """Get the remark for a grade"""
    grade_remarks = {
        "A1": "Excellent",
        "B2": "Very Good",
        "B3": "Good",
        "C4": "Credit",
        "C5": "Credit",
        "C6": "Credit",
        "D7": "Pass",
        "E8": "Pass",
        "F9": "Fail"
    }
    return grade_remarks.get(grade, "")
