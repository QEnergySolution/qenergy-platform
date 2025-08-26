import sys
from pathlib import Path

BACKEND_ROOT = str(Path(__file__).resolve().parents[1])
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

import pytest


def test_project_history_entry_type_validation():
    from app.schemas.project_history import ProjectHistoryCreate

    # valid
    ProjectHistoryCreate(project_code="P1", entry_type="Report", log_date="2025-01-06", summary="ok", category="EPC")

    # invalid
    with pytest.raises(Exception):
        ProjectHistoryCreate(project_code="P1", entry_type="NotValid", log_date="2025-01-06", summary="bad")

    with pytest.raises(Exception):
        ProjectHistoryCreate(project_code="P1", entry_type="Report", log_date="2025-01-06", summary="bad", category="InvalidCat")


def test_weekly_report_analysis_language_default_and_enum():
    from app.schemas.analysis import WeeklyReportAnalysisCreate

    obj = WeeklyReportAnalysisCreate(project_code="P1", cw_label="CW02")
    assert obj.language == "EN"

    with pytest.raises(Exception):
        WeeklyReportAnalysisCreate(project_code="P1", cw_label="CW02", language="ZZ")
