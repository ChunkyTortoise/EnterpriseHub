from __future__ import annotations

import py_compile
from pathlib import Path

from fastapi.testclient import TestClient

from portal_api.app import create_app


def test_portal_api_health_smoke() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_streamlit_demo_entrypoint_compiles() -> None:
    py_compile.compile(str(Path("streamlit_cloud/app.py")), doraise=True)
