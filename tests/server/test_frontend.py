import os
import requests


def test_frontend_homepage_available():
    base = os.getenv("QENERGY_FRONTEND_BASE", "http://10.150.190.63:3001")
    url = base.rstrip("/") + "/"
    r = requests.get(url, timeout=30)
    assert r.status_code in {200, 304}
    # Basic sanity: Next.js app likely serves HTML
    assert "text/html" in r.headers.get("content-type", "").lower()


