import requests


def test_health(remote_base_url, http_headers):
    url = f"{remote_base_url}/health"
    r = requests.get(url, headers=http_headers, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert data.get("ok") is True


def test_db_ping(remote_base_url, http_headers):
    url = f"{remote_base_url}/db/ping"
    r = requests.get(url, headers=http_headers, timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert data.get("db") in {"ok", "fail"}


