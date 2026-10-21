import io
import zipfile
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import init_db

from app.core.security import create_access_token, UserRoles

@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    token = create_access_token({"sub": "test_analyst", "role": UserRoles.ANALYST})
    client.headers.update({"Authorization": f"Bearer {token}"})

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "scanners" in data


def test_upload_and_scan_vulnerable_project():
    # Build in-memory ZIP containing vulnerable code
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr(
            "test_app.py",
            (
                "import os\n"
                "import sqlite3\n"
                "def test(user_input):\n"
                "    conn = sqlite3.connect('test.db')\n"
                "    conn.cursor().execute(f'SELECT * FROM users WHERE id = {user_input}')\n"
                "    os.system('ping ' + user_input)\n"
            )
        )

    response = client.post(
        "/api/scans/upload",
        files={"file": ("test_project.zip", zip_buffer.getvalue(), "application/zip")},
        data={"project_name": "TestVulnerableApp", "rule_mode": "bundled", "enable_ai": "true"}
    )

    if response.status_code != 200:
        print("ERROR RESPONSE:", response.json())
    assert response.status_code == 200
    scan_result = response.json()
    assert scan_result["project_name"] == "TestVulnerableApp"
    assert scan_result["scan_id"].startswith("SCAN-")
    assert "severity_breakdown" in scan_result

    # Verify scan can be retrieved by scan_id
    scan_id = scan_result["scan_id"]
    get_res = client.get(f"/api/scans/{scan_id}")
    assert get_res.status_code == 200
    assert get_res.json()["scan_id"] == scan_id


def test_reject_oversized_or_malicious_archive():
    bad_zip_buffer = io.BytesIO()
    with zipfile.ZipFile(bad_zip_buffer, "w") as zf:
        zf.writestr("../../etc/passwd", "root:x:0:0:root:/root:/bin/bash")

    response = client.post(
        "/api/scans/upload",
        files={"file": ("malicious.zip", bad_zip_buffer.getvalue(), "application/zip")}
    )

    assert response.status_code == 400
    assert "Zip Slip" in response.json()["detail"] or "Malicious" in response.json()["detail"]
