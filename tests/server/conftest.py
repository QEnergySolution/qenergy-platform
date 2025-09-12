import os
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--remote-base", action="store", default=os.getenv("QENERGY_REMOTE_BASE", "http://10.150.190.63:3001/api"),
        help="Base URL for remote server API (default: http://10.150.190.63:3001/api)"
    )


@pytest.fixture(scope="session")
def remote_base_url(pytestconfig) -> str:
    base = pytestconfig.getoption("--remote-base")
    return base.rstrip("/")


@pytest.fixture(scope="session")
def http_headers() -> dict:
    return {
        "Accept": "application/json",
    }


