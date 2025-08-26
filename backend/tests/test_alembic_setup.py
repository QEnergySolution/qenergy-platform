import os


def test_alembic_files_present():
    backend_root = os.path.dirname(os.path.dirname(__file__))
    ini_path = os.path.join(backend_root, "alembic.ini")
    versions_dir = os.path.join(backend_root, "alembic", "versions")

    assert os.path.isfile(ini_path), "alembic.ini should exist at backend/alembic.ini"
    assert os.path.isdir(os.path.join(backend_root, "alembic")), "alembic/ directory should exist"
    assert os.path.isdir(versions_dir), "alembic/versions directory should exist"


