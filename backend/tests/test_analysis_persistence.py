from unittest.mock import patch
from sqlalchemy import text


def test_analysis_saved_and_retrievable(db_session):
    from app.services.analysis_service import AnalysisService

    svc = AnalysisService()

    # Seed a project and two weeks of history content
    db_session.execute(text("""
        INSERT INTO projects (project_code, project_name, status, created_by, updated_by)
        VALUES ('A100','Analysis Project',1,'sys','sys');
    """))

    # Past CW31 and Latest CW32, Development category
    db_session.execute(text("""
        INSERT INTO project_history (project_code, project_name, category, entry_type, log_date, cw_label, title, summary, source_text, created_by, updated_by)
        VALUES
        ('A100','Analysis Project','Development','Report','2025-07-30','CW31','A-31','Past content','Past content', 'test', 'test'),
        ('A100','Analysis Project','Development','Report','2025-08-06','CW32','A-32','Latest content with delays', 'Latest content with delays', 'test','test');
    """))

    # First run should create an analysis row
    import asyncio
    with patch.object(svc, 'get_llm_analysis', return_value={
        'risk_lvl': 55.0,
        'risk_desc': 'Moderate risk',
        'similarity_lvl': 60.0,
        'similarity_desc': 'Some overlap'
    }):
        result, was_created = asyncio.get_event_loop().run_until_complete(
            svc.analyze_project_pair(
                db=db_session,
                project_code='A100',
                past_cw='CW31',
                latest_cw='CW32',
                language='EN',
                category='Development',
                created_by='tester'
            )
        )

    assert was_created is True
    assert result.project_code == 'A100'
    assert result.cw_label == 'CW32'

    # Verify it was saved
    count = db_session.execute(text(
        "SELECT COUNT(*) FROM weekly_report_analysis WHERE project_code='A100' AND cw_label='CW32' AND language='EN' AND category='Development'"
    )).scalar()
    assert count == 1

    # Second run with same content should reuse existing (not create new)
    with patch.object(svc, 'get_llm_analysis', return_value={
        'risk_lvl': 55.0,
        'risk_desc': 'Moderate risk',
        'similarity_lvl': 60.0,
        'similarity_desc': 'Some overlap'
    }):
        result2, was_created2 = asyncio.get_event_loop().run_until_complete(
            svc.analyze_project_pair(
                db=db_session,
                project_code='A100',
                past_cw='CW31',
                latest_cw='CW32',
                language='EN',
                category='Development',
                created_by='tester'
            )
        )

    assert was_created2 is False
    # Retrieval API/service should return the saved row
    results = svc.get_analysis_results(db_session, 'CW31', 'CW32', 'EN', 'Development')
    assert any(r.project_code == 'A100' and r.cw_label == 'CW32' for r in results)


