from isar.matcher import match_job
from isar.models import Job

def make_job(title: str, location: str = "Ottobrunn, Bavaria, Germany", content: str = "") -> Job:
    return Job("1", title, location, "https://example.com/jobs/1", None, content)

def test_working_student_matches():
    result = match_job(
        make_job("Working Student Computer Science (f/m/d)"),
        {"title_include_any": ["working student", "werkstudent", "intern"], "locations": [], "exclude_any": []},
    )
    assert result.matched

def test_intern_matches():
    result = match_job(
        make_job("Intern - Launch Vehicle Assembly"),
        {"title_include_any": ["working student", "intern"], "locations": [], "exclude_any": []},
    )
    assert result.matched

def test_regular_role_does_not_match():
    result = match_job(
        make_job("Propulsion Test Engineer (m/f/d)"),
        {"title_include_any": ["working student", "werkstudent", "intern"], "locations": [], "exclude_any": []},
    )
    assert not result.matched
